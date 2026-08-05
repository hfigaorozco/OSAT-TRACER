from django.urls import path
from . import views

urlpatterns = [
    path('admin/reportes/', views.AdminReportesView.as_view(), name='admin_reportes'),
    path('admin/reportes/generar/', views.AdminReportesGenerarView.as_view(), name='admin_reportes_generar'),
    path('admin/reportes/generar-produccion/', views.AdminReportesGenerarProduccionView.as_view(), name='admin_reportes_generar_produccion'),
    path('admin/reportes/mensual/', views.AdminReportesMensualesView.as_view(), name='admin_reportes_mensual'),

    path('supervisor/reportes/', views.SupervisorReportesView.as_view(), name='supervisor_reportes'),
    path('supervisor/reportes/generar/', views.SupervisorReportesGenerarView.as_view(), name='supervisor_reportes_generar'),
    path('supervisor/reportes/generar-produccion/', views.SupervisorReportesGenerarProduccionView.as_view(), name='supervisor_reportes_generar_produccion'),
    path('supervisor/reportes/mensual/', views.SupervisorReportesMensualesView.as_view(), name='supervisor_reportes_mensual'),
]
