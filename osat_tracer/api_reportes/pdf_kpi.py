"""PDF del reporte de KPI por línea — snapshot['filas'] tiene la misma forma
que calcular_kpi_por_linea() (una fila por KPI, celdas por línea + Global),
así que el dashboard en vivo y este reporte congelado comparten el mismo
cálculo, solo cambia si se guarda o se muestra al momento."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .pdf_utils import COLOR_TURQUOISE, _new_page, _draw_metric, _draw_section_title, _draw_table


def dibujar_pdf_reporte_kpi(snapshot):
    filas = snapshot.get('filas', [])
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    titulo = 'Reporte de KPI por línea'
    subtitulo = f"{snapshot.get('fecha_inicio') or 'Inicio'} a {snapshot.get('fecha_fin') or 'Actual'}"
    pdf.setTitle(f'{titulo} - {subtitulo}')
    page_number = 1
    y = _new_page(pdf, width, height, page_number, titulo, subtitulo)

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
        pdf,
        rows or [{'kpi': 'Sin registros de KPI en el periodo'}],
        columns, 15 * mm, y, col_widths,
        width, height, page_number, titulo, subtitulo,
    )

    pdf.save()
    buffer.seek(0)
    return buffer
