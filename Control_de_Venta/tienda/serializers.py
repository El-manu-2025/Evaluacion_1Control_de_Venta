from django.contrib.auth.models import Group, User
from rest_framework import serializers
from .models import Cliente, Producto, Venta, VentaDetalle

class ClienteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Cliente
        fields = ["url", "rut", "nombre", "correo", "habitual"]

class ProductoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Producto
        fields = ["url", "nombre", "codigo", "cantidad", "precio"]

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