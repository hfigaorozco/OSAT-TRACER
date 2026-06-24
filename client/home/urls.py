from django.urls import path
from . import views

urlpatterns = [

    # ── Auth ──────────────────────────────────────────────────
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ── Admin ─────────────────────────────────────────────────
    path('admin-dash/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/cuentas/', views.admin_cuentas, name='admin_cuentas'),
    path('admin/cuentas/crear/', views.admin_cuentas_crear, name='admin_cuentas_crear'),
    path('admin/personal/', views.admin_personal, name='admin_personal'),
    path('admin/personal/crear/', views.admin_personal_crear, name='admin_personal_crear'),
    path('admin/maquinaria/', views.admin_maquinaria, name='admin_maquinaria'),
    path('admin/maquinaria/crear/', views.admin_maquinaria_crear, name='admin_maquinaria_crear'),
    path('admin/inventario/', views.admin_inventario, name='admin_inventario'),
    path('admin/inventario/crear/', views.admin_inventario_crear, name='admin_inventario_crear'),
    path('admin/inventario/movimiento/', views.admin_inventario_movimiento, name='admin_inventario_movimiento'),
    path('admin/produccion/', views.admin_produccion, name='admin_produccion'),
    path('admin/produccion/plantilla/crear/', views.admin_produccion_plantilla_crear, name='admin_produccion_plantilla_crear'),
    path('admin/configuracion/', views.admin_configuracion, name='admin_configuracion'),
    path('admin/configuracion/kpi/', views.admin_config_kpi_save, name='admin_config_kpi_save'),
    path('admin/configuracion/turno/', views.admin_config_turno_crear, name='admin_config_turno_crear'),
    path('admin/configuracion/defecto/', views.admin_config_defecto_crear, name='admin_config_defecto_crear'),
    path('admin/configuracion/password/', views.admin_config_change_password, name='admin_config_change_password'),
    path('admin/notificaciones/', views.admin_notificaciones, name='admin_notificaciones'),
    path('admin/reportes/', views.admin_reportes, name='admin_reportes'),
    # ── Organización ──────────────────────────
    path('admin/organizacion/', views.admin_organizacion, name='admin_organizacion'),
    path('admin/organizacion/plantilla/crear/', views.admin_organizacion_plantilla_crear, name='admin_organizacion_plantilla_crear'),
    path('admin/organizacion/plantilla/<int:pk>/editar/', views.admin_organizacion_plantilla_editar, name='admin_organizacion_plantilla_editar'),
    path('admin/organizacion/oblea/crear/', views.admin_organizacion_oblea_crear, name='admin_organizacion_oblea_crear'),
    path('admin/organizacion/linea/crear/', views.admin_organizacion_linea_crear, name='admin_organizacion_linea_crear'),

    # ── Supervisor ────────────────────────────────────────────
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/ordenes/', views.supervisor_ordenes, name='supervisor_ordenes'),
    path('supervisor/ordenes/crear/', views.supervisor_ordenes_crear, name='supervisor_ordenes_crear'),
    path('supervisor/ordenes/<int:pk>/', views.supervisor_orden_detalle, name='supervisor_orden_detalle'),
    path('supervisor/lotes/', views.supervisor_lotes, name='supervisor_lotes'),
    path('supervisor/lotes/<int:pk>/', views.supervisor_lote_detalle, name='supervisor_lote_detalle'),
    path('supervisor/lotes/<int:pk>/hold/', views.supervisor_lote_hold, name='supervisor_lote_hold'),
    path('supervisor/lotes/<int:pk>/scrap/', views.supervisor_lote_scrap, name='supervisor_lote_scrap'),
    path('supervisor/lotes/registrar/', views.supervisor_lote_registrar, name='supervisor_lote_registrar'),
    path('supervisor/inventario/', views.supervisor_inventario, name='supervisor_inventario'),
    path('supervisor/inventario/entrada/', views.supervisor_inventario_entrada, name='supervisor_inventario_entrada'),
    path('supervisor/reportes/', views.supervisor_reportes, name='supervisor_reportes'),
    path('supervisor/notificaciones/', views.supervisor_notificaciones, name='supervisor_notificaciones'),
    path('supervisor/configuracion/', views.supervisor_configuracion, name='supervisor_configuracion'),

]
