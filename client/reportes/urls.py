from django.urls import path
from . import views

urlpatterns = [
    path('admin/reportes/', views.admin_reportes, name='admin_reportes'),
    path('supervisor/reportes/', views.supervisor_reportes, name='supervisor_reportes'),
]
