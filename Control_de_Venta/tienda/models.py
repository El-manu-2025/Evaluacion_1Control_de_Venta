
# Importa el módulo de modelos de Django
from django.db import models


# Modelo que representa a un cliente
class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)  # RUT chileno, único
    nombre = models.CharField(max_length=100, blank=True, null=True)  # Nombre opcional
    correo = models.EmailField(blank=True, null=True)  # Correo opcional
    habitual = models.BooleanField(default=False)  # Si es cliente habitual

    def __str__(self):
        # Representación legible del cliente
        return f"{self.rut} - {'Habitual' if self.habitual else 'Ocasional'}"


# Modelo que representa un producto en inventario
class Producto(models.Model):
    nombre = models.CharField(max_length=100)  # Nombre del producto
    codigo = models.CharField(max_length=50, unique=True)  # Código único
    cantidad = models.IntegerField()  # Stock disponible
    precio = models.DecimalField(max_digits=10, decimal_places=2)  # Precio unitario

    def __str__(self):
        # Representación legible del producto
        return f"{self.nombre} ({self.codigo})"


# Modelo que representa una venta realizada
class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)  # Cliente que realiza la compra
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)  # Producto vendido
    cantidad = models.PositiveIntegerField()  # Cantidad vendida
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha y hora de la venta

    def total(self):
        # Calcula el total de la venta
        return self.producto.precio * self.cantidad

    def __str__(self):
        # Representación legible de la venta
        return f"{self.fecha.strftime('%Y-%m-%d')} - {self.cliente.rut}"