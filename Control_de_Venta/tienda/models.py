
# Importa el módulo de modelos de Django
from django.db import models, transaction
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


# Modelo que representa a un cliente
class Cliente(models.Model):
    # Validador: acepta dos formatos validos:
    # - 10 dígitos seguidos (ej. 2276090072)
    # - 8 dígitos, guion y dígito verificador (numérico o K), ej. 22760900-7
    rut_validator = RegexValidator(
        regex=r'^(?:\d{10}|\d{8}-[0-9Kk])$',
        message='El RUT debe ser 10 dígitos seguidos o 8 dígitos + "-" + dígito verificador (num o K).'
    )

    # RUT: se permite el guion opcional en el formato (se valida según rut_validator)
    rut = models.CharField(max_length=12, unique=True, validators=[rut_validator])  # RUT chileno, único
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
    """Cabecera de la venta."""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    # Indica si ya se aplicó el ajuste de stock para esta venta
    stock_actualizado = models.BooleanField(default=False)

    def total(self):
        """Suma los totales de los detalles."""
        return sum(d.cantidad * d.precio_unitario for d in self.detalles.all())

    def __str__(self):
        return f"{self.fecha.strftime('%Y-%m-%d %H:%M')} - {self.cliente.rut}"


class VentaDetalle(models.Model):
    """Detalle de línea de una venta.

    Se guarda el precio unitario al momento de la venta para conservar histórico
    aunque el precio del producto cambie después.
    """
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Detalle de venta'
        verbose_name_plural = 'Detalles de venta'

    def clean(self):
        # Validar stock disponible al crear/actualizar el detalle
        if self.pk is None:  # nuevo detalle
            if self.producto.cantidad < self.cantidad:
                raise ValidationError(f"Stock insuficiente para {self.producto.nombre} (disponible: {self.producto.cantidad})")

    def save(self, *args, **kwargs):
        # Si no se recibe precio_unitario, tomar el precio actual del producto
        if self.precio_unitario in (None, ''):
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)