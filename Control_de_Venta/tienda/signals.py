from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Producto, Venta
from .notifications import send_notification


@receiver(post_save, sender=Producto)
def notify_producto_created(sender, instance: Producto, created: bool, **kwargs):
    if created:
        nombre = instance.nombre if hasattr(instance, "nombre") else str(instance)
        categoria = getattr(getattr(instance, "categoria", None), "nombre", "Sin categoría")
        send_notification(
            {
                "type": "producto_created",
                "title": "Nuevo producto creado",
                "producto": nombre,
                "categoria": categoria,
            }
        )


@receiver(post_save, sender=Venta)
def notify_venta_created(sender, instance: Venta, created: bool, **kwargs):
    if created:
        try:
            cliente_nombre = getattr(instance.cliente, "nombre", "Cliente") if hasattr(instance, "cliente") else "Cliente"
        except Exception:
            cliente_nombre = "Cliente"
        total = getattr(instance, "total", None)
        payload = {
            "type": "venta_created",
            "title": "Nueva venta registrada",
            "cliente": cliente_nombre,
        }
        if total is not None:
            payload["total"] = float(total)
        send_notification(payload)
