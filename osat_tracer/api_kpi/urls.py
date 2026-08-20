from django.urls import path
from . import views

urlpatterns = [
    # Semaforo
    path('v1/create/semaforo/', views.CreateSemaforoAPIView.as_view(), name='create_semaforo'),
    path('v1/list/semaforos/', views.ListSemaforoAPIView.as_view(), name='list_semaforo'),
    path('v1/detail/semaforo/<str:pk>/', views.DetailSemaforoAPIView.as_view(), name='detail_semaforo'),

    # EstadoAlerta
    path('v1/create/estado_alerta/', views.CreateEstadoAlertaAPIView.as_view(), name='create_edoAlerta'),
    path('v1/list/estados_alerta/', views.ListEstadoAlertaAPIView.as_view(), name='list_edoAlerta'),
    path('v1/detail/estado_alerta/<str:pk>/', views.DetailEstadoAlertaAPIView.as_view(), name='detail_edoAlerta'),

    # Kpi
    path('v1/create/kpi/', views.CreateKpiAPIView.as_view(), name='create_kpi'),
    path('v1/list/kpis/', views.ListKpiAPIView.as_view(), name='list_kpi'),
    path('v1/detail/kpi/<str:pk>/', views.DetailKpiAPIView.as_view(), name='detail_kpi'),
    path('v1/update/kpi/<str:pk>/', views.UpdateKpiAPIView.as_view(), name='update_kpi'),

    # Alerta
    path('v1/create/alerta/', views.CreateAlertaAPIView.as_view(), name='create_alerta'),
    path('v1/list/alertas/', views.ListAlertaAPIView.as_view(), name='list_alerta'),
    path('v1/detail/alerta/<int:pk>/', views.DetailAlertaAPIView.as_view(), name='detail_alerta'),
    path('v1/update/alerta/<int:pk>/', views.UpdateAlertaAPIView.as_view(), name='update_alerta'),
    path('v1/list/alertas_operador/', views.AlertasOperadorAPIView.as_view(), name='list_alertas_operador'),

    # Registro Kpi
    path('v1/create/registro_kpi/', views.CreateRegistroKpiAPIView.as_view(), name='create_registroKpi'),
    path('v1/list/registros_kpi/', views.ListRegistroKpiAPIView.as_view(), name='list_registroKpi'),
    path('v1/detail/registro_kpi/<int:pk>/', views.DetailRegistroKpiAPIView.as_view(), name='detail_registroKpi'),

    # KPI por línea (semáforo real)
    path('v1/kpi/semaforo_por_linea/', views.KpiPorLineaAPIView.as_view(), name='kpi_semaforo_por_linea'),

    # Registrar el KPI final de un lote (Yield/Throughput/OEE), una vez que
    # queda en estado terminal (Terminada o Rechazada).
    path('v1/kpi/registrar_por_lote/<int:oblea_pk>/', views.RegistrarKpiPorLoteAPIView.as_view(), name='kpi_registrar_por_lote'),
]