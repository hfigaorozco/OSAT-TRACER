from django.urls import path
from . import views

urlpatterns = [
    # Admin producción
    path('admin/produccion/', views.admin_produccion, name='admin_produccion'),
    path('admin/produccion/plantilla/crear/', views.admin_produccion_plantilla_crear, name='admin_produccion_plantilla_crear'),

    # Organización
    path('admin/organizacion/', views.admin_organizacion, name='admin_organizacion'),
    path('admin/organizacion/plantilla/crear/', views.admin_organizacion_plantilla_crear, name='admin_organizacion_plantilla_crear'),
    path('admin/organizacion/plantilla/<int:pk>/editar/', views.admin_organizacion_plantilla_editar, name='admin_organizacion_plantilla_editar'),
    path('admin/organizacion/oblea/crear/', views.admin_organizacion_oblea_crear, name='admin_organizacion_oblea_crear'),
    path('admin/organizacion/linea/crear/', views.admin_organizacion_linea_crear, name='admin_organizacion_linea_crear'),

    # Supervisor
    path('supervisor/ordenes/', views.supervisor_ordenes, name='supervisor_ordenes'),
    path('supervisor/ordenes/crear/', views.supervisor_ordenes_crear, name='supervisor_ordenes_crear'),
    path('supervisor/ordenes/<int:pk>/', views.supervisor_orden_detalle, name='supervisor_orden_detalle'),
    path('supervisor/lotes/', views.supervisor_lotes, name='supervisor_lotes'),
    path('supervisor/lotes/<int:pk>/', views.supervisor_lote_detalle, name='supervisor_lote_detalle'),
    path('supervisor/lotes/<int:pk>/hold/', views.supervisor_lote_hold, name='supervisor_lote_hold'),
    path('supervisor/lotes/<int:pk>/scrap/', views.supervisor_lote_scrap, name='supervisor_lote_scrap'),
    path('supervisor/lotes/registrar/', views.supervisor_lote_registrar, name='supervisor_lote_registrar'),
    path('supervisor/lotes/<int:pk>/completar/', views.supervisor_etapa_completar, name='supervisor_etapa_completar'),
]