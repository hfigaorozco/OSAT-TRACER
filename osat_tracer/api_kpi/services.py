from api_produccion.models import Linea
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
