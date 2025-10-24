from django.contrib import admin
from .models import Producto, Cliente, Venta


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	"""Configuración del admin para Producto."""
	list_display = ('nombre', 'codigo', 'cantidad', 'precio')
	search_fields = ('nombre', 'codigo')
	list_filter = ('cantidad',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
	"""Configuración del admin para Cliente."""
	list_display = ('rut', 'nombre', 'correo', 'habitual')
	search_fields = ('rut', 'nombre', 'correo')
	list_filter = ('habitual',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
	"""Configuración del admin para Venta."""
	list_display = ('fecha', 'cliente', 'producto', 'cantidad', 'total_display')
	search_fields = ('cliente__rut', 'producto__nombre')
	list_filter = ('fecha', 'producto')

	def total_display(self, obj):
		# Muestra el total calculado (precio * cantidad) en el admin
		return obj.total()
	total_display.short_description = 'Total'

# Control_de_Venta/tienda/admin.py