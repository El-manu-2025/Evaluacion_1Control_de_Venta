"""
Utilidad para enviar notificaciones por WebSocket al grupo "notifications".

Ejemplo (vista Django síncrona):
    from Control_de_Venta.tienda.notifications import send_notification
    send_notification("Nueva venta registrada")

Ejemplo (vista/servicio asíncrono):
    from Control_de_Venta.tienda.notifications import send_notification_async
    await send_notification_async("Stock bajo en producto X")

Mensaje recibido por los clientes WebSocket:
    {"message": "Nueva venta registrada"}
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


GROUP_NAME = "notifications"


def send_notification(message: str) -> None:
    """Envío síncrono (usable desde vistas normales)."""
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            GROUP_NAME,
            {"type": "notify", "message": message},
        )


async def send_notification_async(message: str) -> None:
    """Envío asíncrono (usable desde tareas async/consumers)."""
    channel_layer = get_channel_layer()
    if channel_layer:
        await channel_layer.group_send(
            GROUP_NAME,
            {"type": "notify", "message": message},
        )
