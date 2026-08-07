from django.urls import path
from . import views

urlpatterns = [
    # Admin dashboard
    path('admin/dash/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/dash/pasos-hoy/', views.admin_pasos_hoy_detalle, name='admin_pasos_hoy_detalle'),

    # Personal — tabla unificada
    path('admin/personal/', views.admin_personal, name='admin_personal'),
    path('admin/personal/crear/', views.admin_personal_crear, name='admin_personal_crear'),
    path('admin/personal/<int:pk>/editar/', views.admin_personal_editar, name='admin_personal_editar'),
    path('admin/personal/<int:pk>/estado/', views.admin_personal_toggle_estado, name='admin_personal_toggle_estado'),

    # Cuentas (redirigen a personal)
    path('admin/cuentas/', views.admin_cuentas, name='admin_cuentas'),
    path('admin/cuentas/crear/', views.admin_cuentas_crear, name='admin_cuentas_crear'),

    # Supervisor
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/configuracion/', views.supervisor_configuracion, name='supervisor_configuracion'),
]

