from django.urls import path
from . import views

urlpatterns = [
    path('admin/inventario/', views.AdminInventario.as_view(), name='admin_inventario'),
    path("admin/inventario/detail/<str:codigo>/", views.AdminInventarioDetail.as_view(), name="admin_inventario_detail"),
    path('admin/inventario/crear/', views.admin_inventario_crear, name='admin_inventario_crear'),
    path('admin/inventario/movimiento/', views.admin_inventario_movimiento, name='admin_inventario_movimiento'),

    path('supervisor/inventario/', views.supervisor_inventario, name='supervisor_inventario'),
    path('supervisor/inventario/entrada/', views.supervisor_inventario_entrada, name='supervisor_inventario_entrada'),
]
