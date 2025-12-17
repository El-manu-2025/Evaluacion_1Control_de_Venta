from django.contrib.auth.models import Group, User
from rest_framework import serializers
from .models import Cliente, Producto, Venta, VentaDetalle, ChatMessage, ImageAnalysis, Categoria

class ClienteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Cliente
        fields = ["url", "rut", "nombre", "correo", "habitual"]

class CategoriaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Categoria
        fields = ["url", "id", "nombre", "descripcion", "activa"]

class ProductoSerializer(serializers.HyperlinkedModelSerializer):
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all(), required=False, allow_null=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    # Alias de solo lectura para compatibilidad con app móvil
    name = serializers.CharField(source='nombre', read_only=True)
    code = serializers.CharField(source='codigo', read_only=True)
    stock = serializers.IntegerField(source='cantidad', read_only=True)
    price = serializers.SerializerMethodField()
    
    class Meta:
        model = Producto
        fields = [
            "url", "id",
            # Campos originales
            "nombre", "codigo", "cantidad", "precio", "categoria", "categoria_nombre", "descripcion",
            # Aliases para clientes móviles
            "name", "code", "stock", "price",
        ]

    def get_price(self, obj):
        # Mantener el mismo formato que "precio" (string con 2 decimales)
        try:
            return f"{obj.precio:.2f}"
        except Exception:
            return str(obj.precio)

class VentaDetalleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VentaDetalle
        fields = ["url", "venta", "producto", "cantidad", "precio_unitario"]

class VentaSerializer(serializers.HyperlinkedModelSerializer):
    detalles = VentaDetalleSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = ["url", "cliente", "fecha", "stock_actualizado", "detalles"]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "user", "user_message", "ai_response", "timestamp", "context_type"]
        read_only_fields = ["id", "timestamp", "ai_response"]


class ImageAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer mejorado para ImageAnalysis.
    NUNCA devuelve campos null en analysis_result.
    """
    analysis_result = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageAnalysis
        fields = ["id", "user", "image", "analysis_result", "timestamp", "producto_created"]
        read_only_fields = ["id", "timestamp", "producto_created"]
    
    def get_analysis_result(self, obj):
        """
        Retorna analysis_result con validación para evitar null.
        Estructura garantizada:
        {
            'producto': str,
            'precio_estimado': float,
            'categoria': str,
            'descripcion': str
        }
        """
        result = obj.analysis_result or {}
        
        # Validar y establecer valores por defecto
        cleaned_result = {
            'producto': result.get('producto') or '',
            'precio_estimado': float(result.get('precio_estimado', 0)) if result.get('precio_estimado') else 0.0,
            'categoria': result.get('categoria') or '',
            'descripcion': result.get('descripcion') or '',
        }
        
        # Preservar campos adicionales si existen
        if result.get('error'):
            cleaned_result['error'] = result['error']
        
        return cleaned_result