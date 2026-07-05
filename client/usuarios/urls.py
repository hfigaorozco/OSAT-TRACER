from django.urls import path
from . import views

urlpatterns = [
    # Admin dashboard
    path('admin-dash/', views.admin_dashboard, name='admin_dashboard'),

    # Cuentas y personal
    path('admin/cuentas/', views.admin_cuentas, name='admin_cuentas'),
    path('admin/cuentas/crear/', views.admin_cuentas_crear, name='admin_cuentas_crear'),
    path('admin/personal/', views.admin_personal, name='admin_personal'),
    path('admin/personal/crear/', views.admin_personal_crear, name='admin_personal_crear'),

    # Supervisor
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/configuracion/', views.supervisor_configuracion, name='supervisor_configuracion'),
]
