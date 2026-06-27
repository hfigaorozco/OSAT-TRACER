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

    # Registro Kpi
    path('v1/create/registro_kpi/', views.CreateRegistroKpiAPIView.as_view(), name='create_registroKpi'),
    path('v1/list/registros_kpi/', views.ListRegistroKpiAPIView.as_view(), name='list_registroKpi'),
    path('v1/detail/registro_kpi/<int:pk>/', views.DetailRegistroKpiAPIView.as_view(), name='detail_registroKpi'),

    # Historial alerta
    path('v1/create/historial_alertas/', views.CreateHistorialAlertaAPIView.as_view(), name='create_historialAlerta'),
    path('v1/list/historiales_alertas/', views.ListHistorialAlertaAPIView.as_view(), name='list_historialAlerta'),
    path('v1/detail/historial_alertas/<int:registroKPI>/<int:alerta>/', views.DetailHistorialAlertaAPIView.as_view(), name='detail_historialAlerta'),
]