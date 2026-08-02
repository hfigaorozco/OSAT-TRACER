"""Snapshot + PDF del reporte de producción — de una orden completa
(oblea_num=None) o de un solo lote (oblea_num=<pk>)."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from api_produccion.models import Orden, Oblea, Paso_Realizado, Historial_Defectos
from .pdf_utils import (
    COLOR_GREEN, COLOR_TURQUOISE, COLOR_GOLD, COLOR_RED,
    _new_page, _draw_metric, _draw_section_title, _draw_table,
)


def computar_snapshot_orden_o_lote(orden_num, oblea_num=None):
    """Log de todo lo ocurrido en una orden (o en un solo lote de esa orden,
    si se pasa oblea_num) — pasos realizados, scrap, defectos, yield. Usa el
    mismo criterio de dies_iniciales/dies_activos ya establecido en el resto
    de la app: dies_iniciales = Tipo_Oblea.cantidadDies (fijo), dies_activos
    = Oblea.diesGenerados (el trigger ya lo mantiene al día)."""
    orden = Orden.objects.select_related('proceso', 'linea', 'tipoOblea', 'empleado').get(pk=orden_num)
    obleas_qs = Oblea.objects.filter(orden=orden)
    if oblea_num:
        obleas_qs = obleas_qs.filter(pk=oblea_num)
    obleas = list(obleas_qs.order_by('numero'))

    cantidad_dies_fija = orden.tipoOblea.cantidadDies or 0

    obleas_rows = []
    pasos_rows = []
    dies_iniciales_total = 0
    dies_activos_total = 0
    for ob in obleas:
        dies_iniciales_total += cantidad_dies_fija
        dies_activos_total += ob.diesGenerados
        yield_pct = round(ob.diesGenerados / cantidad_dies_fija * 100, 1) if cantidad_dies_fija else 0
        obleas_rows.append({
            'folio': f'LOT-{ob.numero:04d}',
            'dies_iniciales': cantidad_dies_fija,
            'dies_activos': ob.diesGenerados,
            'yield_pct': yield_pct,
            'estado': ob.estado_id,
        })
        pasos = (Paso_Realizado.objects
                 .filter(oblea=ob).select_related('paso', 'estado')
                 .order_by('numero'))
        for pr in pasos:
            defectos = list(
                Historial_Defectos.objects
                .filter(pasoRealizado=pr).select_related('defecto')
                .values_list('defecto__descripcion', flat=True)
            )
            pasos_rows.append({
                'lote': f'LOT-{ob.numero:04d}',
                'paso': pr.paso.nombre,
                'fecha': str(pr.fecha),
                'hora': str(pr.hora),
                'estado': pr.estado.descripcion,
                'scrap': pr.scrap,
                'observaciones': pr.observaciones or '',
                'defectos': ', '.join(defectos),
            })

    yield_global = round(dies_activos_total / dies_iniciales_total * 100, 1) if dies_iniciales_total else 0
    empleado = orden.empleado
    empleado_nombre = f'{empleado.nombre} {empleado.primerApell}' if empleado else '—'

    return {
        'orden_numero': orden.numero,
        'oblea_pk': oblea_num,
        'proceso_nombre': orden.proceso.nombre if orden.proceso else '—',
        'linea_nombre': orden.linea.nombre if orden.linea else '—',
        'tipo_oblea_nombre': orden.tipoOblea.descripcion if orden.tipoOblea else '—',
        'empleado_nombre': empleado_nombre,
        'dies_iniciales_total': dies_iniciales_total,
        'dies_activos_total': dies_activos_total,
        'yield_global': yield_global,
        'obleas_rows': obleas_rows,
        'pasos_rows': pasos_rows,
    }


def computar_snapshot_produccion_mensual(anio, mes):
    """Resumen de producción de TODO un mes — a diferencia del reporte por
    orden/lote, este agrega todas las órdenes creadas ese mes (producción no
    tiene un rango de fechas natural como inventario/KPI, así que el "rango"
    aquí es simplemente el mes completo)."""
    ordenes = list(
        Orden.objects.filter(fecha__year=anio, fecha__month=mes)
        .select_related('tipoOblea', 'proceso')
    )
    ordenes_rows = []
    dies_iniciales_total = 0
    dies_activos_total = 0
    ordenes_cerradas = 0
    oblea_ids_del_mes = []
    for orden in ordenes:
        obleas = list(Oblea.objects.filter(orden=orden))
        oblea_ids_del_mes.extend(ob.numero for ob in obleas)
        cantidad_dies_fija = orden.tipoOblea.cantidadDies if orden.tipoOblea else 0
        for ob in obleas:
            dies_iniciales_total += cantidad_dies_fija
            dies_activos_total += ob.diesGenerados
        if str(orden.estado_id).lower() == 'cerra':
            ordenes_cerradas += 1
        ordenes_rows.append({
            'orden': f'ORD-{orden.numero:04d}',
            'proceso': orden.proceso.nombre if orden.proceso else '—',
            'lotes': len(obleas),
            'estado': orden.estado_id,
        })

    scrap_total = sum(
        pr.scrap for pr in Paso_Realizado.objects.filter(oblea_id__in=oblea_ids_del_mes)
    )
    yield_pct = round(dies_activos_total / dies_iniciales_total * 100, 1) if dies_iniciales_total else 0

    return {
        'anio': anio,
        'mes': mes,
        'ordenes_count': len(ordenes_rows),
        'ordenes_cerradas': ordenes_cerradas,
        'dies_iniciales_total': dies_iniciales_total,
        'dies_activos_total': dies_activos_total,
        'scrap_total': scrap_total,
        'yield_pct': yield_pct,
        'ordenes_rows': ordenes_rows,
    }


def dibujar_pdf_reporte_produccion(snapshot):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    alcance = f"Lote LOT-{snapshot['oblea_pk']:04d}" if snapshot.get('oblea_pk') else f"Orden ORD-{snapshot['orden_numero']:04d} (todos sus lotes)"
    titulo = 'Reporte de producción'
    subtitulo = alcance
    pdf.setTitle(f'{titulo} - {subtitulo}')
    page_number = 1
    y = _new_page(pdf, width, height, page_number, titulo, subtitulo)

    metric_w = (width - 40 * mm) / 4
    _draw_metric(pdf, 15 * mm, y - 23 * mm, metric_w, 'Dies iniciales', snapshot['dies_iniciales_total'], COLOR_TURQUOISE)
    _draw_metric(pdf, 17 * mm + metric_w, y - 23 * mm, metric_w, 'Dies activos', snapshot['dies_activos_total'], COLOR_GREEN)
    _draw_metric(pdf, 19 * mm + metric_w * 2, y - 23 * mm, metric_w, 'Yield', f"{snapshot['yield_global']}%", COLOR_GOLD)
    _draw_metric(pdf, 21 * mm + metric_w * 3, y - 23 * mm, metric_w, 'Lotes', len(snapshot['obleas_rows']), COLOR_RED)
    y -= 36 * mm

    _draw_section_title(pdf, 15 * mm, y, 'Lotes incluidos')
    y -= 6 * mm
    y, page_number = _draw_table(
        pdf,
        snapshot['obleas_rows'],
        [('Lote', 'folio', 12), ('Dies ini.', 'dies_iniciales', 10), ('Dies act.', 'dies_activos', 10),
         ('Yield', 'yield_pct', 8), ('Estado', 'estado', 10)],
        15 * mm, y,
        [30 * mm, 30 * mm, 30 * mm, 25 * mm, 30 * mm],
        width, height, page_number, titulo, subtitulo,
    )
    y -= 10 * mm

    if y < 70 * mm:
        page_number += 1
        y = _new_page(pdf, width, height, page_number, titulo, subtitulo)
    _draw_section_title(pdf, 15 * mm, y, 'Pasos realizados')
    y -= 6 * mm
    _draw_table(
        pdf,
        snapshot['pasos_rows'] or [{'lote': '-', 'paso': 'Sin pasos registrados', 'fecha': '-', 'estado': '-', 'scrap': 0, 'defectos': '-'}],
        [('Lote', 'lote', 10), ('Paso', 'paso', 16), ('Fecha', 'fecha', 12),
         ('Estado', 'estado', 12), ('Scrap', 'scrap', 6), ('Defectos', 'defectos', 20)],
        15 * mm, y,
        [22 * mm, 34 * mm, 26 * mm, 26 * mm, 16 * mm, 41 * mm],
        width, height, page_number, titulo, subtitulo,
    )

    pdf.save()
    buffer.seek(0)
    return buffer
