import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket sencillo para notificaciones en tiempo real.
    Los clientes se suscriben al grupo "notifications" y reciben mensajes broadcast.
    """

    group_name = "notifications"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Eco/broadcast de cualquier mensaje recibido (para pruebas)
        if text_data:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "notify", "message": text_data},
            )

    async def notify(self, event):
        message = event.get("message", "")
        await self.send(text_data=json.dumps({"message": message}))
