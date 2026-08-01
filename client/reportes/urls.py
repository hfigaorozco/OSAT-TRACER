from django.urls import path
from . import views

urlpatterns = [
    path('admin/reportes/', views.AdminReportesView.as_view(), name='admin_reportes'),
    path('supervisor/reportes/', views.SupervisorReportesView.as_view(), name='supervisor_reportes'),
]