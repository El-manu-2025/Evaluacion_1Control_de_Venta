from django.urls import re_path
from Control_de_Venta.tienda import consumers

# WebSocket URL patterns
websocket_urlpatterns = [
    # Accept both with and without trailing slash
    re_path(r"^ws/notifications/?$", consumers.NotificationConsumer.as_asgi()),
    # Temporary catch-all to debug unmatched paths in dev
    re_path(r"^.*$", consumers.NotificationConsumer.as_asgi()),
]
