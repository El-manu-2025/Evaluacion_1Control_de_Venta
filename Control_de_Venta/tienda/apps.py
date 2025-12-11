from django.apps import AppConfig


class TiendaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Control_de_Venta.tienda'

    def ready(self):
        # Importa señales para registrar listeners de post_save
        from . import signals  # noqa: F401

