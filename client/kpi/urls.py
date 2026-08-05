from django.urls import path
from . import views

urlpatterns = [
    # Admin Alertas
    path('admin/notificaciones/', views.admin_notificaciones, name='admin_notificaciones'),
    path('admin/notificaciones/<int:pk>/marcar-leida/', views.admin_alerta_marcar_leida, name='admin_alerta_marcar_leida'),
    path('admin/notificaciones/marcar-todas-leidas/', views.admin_alertas_marcar_todas_leidas, name='admin_alertas_marcar_todas_leidas'),

    # Supervisor Alertas
    path('supervisor/notificaciones/', views.supervisor_notificaciones, name='supervisor_notificaciones'),
    path('supervisor/notificaciones/<int:pk>/marcar-leida/', views.supervisor_alerta_marcar_leida, name='supervisor_alerta_marcar_leida'),
    path('supervisor/notificaciones/marcar-todas-leidas/', views.supervisor_alertas_marcar_todas_leidas, name='supervisor_alertas_marcar_todas_leidas'),

    # Configuración KPI y catálogos
    path('admin/configuracion/', views.admin_configuracion, name='admin_configuracion'),
    path('admin/configuracion/kpi/', views.admin_config_kpi_save, name='admin_config_kpi_save'),
    path('admin/configuracion/defecto/', views.admin_config_defecto_crear, name='admin_config_defecto_crear'),
    path('admin/configuracion/defecto/<str:pk>/editar/', views.admin_config_defecto_editar, name='admin_config_defecto_editar'),
    path('admin/configuracion/defecto/<str:pk>/estado/', views.admin_config_defecto_toggle_estado, name='admin_config_defecto_toggle_estado'),
    path('admin/configuracion/password/', views.admin_config_change_password, name='admin_config_change_password'),
]
