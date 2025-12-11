# Importaciones necesarias de Django y modelos propios
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.db.models import Sum, Count, Q
from django.db.models import ProtectedError
from django.contrib import messages
from .models import Producto, Cliente, Venta, VentaDetalle, ChatMessage, ImageAnalysis, Categoria
from django.db import transaction
import re
import json
import logging
from datetime import timedelta

from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    GroupSerializer, UserSerializer, ClienteSerializer, ProductoSerializer,
    VentaSerializer, VentaDetalleSerializer, ChatMessageSerializer, ImageAnalysisSerializer, CategoriaSerializer
)
from .groq_utils import (
    chat_with_groq, analyze_image_with_groq, generate_stock_suggestions, analyze_sales_trends
)

logger = logging.getLogger(__name__)

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by("nombre")
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAuthenticated]

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by("rut")
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by("nombre")
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all().order_by("-fecha")
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticated]

class VentaDetalleViewSet(viewsets.ModelViewSet):
    queryset = VentaDetalle.objects.all()
    serializer_class = VentaDetalleSerializer
    permission_classes = [permissions.IsAuthenticated]
    

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChatMessageViewSet(viewsets.ModelViewSet):
    """ViewSet para chat IA."""
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Solo retorna mensajes del usuario autenticado."""
        return ChatMessage.objects.filter(user=self.request.user).order_by('-timestamp')

    def create(self, request, *args, **kwargs):
        """Envía un mensaje a Groq y guarda en historial."""
        user_message = request.data.get('user_message', '').strip()
        context_type = request.data.get('context_type', 'general')

        if not user_message:
            return Response(
                {'error': 'El mensaje no puede estar vacío.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener contexto según tipo (productos, ventas, etc)
        context = self._build_context(context_type)

        # Obtener últimos 5 mensajes como historial
        history = list(
            ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:5]
        )
        history.reverse()
        history_messages = [
            {"role": "user", "content": h.user_message}
            for h in history
        ] + [
            {"role": "assistant", "content": h.ai_response}
            for h in history
        ]

        # Llamar a Groq
        ai_response = chat_with_groq(user_message, context=context, history=history_messages)

        # Guardar en BD
        chat_msg = ChatMessage.objects.create(
            user=request.user,
            user_message=user_message,
            ai_response=ai_response,
            context_type=context_type
        )

        serializer = self.get_serializer(chat_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _build_context(self, context_type):
        """Construye contexto según tipo solicitado."""
        if context_type == 'producto':
            productos = Producto.objects.all().values('nombre', 'codigo', 'cantidad', 'precio')
            return f"Productos disponibles:\n{json.dumps(list(productos), default=str, ensure_ascii=False)}"
        elif context_type == 'venta':
            ventas_recent = Venta.objects.filter(
                fecha__gte=now() - timedelta(days=30)
            ).values('cliente__nombre', 'fecha').annotate(total=Sum('detalles__cantidad'))
            return f"Ventas últimos 30 días:\n{json.dumps(list(ventas_recent), default=str, ensure_ascii=False)}"
        elif context_type == 'stock':
            bajo_stock = Producto.objects.filter(cantidad__lt=10).values('nombre', 'cantidad')
            return f"Productos con bajo stock:\n{json.dumps(list(bajo_stock), default=str, ensure_ascii=False)}"
        return None

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Retorna el historial de chat del usuario."""
        queryset = self.get_queryset()[:20]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ImageAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análisis de imágenes con Groq Vision."""
    serializer_class = ImageAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Solo retorna análisis del usuario autenticado."""
        return ImageAnalysis.objects.filter(user=self.request.user).order_by('-timestamp')

    def create(self, request, *args, **kwargs):
        """
        Analiza una imagen y extrae información de producto.
        SIEMPRE devuelve un JSON válido con estructura completa.
        """
        # Validación de archivo
        if 'image' not in request.FILES:
            return Response(
                {
                    'error': 'No se proporcionó una imagen.',
                    'analysis_result': {
                        'producto': '',
                        'precio_estimado': 0.0,
                        'categoria': '',
                        'descripcion': 'Imagen no proporcionada'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = request.FILES['image']
        
        # Validar tipo de archivo
        valid_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in valid_types:
            logger.warning(f"Tipo de archivo inválido: {image_file.content_type}")
            return Response(
                {
                    'error': f'Tipo de archivo no válido. Use: {", ".join(valid_types)}',
                    'analysis_result': {
                        'producto': '',
                        'precio_estimado': 0.0,
                        'categoria': '',
                        'descripcion': 'Formato de imagen no soportado'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image_bytes = image_file.read()
        except Exception as e:
            logger.error(f"Error leyendo archivo: {str(e)}")
            return Response(
                {
                    'error': 'Error al leer el archivo de imagen',
                    'analysis_result': {
                        'producto': '',
                        'precio_estimado': 0.0,
                        'categoria': '',
                        'descripcion': 'No se pudo procesar la imagen'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Usar la función mejorada de análisis
        from .groq_utils import analyze_product_image_v2
        analysis_result = analyze_product_image_v2(image_bytes, max_retries=2)
        
        # Log detallado para debugging
        logger.info(f"📊 Resultado del análisis: {analysis_result}")
        logger.info(f"  - Producto: '{analysis_result.get('producto')}'")
        logger.info(f"  - Precio: {analysis_result.get('precio_estimado')}")
        logger.info(f"  - Categoría: '{analysis_result.get('categoria')}'")
        logger.info(f"  - Descripción: '{analysis_result.get('descripcion')}'")

        # Guardar análisis en BD
        try:
            img_analysis = ImageAnalysis.objects.create(
                user=request.user,
                image=image_file,
                analysis_result=analysis_result
            )
            
            logger.info(f"Análisis guardado. ID: {img_analysis.id}, Resultado: {analysis_result}")
            
            serializer = self.get_serializer(img_analysis)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error guardando análisis en BD: {str(e)}")
            return Response(
                {
                    'error': 'Error guardando análisis en base de datos',
                    'analysis_result': analysis_result
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def debug_analysis(self, request):
        """
        ENDPOINT DE DEBUG - Muestra respuesta RAW de Groq
        Útil para ver qué devuelve la IA sin procesamiento
        """
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó una imagen.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = request.FILES['image']
        
        try:
            image_bytes = image_file.read()
        except Exception as e:
            logger.error(f"Error leyendo imagen: {str(e)}")
            return Response(
                {'error': f'Error al leer imagen: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Usar la función antigua para ver respuesta RAW
        from .groq_utils import analyze_image_with_groq
        raw_response = analyze_image_with_groq(image_bytes)
        
        logger.info(f"🔍 RESPUESTA RAW DE GROQ:\n{raw_response}")
        
        return Response(
            {
                'message': 'DEBUG - Ver logs del servidor para respuesta RAW',
                'raw_response': raw_response
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def create_producto_from_image(self, request):
        """
        Analiza imagen y crea producto en BD.
        SIEMPRE retorna datos válidos (nunca null).
        """
        if 'image' not in request.FILES:
            return Response(
                {
                    'error': 'No se proporcionó una imagen.',
                    'producto': None,
                    'analysis': {
                        'producto': '',
                        'precio_estimado': 0.0,
                        'categoria': '',
                        'descripcion': 'Imagen no proporcionada'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = request.FILES['image']
        
        try:
            image_bytes = image_file.read()
        except Exception as e:
            logger.error(f"Error leyendo imagen: {str(e)}")
            return Response(
                {
                    'error': 'No se pudo leer el archivo de imagen',
                    'producto': None,
                    'analysis': {
                        'producto': '',
                        'precio_estimado': 0.0,
                        'categoria': '',
                        'descripcion': 'Error al procesar imagen'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Analizar imagen con versión mejorada
        from .groq_utils import analyze_product_image_v2
        analysis_data = analyze_product_image_v2(image_bytes, max_retries=2)

        logger.info(f"Análisis completado: {analysis_data}")

        # Extraer datos (con fallbacks para campos vacíos)
        nombre = analysis_data.get('producto', '').strip()
        precio = analysis_data.get('precio_estimado', 0.0)
        categoria_nombre = analysis_data.get('categoria', '').strip()
        descripcion = analysis_data.get('descripcion', '').strip()

        # Si no se reconoció el producto, retornar error sin crear
        if not nombre:
            logger.warning("Producto no reconocido en la imagen")
            return Response(
                {
                    'error': 'No se pudo reconocer el producto en la imagen',
                    'producto': None,
                    'analysis': analysis_data
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generar código automático si no está disponible
        codigo = f"AUTO-{image_file.name.split('.')[0][:10].upper()}"

        try:
            # Obtener o crear categoría
            categoria = None
            if categoria_nombre:
                categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)

            # Crear producto
            producto = Producto.objects.create(
                nombre=nombre,
                codigo=codigo,
                precio=float(precio) if precio else 0.0,
                cantidad=0,  # Por defecto 0 hasta que se agregue stock
                categoria=categoria
            )

            logger.info(f"Producto creado. ID: {producto.id}, Nombre: {nombre}")

            # Guardar análisis con referencia al producto
            img_analysis = ImageAnalysis.objects.create(
                user=request.user,
                image=image_file,
                analysis_result=analysis_data,
                producto_created=producto
            )

            return Response(
                {
                    'success': True,
                    'message': f'Producto "{nombre}" creado exitosamente',
                    'producto': ProductoSerializer(producto).data,
                    'analysis': ImageAnalysisSerializer(img_analysis).data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error creando producto: {str(e)}")
            return Response(
                {
                    'error': f'Error creando producto en BD: {str(e)}',
                    'producto': None,
                    'analysis': analysis_data
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_producto_from_text(self, request):
        """Crea producto a partir de texto (nombre, código, precio, cantidad)."""
        nombre = request.data.get('nombre', '').strip()
        codigo = request.data.get('codigo', '').strip()
        precio = float(request.data.get('precio', 0))
        cantidad = int(request.data.get('cantidad', 0))

        if not nombre or not codigo:
            return Response(
                {'error': 'Nombre y código son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto = Producto.objects.create(
                nombre=nombre,
                codigo=codigo,
                precio=precio,
                cantidad=cantidad
            )
            return Response(
                ProductoSerializer(producto).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': f'Error creando producto: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Retorna últimos 10 análisis."""
        queryset = self.get_queryset()[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet para análisis de ventas y recomendaciones."""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Analiza tendencias de ventas de los últimos 30 días."""
        days = int(request.query_params.get('days', 30))
        start_date = now() - timedelta(days=days)

        ventas = Venta.objects.filter(fecha__gte=start_date).values(
            'fecha__date'
        ).annotate(
            total_units=Sum('detalles__cantidad'),
            total_sales=Sum(
                models.F('detalles__cantidad') * models.F('detalles__precio_unitario'),
                output_field=models.DecimalField()
            )
        ).order_by('fecha__date')

        productos_vendidos = VentaDetalle.objects.filter(
            venta__fecha__gte=start_date
        ).values('producto__nombre').annotate(
            cantidad=Sum('cantidad'),
            ingresos=Sum(models.F('cantidad') * models.F('precio_unitario'), output_field=models.DecimalField())
        ).order_by('-cantidad')

        analytics_data = {
            'periodo_dias': days,
            'ventas_por_fecha': list(ventas),
            'productos_top': list(productos_vendidos[:10]),
            'fecha_analisis': str(now().date())
        }

        # Generar análisis con Groq
        analysis_text = analyze_sales_trends(analytics_data)

        return Response({
            'analytics_data': analytics_data,
            'ai_analysis': analysis_text
        })

    @action(detail=False, methods=['get'])
    def stock_suggestions(self, request):
        """Genera sugerencias de reorden de stock."""
        productos = Producto.objects.all().values('id', 'nombre', 'codigo', 'cantidad', 'precio')

        # Calcular velocidad de venta por producto (últimos 30 días)
        days = 30
        start_date = now() - timedelta(days=days)

        velocidades = {}
        for prod in productos:
            vendidos = VentaDetalle.objects.filter(
                producto_id=prod['id'],
                venta__fecha__gte=start_date
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            velocidades[prod['nombre']] = {
                'stock_actual': prod['cantidad'],
                'precio': str(prod['precio']),
                'vendidos_30dias': vendidos,
                'velocidad_diaria': round(vendidos / days, 2)
            }

        # Generar sugerencias con Groq
        suggestions_text = generate_stock_suggestions(velocidades)

        return Response({
            'velocidades_venta': velocidades,
            'sugerencias_reorden': suggestions_text,
            'fecha_analisis': str(now().date())
        })

    @action(detail=False, methods=['get'])
    def low_stock_alert(self, request):
        """Retorna productos con stock bajo."""
        threshold = int(request.query_params.get('threshold', 10))
        low_stock = Producto.objects.filter(cantidad__lt=threshold).values(
            'id', 'nombre', 'codigo', 'cantidad', 'precio'
        )
        return Response({
            'threshold': threshold,
            'productos': list(low_stock),
            'cantidad_critica': len(low_stock)
        })

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'tienda/lista_productos.html', {'productos': productos})

def ws_test(request):
    return render(request, "tienda/ws_test.html")

# Vista para mostrar el resumen de ventas, con filtro por fechas
def resumen_ventas(request):
    from django.utils.dateparse import parse_date
    # Obtiene todas las ventas, ordenadas por fecha descendente
    ventas_qs = Venta.objects.select_related('cliente').prefetch_related('detalles__producto').order_by('-fecha')
    # Obtiene los parámetros de filtro de fecha desde la URL
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    ventas = ventas_qs
    # Aplica filtro por fecha de inicio si corresponde
    if fecha_inicio:
        ventas = ventas.filter(fecha__date__gte=fecha_inicio)
    # Aplica filtro por fecha de fin si corresponde
    if fecha_fin:
        ventas = ventas.filter(fecha__date__lte=fecha_fin)
    # Limita a las últimas 20 ventas o las filtradas
    ventas = ventas[:20]
    # Calcula el total vendido en el periodo mostrado
    total = sum(v.total() for v in ventas)

    return render(request, 'tienda/resumen_ventas.html', {
        'ventas': ventas,
        'total': total,
        'hoy': now().date(),
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
    })

# Vista para agregar o editar un producto
def agregar_producto(request):
    if request.method == 'POST':
        # Obtiene los datos del formulario
        nombre = request.POST['nombre']
        codigo = request.POST['codigo']
        cantidad = int(request.POST['cantidad'] or 0)
        precio = float(request.POST['precio'] or 0)
        categoria_id = request.POST.get('categoria_id') or None
        
        # Si viene un id de producto, se actualiza; si no, se crea uno nuevo
        producto_id = request.POST.get('producto_id')
        if producto_id:
            producto = get_object_or_404(Producto, id=producto_id)
            producto.nombre = nombre
            producto.codigo = codigo
            producto.cantidad = cantidad
            producto.precio = precio
            producto.categoria_id = categoria_id
            producto.save()

            # Mensaje de actualización
            messages.success(request, '✅ Producto actualizado con éxito.')

        else:
            Producto.objects.create(
                nombre=nombre,
                codigo=codigo,
                cantidad=cantidad,
                precio=precio,
                categoria_id=categoria_id
            )
            # Mensaje de creación
            messages.success(request, '✅ Producto agregado con éxito.')
        return redirect('lista_productos')

    # Si es GET, muestra el formulario, y si hay id, carga el producto a editar
    producto_id = request.GET.get('id')
    categorias = Categoria.objects.filter(activa=True).order_by('nombre')
    context = {'categorias': categorias}
    if producto_id:
        context['producto'] = get_object_or_404(Producto, id=producto_id)
    return render(request, 'tienda/agregar_producto.html', context)


# Vista para eliminar un producto por su id
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    try:
        producto.delete()
        messages.success(request, "Producto eliminado correctamente.")
    except ProtectedError:
        messages.error(request, "No se puede eliminar este producto porque está asociado a una venta.")
    return redirect('lista_productos')

# Vista para registrar una venta
def registrar_venta(request):
    productos = Producto.objects.all()
    if request.method == 'POST':
        # Obtiene los datos del formulario
        rut = request.POST['rut'].strip()
        # Normaliza el RUT: elimina puntos y convierte a mayúsculas para la K
        rut_raw = rut.replace('.', '').upper()

        # Si recibe 9 o 10 dígitos sin guion, se puede considerar:
        # - 10 dígitos seguidos: lo permitimos (ej. 2276090072)
        # - 9 dígitos (8 + dv) sin guion: agregamos el guion
        # Aceptamos también formato con guion (ej. 22760900-7)
        # Quitar espacios
        rut_raw = rut_raw.replace(' ', '')

        # Si viene sin guion y tiene 9 o 10 caracteres, intentar formatear
        if '-' not in rut_raw and len(rut_raw) in (9, 10):
            # Si tiene 9 caracteres asumimos 8 + dv
            if len(rut_raw) == 9:
                rut_norm = rut_raw[:8] + '-' + rut_raw[8]
            else:
                # 10 dígitos: tomar los primeros 8, guion, resto como dv (si vienen 10 se considera 8+dv)
                rut_norm = rut_raw[:8] + '-' + rut_raw[8:]
        else:
            rut_norm = rut_raw

        # Validación final: acepta 10 dígitos seguidos o 8 dígitos + '-' + dv (num o K)
        if not re.fullmatch(r'(?:\d{10}|\d{8}-[0-9K])', rut_norm):
            messages.error(request, 'RUT inválido. Use 10 dígitos seguidos o formato 8 dígitos-VD (ej. 22760900-7).')
            return render(request, 'tienda/registrar_venta.html', {'productos': productos})

        # Usar rut_norm como valor estandarizado para buscar/crear cliente
        rut = rut_norm
        nombre = request.POST.get('nombre', '').strip()
        habitual = request.POST.get('habitual') == 'on'
        codigo = request.POST['codigo']
        cantidad = int(request.POST['cantidad'] or 0)

        # Busca el producto por su código
        producto = get_object_or_404(Producto, codigo=codigo)

        # Valida que haya suficiente stock
        if producto.cantidad < cantidad:
            messages.error(request, '❌ No puedes vender más de lo que hay en stock.')
            return render(request, 'tienda/error.html', {'mensaje': 'Stock insuficiente'})

        # Busca o crea el cliente
        cliente, creado = Cliente.objects.get_or_create(rut=rut)
        if habitual:
            cliente.habitual = True
            if nombre:
                cliente.nombre = nombre
            cliente.save()

        # Registra la venta y el detalle en una transacción, actualizando stock
        try:
            with transaction.atomic():
                venta = Venta.objects.create(cliente=cliente)
                detalle = VentaDetalle.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                )
                # Descontar stock
                producto.cantidad -= cantidad
                producto.save()
        except Exception as e:
            messages.error(request, f'❌ Error al registrar la venta: {e}')
            return render(request, 'tienda/error.html', {'mensaje': str(e)})
        
        messages.success(request, '✅ Venta registrada con éxito.')
        return redirect('lista_productos')

    # Si es GET, muestra el formulario de venta
    return render(request, 'tienda/registrar_venta.html', {'productos': productos})
