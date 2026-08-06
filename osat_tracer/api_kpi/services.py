from api_produccion.models import Linea, Paso_Realizado
from . import models


def calcular_kpi_por_linea(fecha_inicio=None, fecha_fin=None):
    """Agrega Registro_Kpi por línea de producción (join Registro_Kpi -> Oblea
    -> Orden -> Linea) y por Kpi, promediando 'valor' dentro del rango de
    fechas dado (o de siempre, si no se pasan fechas). Es la única función que
    calcula KPI por línea en todo el proyecto — la usan tanto el semáforo del
    dashboard (en vivo) como el reporte de KPI (foto congelada), para no
    duplicar el criterio en dos lugares.

    Devuelve una lista de dicts, uno por Kpi, cada uno con una celda por línea
    existente más una celda 'Global' (promedio de todas las líneas juntas).
    """
    registros = models.Registro_Kpi.objects.select_related('kpi', 'oblea__orden__linea')
    if fecha_inicio:
        registros = registros.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(fecha__lte=fecha_fin)

    kpis = list(models.Kpi.objects.all())
    lineas = list(Linea.objects.all().order_by('codigo'))

    # Un solo paso por los registros: acumula suma/conteo por (kpi, linea) y
    # por (kpi, None) para el bucket Global, evitando repetir la consulta.
    acumulado = {}
    for r in registros:
        linea_codigo = r.oblea.orden.linea_id if (r.oblea and r.oblea.orden) else None
        for clave in ((r.kpi_id, linea_codigo), (r.kpi_id, None)):
            acum = acumulado.setdefault(clave, [0, 0])
            acum[0] += r.valor
            acum[1] += 1

    resultado = []
    for kpi in kpis:
        celdas = []
        for linea in lineas:
            suma, cuenta = acumulado.get((kpi.clave, linea.codigo), (0, 0))
            valor = round(suma / cuenta, 1) if cuenta else None
            celdas.append({'linea_codigo': linea.codigo, 'linea_nombre': linea.nombre, 'valor': valor})
        suma_g, cuenta_g = acumulado.get((kpi.clave, None), (0, 0))
        valor_global = round(suma_g / cuenta_g, 1) if cuenta_g else None
        celdas.append({'linea_codigo': None, 'linea_nombre': 'Global', 'valor': valor_global})

        resultado.append({
            'kpi_clave': kpi.clave,
            'kpi_nombre': kpi.nombre,
            'unidad': kpi.unidad,
            'umbralVerde': kpi.umbralVerde,
            'umbralAmarillo': kpi.umbralAmarillo,
            'umbralRojo': kpi.umbralRojo,
            'celdas': celdas,
        })
    return resultado


def _semaforo_de(kpi, valor):
    """Los 3 KPI actuales (Yield, Throughput, OEE) son 'más alto es mejor'
    — umbralVerde > umbralAmarillo > umbralRojo — así que la comparación es
    la misma para los tres. Si algún día se agrega un KPI 'más bajo es
    mejor' (ej. scrap rate), esta función es el único lugar que hay que
    tocar."""
    if valor >= kpi.umbralVerde:
        return 'ver'
    if valor >= kpi.umbralAmarillo:
        return 'ama'
    return 'roj'


def _alerta_para_kpi(kpi, valor, codigo_semaforo, oblea):
    """Registro_Kpi exige una Alerta (FK obligatoria) — mismo patrón que ya
    usa CreatePasoRealizadoSerializer para Paso_Realizado: en amarillo/rojo
    se crea una alerta nueva y real (hay algo que revisar); en verde se
    reutiliza una alerta compartida 'en rango normal' por KPI (get_or_create)
    para no llenar la bandeja de Alertas de ruido en cada paso bueno."""
    estados = {e.codigo: e for e in models.EstadoAlerta.objects.filter(codigo__in=('sinre', 'resue'))}
    sin_resolver = estados.get('sinre') or models.EstadoAlerta.objects.first()
    resuelta = estados.get('resue') or sin_resolver

    if codigo_semaforo == 'roj':
        return models.Alerta.objects.create(
            descripcion=f'{kpi.nombre} crítico en {oblea} ({valor}{kpi.unidad})',
            estadoAlerta=sin_resolver,
        )
    if codigo_semaforo == 'ama':
        return models.Alerta.objects.create(
            descripcion=f'{kpi.nombre} en advertencia en {oblea} ({valor}{kpi.unidad})',
            estadoAlerta=sin_resolver,
        )
    alerta, _ = models.Alerta.objects.get_or_create(
        descripcion=f'{kpi.nombre} en rango normal',
        defaults={'estadoAlerta': resuelta},
    )
    return alerta


