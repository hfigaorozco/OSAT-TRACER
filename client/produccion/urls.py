from django.urls import path
from . import views

urlpatterns = [
    # Admin producción
    path('admin/produccion/', views.admin_produccion, name='admin_produccion'),
    path('admin/produccion/plantilla/crear/', views.admin_produccion_plantilla_crear, name='admin_produccion_plantilla_crear'),
    path('admin/produccion/orden/crear/', views.admin_orden_crear, name='admin_orden_crear'),
    path('admin/produccion/lotes-max-stock/', views.admin_lotes_max_stock, name='admin_lotes_max_stock'),
    path('admin/produccion/orden/<int:pk>/editar/', views.admin_orden_editar, name='admin_orden_editar'),
    path('admin/produccion/orden/<int:pk>/liberar/', views.admin_orden_liberar, name='admin_orden_liberar'),
    path('admin/produccion/orden/<int:pk>/rechazar/', views.admin_orden_rechazar, name='admin_orden_rechazar'),
    path('admin/produccion/orden/<int:pk>/liberar-rechazando/<int:lote_pk>/', views.admin_orden_liberar_rechazando_lote, name='admin_orden_liberar_rechazando_lote'),
    path('admin/produccion/orden/<int:pk>/reporte/', views.admin_orden_generar_reporte, name='admin_orden_generar_reporte'),
    path('admin/produccion/lote/registrar/', views.admin_lote_registrar, name='admin_lote_registrar'),
    path('admin/produccion/lote/<int:pk>/hold/', views.admin_lote_hold, name='admin_lote_hold'),
    path('admin/produccion/lote/<int:pk>/liberar/', views.admin_lote_liberar, name='admin_lote_liberar'),
    path('admin/produccion/lote/<int:pk>/reporte/', views.admin_lote_generar_reporte, name='admin_lote_generar_reporte'),
    path('admin/produccion/lote/<int:pk>/completar/', views.admin_etapa_completar, name='admin_etapa_completar'),

    # Organización
    path('admin/organizacion/', views.admin_organizacion, name='admin_organizacion'),

    path('admin/organizacion/plantilla/crear/', views.admin_organizacion_plantilla_crear, name='admin_organizacion_plantilla_crear'),
    path('admin/organizacion/plantilla/<str:pk>/editar/', views.admin_organizacion_plantilla_editar, name='admin_organizacion_plantilla_editar'),
    path('admin/organizacion/plantilla/<str:pk>/paso/asignar/', views.admin_organizacion_plantilla_paso_asignar, name='admin_organizacion_plantilla_paso_asignar'),
    path('admin/organizacion/plantilla/paso/<int:rel_pk>/quitar/', views.admin_organizacion_plantilla_paso_quitar, name='admin_organizacion_plantilla_paso_quitar'),
    path('admin/organizacion/plantilla/<str:pk>/pieza/asignar/', views.admin_organizacion_plantilla_pieza_asignar, name='admin_organizacion_plantilla_pieza_asignar'),
    path('admin/organizacion/plantilla/pieza/<int:rel_pk>/quitar/', views.admin_organizacion_plantilla_pieza_quitar, name='admin_organizacion_plantilla_pieza_quitar'),

    path('admin/organizacion/oblea/crear/', views.admin_organizacion_oblea_crear, name='admin_organizacion_oblea_crear'),
    path('admin/organizacion/oblea/<str:pk>/editar/', views.admin_organizacion_oblea_editar, name='admin_organizacion_oblea_editar'),

    path('admin/organizacion/linea/crear/', views.admin_organizacion_linea_crear, name='admin_organizacion_linea_crear'),
    path('admin/organizacion/linea/<str:pk>/editar/', views.admin_organizacion_linea_editar, name='admin_organizacion_linea_editar'),

    path('admin/organizacion/paso/crear/', views.admin_organizacion_paso_crear, name='admin_organizacion_paso_crear'),
    path('admin/organizacion/paso/<str:pk>/editar/', views.admin_organizacion_paso_editar, name='admin_organizacion_paso_editar'),

    # Supervisor
    path('supervisor/ordenes/', views.supervisor_ordenes, name='supervisor_ordenes'),
    path('supervisor/ordenes/crear/', views.supervisor_ordenes_crear, name='supervisor_ordenes_crear'),
    path('supervisor/ordenes/lotes-max-stock/', views.supervisor_lotes_max_stock, name='supervisor_lotes_max_stock'),
    path('supervisor/ordenes/<int:pk>/editar/', views.supervisor_orden_editar, name='supervisor_orden_editar'),
    path('supervisor/ordenes/<int:pk>/', views.supervisor_orden_detalle, name='supervisor_orden_detalle'),
    path('supervisor/ordenes/<int:pk>/liberar/', views.supervisor_orden_liberar, name='supervisor_orden_liberar'),
    path('supervisor/ordenes/<int:pk>/rechazar/', views.supervisor_orden_rechazar, name='supervisor_orden_rechazar'),
    path('supervisor/ordenes/<int:pk>/liberar-rechazando/<int:lote_pk>/', views.supervisor_orden_liberar_rechazando_lote, name='supervisor_orden_liberar_rechazando_lote'),
    path('supervisor/ordenes/<int:pk>/reporte/', views.supervisor_orden_generar_reporte, name='supervisor_orden_generar_reporte'),
    path('supervisor/lotes/', views.supervisor_lotes, name='supervisor_lotes'),
    path('supervisor/lotes/<int:pk>/', views.supervisor_lote_detalle, name='supervisor_lote_detalle'),
    path('supervisor/lotes/<int:pk>/hold/', views.supervisor_lote_hold, name='supervisor_lote_hold'),
    path('supervisor/lotes/<int:pk>/liberar/', views.supervisor_lote_liberar, name='supervisor_lote_liberar'),
    path('supervisor/lotes/<int:pk>/reporte/', views.supervisor_lote_generar_reporte, name='supervisor_lote_generar_reporte'),
    path('supervisor/lotes/<int:pk>/scrap/', views.supervisor_lote_scrap, name='supervisor_lote_scrap'),
    path('supervisor/lotes/registrar/', views.supervisor_lote_registrar, name='supervisor_lote_registrar'),
    path('supervisor/lotes/<int:pk>/completar/', views.supervisor_etapa_completar, name='supervisor_etapa_completar'),
]