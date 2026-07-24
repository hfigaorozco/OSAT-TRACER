from django.urls import path

from api_reportes import views

app_name = "api_reportes"

urlpatterns = [
    ## Reportes
    path('v1/create/reportes/', views.CreateReporteAPIView.as_view(), name="create_reporte"),
    path('v1/list/reportes/', views.ListReportesAPIView.as_view(), name="list_reportes"),
    path('v1/detail/reportes/<int:pk>/', views.DetailReporteAPIView.as_view(), name="detail_reporte"),
    path('v1/update/reportes/<int:pk>/', views.UpdateReporteAPIView.as_view(), name="update_reporte"),
]