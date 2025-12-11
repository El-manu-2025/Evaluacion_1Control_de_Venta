from django.urls import path, include
from . import views
from rest_framework import routers 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"groups", views.GroupViewSet)
router.register(r"categorias", views.CategoriaViewSet)
router.register(r"clientes", views.ClienteViewSet)
router.register(r"productos", views.ProductoViewSet)
router.register(r"ventas", views.VentaViewSet)
router.register(r"ventadetalle", views.VentaDetalleViewSet)
router.register(r"chat", views.ChatMessageViewSet, basename="chat")
router.register(r"images", views.ImageAnalysisViewSet, basename="images")
router.register(r"analytics", views.AnalyticsViewSet, basename="analytics")

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),

    path('', views.lista_productos, name='lista_productos'),
    path('agregar/', views.agregar_producto, name='agregar_producto'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('venta/', views.registrar_venta, name='registrar_venta'),
    path('resumen/', views.resumen_ventas, name='resumen_ventas'),
    path('ws-test/', views.ws_test, name='ws_test'),
]