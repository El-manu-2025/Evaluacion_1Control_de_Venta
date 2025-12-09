from django.contrib import admin
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Producto, Cliente, Venta, VentaDetalle, Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
	"""Configuración del admin para Categoría."""
	list_display = ('nombre', 'activa')
	search_fields = ('nombre',)
	list_filter = ('activa',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	"""Configuración del admin para Producto."""
	list_display = ('nombre', 'codigo', 'cantidad', 'precio', 'categoria')
	search_fields = ('nombre', 'codigo')
	list_filter = ('cantidad', 'categoria')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
	"""Configuración del admin para Cliente."""
	list_display = ('rut', 'nombre', 'correo', 'habitual')
	search_fields = ('rut', 'nombre', 'correo')
	list_filter = ('habitual',)


class VentaDetalleInline(admin.TabularInline):
	model = VentaDetalle
	extra = 1
	autocomplete_fields = ('producto',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
	"""Configuración del admin para Venta usando inline de detalles.

	La actualización de stock se realiza de forma transaccional en
	`save_formset` para evitar inconsistencias cuando el admin crea
	o modifica la venta junto con sus detalles.
	"""
	inlines = [VentaDetalleInline]
	list_display = ('fecha', 'cliente', 'total_display')
	search_fields = ('cliente__rut',)
	list_filter = ('fecha',)

	def total_display(self, obj):
		return obj.total()
	total_display.short_description = 'Total'

	def save_model(self, request, obj, form, change):
		# Solo guardar la cabecera aquí; el ajuste de stock se hace al guardar el formset
		super().save_model(request, obj, form, change)

	def save_formset(self, request, form, formset, change):
		# Guardar y validar transaccionalmente los detalles y ajustar el stock
		with transaction.atomic():
			# Guardar la cabecera si acaso no está guardada
			if form.instance and form.instance.pk is None:
				form.instance.save()

			instances = formset.save(commit=False)

			# Validar stock para nuevos/actualizados detalles
			for inst in instances:
				producto = inst.producto
				# Si el detalle ya existe, calcular delta de cantidad
				if inst.pk:
					orig = VentaDetalle.objects.get(pk=inst.pk)
					delta = inst.cantidad - orig.cantidad
				else:
					delta = inst.cantidad

				if delta > 0 and producto.cantidad < delta:
					raise ValidationError(f"Stock insuficiente para {producto.nombre} (disponible: {producto.cantidad})")

			# Aplicar cambios: restar stock por los deltas y guardar instancias
			for inst in instances:
				producto = inst.producto
				if inst.pk:
					orig = VentaDetalle.objects.get(pk=inst.pk)
					delta = inst.cantidad - orig.cantidad
				else:
					delta = inst.cantidad

				if delta != 0:
					producto.cantidad -= delta
					producto.save()

				inst.save()

			# Manejar objetos eliminados: devolver el stock
			for obj_del in formset.deleted_objects:
				prod = obj_del.producto
				prod.cantidad += obj_del.cantidad
				prod.save()
				obj_del.delete()

			formset.save_m2m()

# Control_de_Venta/tienda/admin.py