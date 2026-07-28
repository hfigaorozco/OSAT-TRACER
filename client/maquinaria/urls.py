from django.urls import path
from . import views

urlpatterns = [
    path('admin/maquinaria/', views.AdminMaquinaria.as_view(), name='admin_maquinaria'),
    path('admin/maquinaria/crear/', views.AdminMaquinariaCrear.as_view(), name='admin_maquinaria_crear'),
    path('admin/maquinaria/editar/<str:pk>/', views.AdminMaquinariaEditar.as_view(), name='admin_maquinaria_editar'),
    path('admin/maquinaria/<str:pk>/estado/', views.AdminMaquinariaToggleEstado.as_view(), name='admin_maquinaria_toggle_estado'),
]
