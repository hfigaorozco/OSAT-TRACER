from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('home.urls')),
    path('', include('usuarios.urls')),
    path('', include('maquinaria.urls')),
    path('', include('inventario.urls')),
    path('', include('produccion.urls')),
    path('', include('kpi.urls')),
    path('', include('reportes.urls')),
]
