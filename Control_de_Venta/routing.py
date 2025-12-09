from django.urls import path
from Control_de_Venta.tienda import consumers

# WebSocket URL patterns
websocket_urlpatterns = [
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
]
