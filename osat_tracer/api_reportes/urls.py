from django.urls import path

from api_reportes import views

app_name = "api_reportes"

urlpatterns = [
    ## Reporte (producción)
    path('v1/create/reportes/', views.CreateReporteAPIView.as_view(), name="create_reporte"),
    path('v1/list/reportes/', views.ListReportesAPIView.as_view(), name="list_reportes"),
    path('v1/detail/reportes/<int:pk>/', views.DetailReporteAPIView.as_view(), name="detail_reporte"),
    path('v1/update/reportes/<int:pk>/', views.UpdateReporteAPIView.as_view(), name="update_reporte"),
    path('v1/reporte/<int:pk>/pdf/', views.PdfReporteAPIView.as_view(), name="pdf_reporte"),

    ## ReporteInventario
    path('v1/create/reporte_inventario/', views.CreateReporteInventarioAPIView.as_view(), name="create_reporte_inventario"),
    path('v1/list/reportes_inventario/', views.ListReporteInventarioAPIView.as_view(), name="list_reportes_inventario"),
    path('v1/detail/reporte_inventario/<int:pk>/', views.DetailReporteInventarioAPIView.as_view(), name="detail_reporte_inventario"),
    path('v1/reporte_inventario/<int:pk>/pdf/', views.PdfReporteInventarioAPIView.as_view(), name="pdf_reporte_inventario"),

    ## ReporteKpi
    path('v1/create/reporte_kpi/', views.CreateReporteKpiAPIView.as_view(), name="create_reporte_kpi"),
    path('v1/list/reportes_kpi/', views.ListReporteKpiAPIView.as_view(), name="list_reportes_kpi"),
    path('v1/detail/reporte_kpi/<int:pk>/', views.DetailReporteKpiAPIView.as_view(), name="detail_reporte_kpi"),
    path('v1/reporte_kpi/<int:pk>/pdf/', views.PdfReporteKpiAPIView.as_view(), name="pdf_reporte_kpi"),

    ## ReporteMensual
    path('v1/create/reporte_mensual/', views.CreateReporteMensualAPIView.as_view(), name="create_reporte_mensual"),
    path('v1/list/reportes_mensuales/', views.ListReporteMensualAPIView.as_view(), name="list_reportes_mensuales"),
    path('v1/detail/reporte_mensual/<int:pk>/', views.DetailReporteMensualAPIView.as_view(), name="detail_reporte_mensual"),
    path('v1/reporte_mensual/<int:pk>/pdf/', views.PdfReporteMensualAPIView.as_view(), name="pdf_reporte_mensual"),
]
