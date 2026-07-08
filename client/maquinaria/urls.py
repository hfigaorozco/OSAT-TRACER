from django.urls import path
from . import views

urlpatterns = [
    path('admin/maquinaria/', views.admin_maquinaria, name='admin_maquinaria'),
    path('admin/maquinaria/crear/', views.admin_maquinaria_crear, name='admin_maquinaria_crear'),
]