def registrar_kpis_de_lote(oblea):
    """Calcula y guarda el Yield/Throughput/OEE FINAL de un lote — se llama
    una sola vez, cuando el lote (Oblea) queda en estado terminal (Terminada
    o Rechazada), no después de cada paso individual. Throughput y OEE son
    medidas de todo el proceso (dies por hora del lote completo, rendimiento
    contra el tiempo estimado de TODOS sus pasos) — calcularlas a medio
    proceso las hacía salir "críticas" solo porque faltaba tiempo/pasos por
    recorrer, no porque el lote realmente rindiera mal. Se llama desde
    client/produccion/views.py::_avanzar_estado_lote_y_orden justo después
    de confirmar el estado final del lote, vía el endpoint
    /v1/kpi/registrar_por_lote/<oblea>/.

    Fórmulas (con los datos que hoy existen en el modelo; no hay tracking
    de tiempo muerto de máquina, así que Disponibilidad se asume 100%):
      - Yield      = diesGenerados final / cantidadDies inicial del lote.
      - Throughput = diesGenerados final / horas entre el primer y el
                     último Paso_Realizado del lote.
      - OEE        = Rendimiento x Calidad, donde Rendimiento = suma de
                     tiempoEstimado de todos los pasos / tiempo real
                     transcurrido (tope 100%), y Calidad = Yield.
    """
    oblea.refresh_from_db()
    if not oblea.orden_id or not oblea.orden.tipoOblea_id:
        return
    dies_iniciales = oblea.orden.tipoOblea.cantidadDies or 0
    if dies_iniciales <= 0:
        return

    pasos_de_la_oblea = list(
        Paso_Realizado.objects.filter(oblea=oblea).select_related('paso').order_by('fecha', 'hora')
    )
    if not pasos_de_la_oblea:
        return

    dies_actuales = oblea.diesGenerados or 0
    yield_pct = max(0.0, min(100.0, dies_actuales / dies_iniciales * 100))

    primer_paso = pasos_de_la_oblea[0]
    ultimo_paso = pasos_de_la_oblea[-1]
    horas_transcurridas = max((ultimo_paso.fecha - primer_paso.fecha).total_seconds() / 3600, 1 / 60)
    throughput = dies_actuales / horas_transcurridas

    segundos_estimados = sum((pr.paso.tiempoEstimado.total_seconds() for pr in pasos_de_la_oblea), 0.0)
    rendimiento = min(segundos_estimados / (horas_transcurridas * 3600), 1.0)
    oee_pct = max(0.0, min(100.0, rendimiento * (yield_pct / 100) * 100))

    valores_por_kpi = {'yie': yield_pct, 'thr': throughput, 'oee': oee_pct}
    kpis = {k.clave: k for k in models.Kpi.objects.filter(clave__in=valores_por_kpi)}
    semaforos = {s.codigo: s for s in models.Semaforo.objects.all()}

    for clave, valor in valores_por_kpi.items():
        kpi = kpis.get(clave)
        if not kpi:
            continue
        valor_redondeado = round(valor)
        codigo_semaforo = _semaforo_de(kpi, valor_redondeado)
        semaforo = semaforos.get(codigo_semaforo)
        if not semaforo:
            continue
        alerta = _alerta_para_kpi(kpi, valor_redondeado, codigo_semaforo, oblea)
        models.Registro_Kpi.objects.create(
            valor=valor_redondeado,
            oblea=oblea,
            kpi=kpi,
            semaforo=semaforo,
            alerta=alerta,
        )
