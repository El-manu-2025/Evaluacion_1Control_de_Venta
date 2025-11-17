# Importaciones necesarias de Django y modelos propios
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.db.models import Sum
from django.db.models import ProtectedError
from django.contrib import messages
from .models import Producto, Cliente, Venta, VentaDetalle
from django.db import transaction
import re
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets

from .serializers import GroupSerializer, UserSerializer

# Vista para listar todos los productos
def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'tienda/lista_productos.html', {'productos': productos})


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
        # Si viene un id de producto, se actualiza; si no, se crea uno nuevo
        producto_id = request.POST.get('producto_id')
        if producto_id:
            producto = get_object_or_404(Producto, id=producto_id)
            producto.nombre = nombre
            producto.codigo = codigo
            producto.cantidad = cantidad
            producto.precio = precio
            producto.save()

            # Mensaje de actualización
            messages.success(request, '✅ Producto actualizado con éxito.')

        else:
            Producto.objects.create(nombre=nombre, codigo=codigo, cantidad=cantidad, precio=precio)
            # Mensaje de creación
            messages.success(request, '✅ Producto agregado con éxito.')
        return redirect('lista_productos')

    # Si es GET, muestra el formulario, y si hay id, carga el producto a editar
    producto_id = request.GET.get('id')
    context = {}
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
