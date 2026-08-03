"""PDF del reporte mensual — combina los 3 snapshots (producción, inventario,
KPI) de ReporteMensual en un solo documento, una sección por página."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .pdf_utils import (
    COLOR_GREEN, COLOR_TURQUOISE, COLOR_GOLD, COLOR_RED,
    _new_page, _draw_metric, _draw_section_title, _draw_table,
)
from api_inventario.services import ESTADO_COLOR


def dibujar_pdf_reporte_mensual(snapshot_produccion, snapshot_inventario, snapshot_kpi):
    anio = snapshot_produccion.get('anio')
    mes = snapshot_produccion.get('mes')
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    titulo = 'Reporte mensual'
    subtitulo = f'{mes:02d}/{anio}' if anio and mes else ''
    pdf.setTitle(f'{titulo} - {subtitulo}')
    page_number = 1

    # ── Producción ──────────────────────────────────────────────
    y = _new_page(pdf, width, height, page_number, titulo, subtitulo + ' · Producción')
    metric_w = (width - 40 * mm) / 4
    _draw_metric(pdf, 15 * mm, y - 23 * mm, metric_w, 'Órdenes', snapshot_produccion.get('ordenes_count', 0), COLOR_TURQUOISE)
    _draw_metric(pdf, 17 * mm + metric_w, y - 23 * mm, metric_w, 'Cerradas', snapshot_produccion.get('ordenes_cerradas', 0), COLOR_GREEN)
    _draw_metric(pdf, 19 * mm + metric_w * 2, y - 23 * mm, metric_w, 'Yield', f"{snapshot_produccion.get('yield_pct', 0)}%", COLOR_GOLD)
    _draw_metric(pdf, 21 * mm + metric_w * 3, y - 23 * mm, metric_w, 'Scrap total', snapshot_produccion.get('scrap_total', 0), COLOR_RED)
    y -= 36 * mm
    _draw_section_title(pdf, 15 * mm, y, 'Órdenes del mes')
    y -= 6 * mm
    _draw_table(
        pdf,
        snapshot_produccion.get('ordenes_rows') or [{'orden': '-', 'proceso': 'Sin órdenes este mes', 'lotes': 0, 'estado': '-'}],
        [('Orden', 'orden', 12), ('Proceso', 'proceso', 24), ('Lotes', 'lotes', 8), ('Estado', 'estado', 10)],
        15 * mm, y, [30 * mm, 80 * mm, 30 * mm, 30 * mm],
        width, height, page_number, titulo, subtitulo,
    )

    # ── Inventario ──────────────────────────────────────────────
    page_number += 1
    y = _new_page(pdf, width, height, page_number, titulo, subtitulo + ' · Inventario')
    _draw_metric(pdf, 15 * mm, y - 23 * mm, metric_w, 'Materiales', snapshot_inventario.get('materiales', 0), COLOR_TURQUOISE)
    _draw_metric(pdf, 17 * mm + metric_w, y - 23 * mm, metric_w, 'Bajo mínimo', snapshot_inventario.get('bajo_minimo', 0), COLOR_RED)
    _draw_metric(pdf, 19 * mm + metric_w * 2, y - 23 * mm, metric_w, 'Consumo total', snapshot_inventario.get('consumo_total', 0), COLOR_GOLD)
    _draw_metric(pdf, 21 * mm + metric_w * 3, y - 23 * mm, metric_w, 'Movimientos', snapshot_inventario.get('movimientos_count', 0), COLOR_GREEN)
    y -= 36 * mm
    inventario_rows = [
        {**r, 'estado_color': ESTADO_COLOR[r['estado_clave']]}
        for r in snapshot_inventario.get('inventario_rows', [])
    ]
    _draw_section_title(pdf, 15 * mm, y, 'Stock al cierre del mes')
    y -= 6 * mm
    _draw_table(
        pdf, inventario_rows,
        [('Codigo', 'codigo', 8), ('Material', 'material', 22), ('Minimo', 'minimo', 8),
         ('Actual', 'actual', 8), ('Estado', 'estado', 16)],
        15 * mm, y, [25 * mm, 65 * mm, 25 * mm, 25 * mm, 40 * mm],
        width, height, page_number, titulo, subtitulo,
    )

    # ── KPI ─────────────────────────────────────────────────────
    page_number += 1
    y = _new_page(pdf, width, height, page_number, titulo, subtitulo + ' · KPI por línea')
    filas = snapshot_kpi.get('filas', [])
    _draw_metric(pdf, 15 * mm, y - 23 * mm, width - 30 * mm, 'KPIs evaluados', len(filas), COLOR_TURQUOISE)
    y -= 36 * mm
    columnas_nombres = [c.get('linea_nombre', '—') for c in filas[0]['celdas']] if filas else []
    columns = [('KPI', 'kpi', 16)] + [(nombre, f'col{i}', 14) for i, nombre in enumerate(columnas_nombres)]
    usable = width - 30 * mm
    kpi_col_w = 45 * mm
    resto = usable - kpi_col_w
    col_widths = [kpi_col_w] + ([resto / len(columnas_nombres)] * len(columnas_nombres) if columnas_nombres else [])
    rows = []
    for fila in filas:
        row = {'kpi': f"{fila.get('kpi_nombre', '')} ({fila.get('unidad', '')})"}
        for i, celda in enumerate(fila.get('celdas', [])):
            valor = celda.get('valor')
            row[f'col{i}'] = valor if valor is not None else '—'
        rows.append(row)
    _draw_section_title(pdf, 15 * mm, y, 'KPI por línea de producción')
    y -= 6 * mm
    _draw_table(
        pdf, rows or [{'kpi': 'Sin registros de KPI este mes'}],
        columns, 15 * mm, y, col_widths,
        width, height, page_number, titulo, subtitulo,
    )

    pdf.save()
    buffer.seek(0)
    return buffer
