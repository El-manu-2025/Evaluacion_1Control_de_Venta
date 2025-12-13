"""
URL configuration for Control_de_Venta project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Control_de_Venta.tienda.urls')),

    # Healthcheck simple para Railway
    path(
        'healthz/',
        lambda request: JsonResponse(
            {
                'ok': True,
                'has_groq_chat': bool(os.getenv('GROQ_API_KEY_CHAT') or os.getenv('GROQ_API_KEY')),
                'has_groq_vision': bool(os.getenv('GROQ_API_KEY_VISION') or os.getenv('GROQ_API_KEY')),
            }
        ),
    ),

]
