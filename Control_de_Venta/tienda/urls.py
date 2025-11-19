from django.urls import path, include
from . import views
from rest_framework import routers 
router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"groups", views.GroupViewSet)
router.register(r"clientes", views.ClienteViewSet)
router.register(r"productos", views.ProductoViewSet)
router.register(r"ventas", views.VentaViewSet)


urlpatterns = [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),

    path('', views.lista_productos, name='lista_productos'),
    path('agregar/', views.agregar_producto, name='agregar_producto'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('venta/', views.registrar_venta, name='registrar_venta'),
    path('resumen/', views.resumen_ventas, name='resumen_ventas'),
]