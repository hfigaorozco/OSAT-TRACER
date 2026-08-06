from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from . import serializers, models
from .services import calcular_kpi_por_linea, registrar_kpis_de_lote

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



### KPI POR LINEA (semáforo real, usado por el dashboard y por el reporte de KPI)
class KpiPorLineaAPIView(APIView):

    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        data = calcular_kpi_por_linea(fecha_inicio, fecha_fin)
        return Response(data)


### Registrar el KPI final de un lote (Yield/Throughput/OEE) al quedar en
### estado terminal — lo llama el cliente (produccion/views.py) justo
### después de confirmar que el lote quedó Terminada o Rechazada.
class RegistrarKpiPorLoteAPIView(APIView):

    def post(self, request, oblea_pk):
        from api_produccion.models import Oblea
        try:
            oblea = Oblea.objects.get(pk=oblea_pk)
        except Oblea.DoesNotExist:
            return Response({'detail': 'Lote no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        registrar_kpis_de_lote(oblea)
        return Response({'ok': True})


### ALERTAS PARA LA APP MÓVIL — clasificadas por tipo (stock/produccion/kpi)
### y priorizadas según la línea asignada al operador. La web (client/kpi/
### views.py::_build_alertas) hace esta misma clasificación cruzando 3
### endpoints en Python porque no tiene acceso directo al ORM; aquí, al
### estar en el backend, se hace con consultas directas — es la MISMA
### regla (kpi si hay Registro_Kpi ligado, produccion si hay Paso_Realizado
### ligado, si no stock) para no divergir entre web y móvil.
_PRIORIDAD_TIPO = {'produccion': 3, 'kpi': 2, 'stock': 1}


def _empleado_linea_codigo(empleado_numero):
    """Un operador no tiene línea propia en el modelo — se deriva de la
    máquina que tenga asignada (Maquina.empleado -> Maquina.linea), igual
    que ya hace EmpleadoListSerializer.get_linea_codigo."""
    if not empleado_numero:
        return None
    try:
        empleado_numero = int(empleado_numero)
    except (TypeError, ValueError):
        return None
    from api_maquinaria.models import Maquina
    # order_by explícito: si el empleado tiene más de una máquina asignada
    # (el modelo lo permite, no hay unicidad en Maquina.empleado), sin esto
    # cuál línea "gana" no está garantizado que sea la misma entre llamadas.
    maquina = (
        Maquina.objects.filter(empleado_id=empleado_numero, linea__isnull=False)
        .select_related('linea')
        .order_by('numSerie')
        .first()
    )
    return maquina.linea.codigo if maquina else None


class AlertasOperadorAPIView(APIView):

    def get(self, request):
        from api_produccion.models import Oblea, Orden, Paso_Realizado, Linea

        empleado_numero = request.query_params.get('empleado')
        mi_linea = _empleado_linea_codigo(empleado_numero)

        alertas = models.Alerta.objects.select_related('estadoAlerta').all()

        # order_by('numero') explícito: numero es PK autoincremental, así
        # que ordenar ascendente y dejar que dict() se quede con la última
        # fila de cada alerta_id es determinista (la más reciente) en vez
        # de depender del orden que MySQL devuelva por su cuenta.
        oblea_por_registro = dict(
            models.Registro_Kpi.objects.order_by('numero').values_list('alerta_id', 'oblea_id')
        )
        oblea_por_paso = dict(
            Paso_Realizado.objects.order_by('numero').values_list('alerta_id', 'oblea_id')
        )
        orden_por_oblea = dict(Oblea.objects.values_list('numero', 'orden_id'))
        linea_por_orden = dict(Orden.objects.exclude(linea__isnull=True).values_list('numero', 'linea_id'))
        lineas_map = {l.codigo: l.nombre for l in Linea.objects.all()}

        resultado = []
        for a in alertas:
            if a.numero in oblea_por_registro:
                tipo = 'kpi'
                oblea_id = oblea_por_registro[a.numero]
            elif a.numero in oblea_por_paso:
                tipo = 'produccion'
                oblea_id = oblea_por_paso[a.numero]
            else:
                tipo = 'stock'
                oblea_id = None

            linea_codigo = None
            if oblea_id is not None:
                orden_id = orden_por_oblea.get(oblea_id)
                linea_codigo = linea_por_orden.get(orden_id)

            leida = a.estadoAlerta_id == 'resue'
            es_mi_linea = bool(mi_linea) and linea_codigo == mi_linea

            prioridad = _PRIORIDAD_TIPO.get(tipo, 0)
            if es_mi_linea:
                prioridad += 10
            if not leida:
                prioridad += 5

            resultado.append({
                'numero': a.numero,
                'descripcion': a.descripcion,
                'fecha': a.fecha.isoformat(),
                'hora': a.hora.strftime('%H:%M'),
                'estadoAlerta': a.estadoAlerta_id,
                'leida': leida,
                'tipo': tipo,
                'linea_codigo': linea_codigo,
                'linea_nombre': lineas_map.get(linea_codigo),
                'es_mi_linea': es_mi_linea if mi_linea else None,
                'prioridad': prioridad,
                # Solo tipo/produccion tienen lote asociado — 'stock' siempre
                # llega en None, el cliente lo usa para saber si hay a dónde
                # navegar al tocar el detalle de la alerta.
                'oblea_id': oblea_id,
            })

        resultado.sort(key=lambda r: (-r['prioridad'], -r['numero']))
        return Response(resultado)