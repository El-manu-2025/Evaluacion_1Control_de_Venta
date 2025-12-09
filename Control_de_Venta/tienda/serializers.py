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
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    
    class Meta:
        model = Producto
        fields = ["url", "id", "nombre", "codigo", "cantidad", "precio", "categoria", "categoria_nombre"]

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
    class Meta:
        model = ImageAnalysis
        fields = ["id", "user", "image", "analysis_result", "timestamp", "producto_created"]
        read_only_fields = ["id", "timestamp", "analysis_result", "producto_created"]