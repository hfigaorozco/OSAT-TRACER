from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from . import serializers, models
from .services import calcular_kpi_por_linea

# Create your views here.

### CRUD SEMAFORO SERVICES
## Create Semaforo
class CreateSemaforoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateSemaforoSerializer

## List Semaforo
class ListSemaforoAPIView(APIView):
    
    def get(self, request):
        semaforos = models.Semaforo.objects.all()
        data = serializers.ListSemaforoSerializer(semaforos, many=True).data
        return Response(data)

## Detail Semaforo
class DetailSemaforoAPIView(generics.RetrieveAPIView):
    queryset = models.Semaforo.objects.all()
    serializer_class = serializers.DetailSemaforoSerializer
    lookup_field = 'pk'


### CRUD ESTADO_ALERTA SERVICES

## Create Estado_Alerta
class CreateEstadoAlertaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoAlertaSerializer

## List Estado_Alerta
class ListEstadoAlertaAPIView(APIView):
    
    def get(self, request):
        edos_alerta = models.EstadoAlerta.objects.all()
        data = serializers.ListEstadoAlertaSerializer(edos_alerta, many=True).data
        return Response(data)

## Detail Estado_Alerta
class DetailEstadoAlertaAPIView(generics.RetrieveAPIView):
    queryset = models.EstadoAlerta.objects.all()
    serializer_class = serializers.DetailEstadoAlertaSerializer
    lookup_field = 'pk'


### CRUD KPI SERVICES
## Create Kpi
class CreateKpiAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateKpiSerializer

## List Kpi
class ListKpiAPIView(APIView):
    
    def get(self, request):
        kpis = models.Kpi.objects.all()
        data = serializers.ListKpiSerializer(kpis, many=True).data
        return Response(data)

## Detail Kpi
class DetailKpiAPIView(generics.RetrieveAPIView):
    queryset = models.Kpi.objects.all()
    serializer_class = serializers.DetailKpiSerializer
    lookup_field = 'pk'

## Update Kpi
class UpdateKpiAPIView(generics.UpdateAPIView):
    queryset = models.Kpi.objects.all()
    serializer_class = serializers.UpdateKpiSerializer
    lookup_field = 'pk'


### CRUD ALERTA SERVICES
## Create Alerta
class CreateAlertaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateAlertaSerializer

## List Alerta
class ListAlertaAPIView(APIView):
    
    def get(self, request):
        alertas = models.Alerta.objects.all()
        data = serializers.ListAlertaSerializer(alertas, many=True).data
        return Response(data)

## Detail Alerta
class DetailAlertaAPIView(generics.RetrieveAPIView):
    queryset = models.Alerta.objects.all()
    serializer_class = serializers.DetailAlertaSerializer
    lookup_field = 'pk'

## Update Alerta
class UpdateAlertaAPIView(generics.UpdateAPIView):
    queryset = models.Alerta.objects.all()
    serializer_class = serializers.UpdateAlertaSerializer
    lookup_field = 'pk'


### CRUD REGISTRO_KPI SERVICES
## Create Registro_Kpi
class CreateRegistroKpiAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateRegistroKpiSerializer

## List Registro_Kpi
class ListRegistroKpiAPIView(APIView):
    
    def get(self, request):
        registros_kpi = models.Registro_Kpi.objects.all()
        data = serializers.ListRegistroKpiSerializer(registros_kpi, many=True).data
        return Response(data)

## Detail Registro_Kpi
class DetailRegistroKpiAPIView(generics.RetrieveAPIView):
    queryset = models.Registro_Kpi.objects.all()
    serializer_class = serializers.DetailRegistroKpiSerializer
    lookup_field = 'pk'


### CRUD HISTORIAL_ALERTAS SERVICES
## Create Historial_alerta
class CreateHistorialAlertasAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateHistorialAlertasSerializer

## List Historial_alerta
class ListHistorialAlertasAPIView(APIView):
    
    def get(self, request):
        historiales = models.Historial_Alertas.objects.all()
        data = serializers.ListHistorialAlertasSerializer(historiales, many=True).data
        return Response(data)

## Detail Historial_alerta
class DetailHistorialAlertaAPIView(generics.RetrieveAPIView):
    serializer_class = serializers.DetailHistorialAlertasSerializer

    def get_object(self):
        return get_object_or_404(models.Historial_Alertas, registroKPI_id=self.kwargs['registroKPI'], alerta_id=self.kwargs['alerta'])


### KPI POR LINEA (semáforo real, usado por el dashboard y por el reporte de KPI)
class KpiPorLineaAPIView(APIView):

    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        data = calcular_kpi_por_linea(fecha_inicio, fecha_fin)
        return Response(data)