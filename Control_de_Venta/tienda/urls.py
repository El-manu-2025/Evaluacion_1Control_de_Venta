from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('agregar/', views.agregar_producto, name='agregar_producto'),
    path('eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('venta/', views.registrar_venta, name='registrar_venta'),
    path('resumen/', views.resumen_ventas, name='resumen_ventas'),
]