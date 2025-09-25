from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    habitual = models.BooleanField(default=False)

    def __str__(self):
        return self.rut

class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    def total(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f"Venta {self.id} - {self.cliente.rut}"
# Control_de_Venta/Control_de_Venta/settings.py