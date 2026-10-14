import re
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
        resultado = _construir_alertas_base()
        resultado.sort(key=lambda r: -r['numero'])
        return Response(resultado)

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


### ALERTAS — clasificación y enriquecimiento COMPARTIDO entre la web
### (ListAlertaAPIView, consumida por client/kpi/views.py::_build_alertas)
### y la app móvil (AlertasOperadorAPIView). Antes cada lado reimplementaba
### su propia versión de esta clasificación (la web cruzando 3 endpoints en
### Python, el móvil con consultas directas) y podían divergir; ahora ambas
### parten del mismo _construir_alertas_base() para no volver a desalinearse,
### y cada una le agrega encima solo lo que le es propio (la web ordena por
### más reciente, el móvil agrega prioridad/es_mi_linea).
_PRIORIDAD_TIPO = {'hold': 4, 'produccion': 3, 'kpi': 2, 'stock': 1}

# Las alertas de Hold (manual desde _lote_hold via UpdateObleaSerializer,
# automática desde t_scrap_excedente_del_permitido vía
# _avanzar_estado_lote_y_orden, o al rechazar un lote para liberar la orden
# vía _lote_rechazar_liberando_orden) se crean como Alerta suelta, sin FK a
# Oblea/Paso_Realizado/Registro_Kpi — así que no hay forma de clasificarlas
# por relación como al resto. Se reconocen por el texto fijo de descripcion:
# las 3 variantes siempre contienen la palabra "Hold", y casi siempre un
# folio LOT-XXXX (para resolver oblea_id) y/o "Orden #N" (para resolver la
# orden directamente cuando no hay folio de lote en el texto).
_RE_HOLD_LOTE = re.compile(r'LOT-(\d+)')
_RE_HOLD_ORDEN = re.compile(r'Orden #(\d+)')
_RE_HOLD_DESC = re.compile(r'Hold')

# Placeholder técnico: Paso_Realizado.alerta es FK obligatoria, así que cada
# paso completado SIN incidentes reutiliza esta misma Alerta compartida (ver
# CreatePasoRealizadoSerializer.create()) solo para satisfacer la relación.
# No es una notificación real — mostrarla en las pantallas de Alertas es
# puro ruido (y además, al estar ligada a decenas de pasos distintos, no
# hay un solo lote/orden "correcto" al que apuntarla). Se excluye por completo.
_DESCRIPCION_PLACEHOLDER = 'Sin novedad'


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


