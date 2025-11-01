from django.apps import AppConfig


class TiendaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Declare the app name as the top-level 'tienda' package so Django
    # imports it from the project 'Control_de_Venta/tienda' directory.
    name = 'Control_de_Venta.tienda'

