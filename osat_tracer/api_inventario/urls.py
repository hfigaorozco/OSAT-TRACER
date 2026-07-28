from django.urls import path
from . import views

urlpatterns = [
    path('v1/list/piezas/', views.ListPiezaAPIView.as_view(), name='list_piezas'),
    path('v1/create/pieza/', views.CreatePiezaAPIView.as_view(), name='create_pieza'),
    path('v1/detail/pieza/<str:pk>/', views.DetailPiezaAPIView.as_view(), name='detail_pieza'),
    path('v1/update/pieza/<str:pk>/', views.UpdatePiezaAPIView.as_view(), name='update_pieza'),
    path('v1/list/movimientos_inventario/', views.ListMovimientoInventarioAPIView.as_view(), name='list_movimientos_inventario'),
    path('v1/create/movimiento_inventario/', views.CreateMovimientoInventarioAPIView.as_view(), name='create_movimiento_inventario'),
    path('v1/reporte/inventario/', views.GenerarReporteInventarioView.as_view(), name='reporte_inventario'),
]