def _construir_alertas_base():
    """Clasifica y enriquece TODAS las alertas (menos el placeholder 'Sin
    novedad') con la mayor información resoluble: tipo, lote/orden/línea
    asociados, folios legibles, operador asignado, y el detalle específico
    del tipo (valor/umbral de KPI, paso + defectos de producción)."""
    from api_produccion.models import Oblea, Orden, Paso_Realizado, Linea, Historial_Defectos

    alertas_qs = (
        models.Alerta.objects
        .exclude(descripcion=_DESCRIPCION_PLACEHOLDER)
        .select_related('estadoAlerta')
        .order_by('numero')
    )

    # order_by('numero') + dict/último-gana: determinista (el registro más
    # reciente ligado a esa alerta), igual que antes.
    registro_por_alerta = {}
    for r in models.Registro_Kpi.objects.select_related('kpi', 'semaforo').order_by('numero'):
        registro_por_alerta[r.alerta_id] = r

    paso_por_alerta = {}
    for p in Paso_Realizado.objects.select_related('paso').order_by('numero'):
        paso_por_alerta[p.alerta_id] = p

    defectos_por_paso = {}
    for hd in Historial_Defectos.objects.select_related('defecto').order_by('id'):
        defectos_por_paso.setdefault(hd.pasoRealizado_id, []).append(hd.defecto.descripcion)

    orden_por_oblea = dict(Oblea.objects.values_list('numero', 'orden_id'))
    ordenes_map = {o.numero: o for o in Orden.objects.select_related('empleado').all()}
    lineas_map = {l.codigo: l.nombre for l in Linea.objects.all()}

    resultado = []
    for a in alertas_qs:
        reg = registro_por_alerta.get(a.numero)
        paso = paso_por_alerta.get(a.numero)
        oblea_id = None
        orden_numero = None
        extra = {
            'kpi_nombre': None, 'kpi_valor': None, 'kpi_umbral_verde': None,
            'kpi_umbral_amarillo': None, 'kpi_umbral_rojo': None, 'kpi_semaforo': None,
            'paso_nombre': None, 'paso_scrap': None, 'defectos': [],
        }

        if reg is not None:
            tipo = 'kpi'
            oblea_id = reg.oblea_id
            extra.update({
                'kpi_nombre': reg.kpi.nombre if reg.kpi_id else None,
                'kpi_valor': reg.valor,
                'kpi_umbral_verde': reg.kpi.umbralVerde if reg.kpi_id else None,
                'kpi_umbral_amarillo': reg.kpi.umbralAmarillo if reg.kpi_id else None,
                'kpi_umbral_rojo': reg.kpi.umbralRojo if reg.kpi_id else None,
                'kpi_semaforo': reg.semaforo.descripcion if reg.semaforo_id else None,
            })
        elif paso is not None:
            tipo = 'produccion'
            oblea_id = paso.oblea_id
            extra.update({
                'paso_nombre': paso.paso.nombre if paso.paso_id else None,
                'paso_scrap': paso.scrap,
                'defectos': defectos_por_paso.get(paso.numero, []),
            })
        elif _RE_HOLD_DESC.search(a.descripcion or ''):
            tipo = 'hold'
            m_lote = _RE_HOLD_LOTE.search(a.descripcion or '')
            oblea_id = int(m_lote.group(1)) if m_lote else None
            m_orden = _RE_HOLD_ORDEN.search(a.descripcion or '')
            if m_orden:
                orden_numero = int(m_orden.group(1))
        elif (a.descripcion or '').startswith('Orden #'):
            # Rechazo manual de orden (ver _orden_rechazar) — no nace de un
            # paso ni de un KPI, pero sigue siendo un evento de producción.
            tipo = 'produccion'
            m_orden = _RE_HOLD_ORDEN.search(a.descripcion or '')
            if m_orden:
                orden_numero = int(m_orden.group(1))
        else:
            tipo = 'stock'

        if oblea_id is not None:
            orden_numero = orden_por_oblea.get(oblea_id)

        orden_obj = ordenes_map.get(orden_numero) if orden_numero else None
        linea_codigo = orden_obj.linea_id if orden_obj else None
        empleado_nombre = None
        if orden_obj and orden_obj.empleado_id:
            empleado_nombre = f'{orden_obj.empleado.nombre} {orden_obj.empleado.primerApell}'.strip()

        leida = a.estadoAlerta_id == 'resue'

        item = {
            'numero': a.numero,
            'descripcion': a.descripcion,
            'fecha': a.fecha.isoformat(),
            'hora': a.hora.strftime('%H:%M'),
            'estadoAlerta': a.estadoAlerta_id,
            'leida': leida,
            'tipo': tipo,
            # 'kpi'/'produccion'/'hold' casi siempre tienen lote asociado —
            # 'stock' siempre llega en None, el cliente lo usa para saber si
            # hay a dónde navegar al tocar el detalle de la alerta.
            'oblea_id': oblea_id,
            'orden_numero': orden_numero,
            'folio_lote': f'LOT-{oblea_id:04d}' if oblea_id else None,
            'folio_orden': f'ORD-{orden_numero:04d}' if orden_numero else None,
            'linea_codigo': linea_codigo,
            'linea_nombre': lineas_map.get(linea_codigo),
            'empleado_nombre': empleado_nombre,
        }
        item.update(extra)
        resultado.append(item)

    return resultado


class AlertasOperadorAPIView(APIView):

    def get(self, request):
        empleado_numero = request.query_params.get('empleado')
        mi_linea = _empleado_linea_codigo(empleado_numero)

        resultado = _construir_alertas_base()
        for item in resultado:
            es_mi_linea = bool(mi_linea) and item['linea_codigo'] == mi_linea
            prioridad = _PRIORIDAD_TIPO.get(item['tipo'], 0)
            if es_mi_linea:
                prioridad += 10
            if not item['leida']:
                prioridad += 5
            item['es_mi_linea'] = es_mi_linea if mi_linea else None
            item['prioridad'] = prioridad

        resultado.sort(key=lambda r: (-r['prioridad'], -r['numero']))
        return Response(resultado)