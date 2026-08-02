"""Primitivas de dibujo genéricas para todos los reportes en PDF (producción,
inventario, KPI, mensual). Extraídas de api_inventario/services.py, que fue
donde se escribieron originalmente para el primer reporte (inventario) —
no son específicas de inventario, así que viven aquí y ese módulo las
importa de vuelta, sin cambiar su comportamiento."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

COLOR_BG = colors.HexColor('#1C2433')
COLOR_PANEL = colors.HexColor('#243040')
COLOR_GREEN = colors.HexColor('#16A85E')
COLOR_TURQUOISE = colors.HexColor('#009EAF')
COLOR_GOLD = colors.HexColor('#F5A623')
COLOR_RED = colors.HexColor('#EF5350')
COLOR_TEXT = colors.HexColor('#1A202C')
COLOR_MUTED = colors.HexColor('#718096')
COLOR_BORDER = colors.HexColor('#E2E8F0')
COLOR_TABLE_HEAD = colors.HexColor('#F7FAFC')


def _draw_header(pdf, width, height, titulo, subtitulo):
    pdf.setFillColor(COLOR_BG)
    pdf.rect(0, height - 35 * mm, width, 35 * mm, fill=1, stroke=0)
    pdf.setFillColor(COLOR_GREEN)
    pdf.rect(0, height - 35 * mm, 5 * mm, 35 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(16 * mm, height - 16 * mm, 'OSAT TRACER')
    pdf.setFont('Helvetica', 9)
    pdf.drawString(16 * mm, height - 24 * mm, titulo)
    pdf.setFillColor(colors.HexColor('#C4C5D0'))
    pdf.drawRightString(width - 16 * mm, height - 17 * mm, subtitulo)


def _draw_footer(pdf, width, page_number):
    pdf.setStrokeColor(COLOR_BORDER)
    pdf.line(15 * mm, 13 * mm, width - 15 * mm, 13 * mm)
    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont('Helvetica', 8)
    pdf.drawString(15 * mm, 8 * mm, 'Reporte generado automaticamente desde OSAT TRACER')
    pdf.drawRightString(width - 15 * mm, 8 * mm, f'Pagina {page_number}')


def _new_page(pdf, width, height, page_number, titulo, subtitulo):
    if page_number > 1:
        pdf.showPage()
    _draw_header(pdf, width, height, titulo, subtitulo)
    _draw_footer(pdf, width, page_number)
    return height - 50 * mm


def _draw_metric(pdf, x, y, w, label, value, accent):
    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(COLOR_BORDER)
    pdf.roundRect(x, y, w, 23 * mm, 4, fill=1, stroke=1)
    pdf.setFillColor(accent)
    pdf.roundRect(x, y, 3 * mm, 23 * mm, 2, fill=1, stroke=0)
    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont('Helvetica', 8)
    pdf.drawString(x + 7 * mm, y + 14 * mm, label.upper())
    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(x + 7 * mm, y + 6 * mm, str(value))


def _draw_section_title(pdf, x, y, title):
    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont('Helvetica-Bold', 11)
    pdf.drawString(x, y, title)
    pdf.setStrokeColor(COLOR_GREEN)
    pdf.setLineWidth(1)
    pdf.line(x, y - 2 * mm, x + 35 * mm, y - 2 * mm)


def _fit_text(text, max_chars):
    text = str(text or '')
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + '...'


def _draw_table(pdf, rows, columns, x, y, col_widths, width, height, page_number, titulo, subtitulo):
    """columns: lista de (encabezado, llave, max_chars). Cada row puede traer
    una llave '<llave>_color' con un objeto Color de reportlab para pintar
    ese valor (por defecto COLOR_TEXT) — quien arma el snapshot JSON debe
    guardar una CLAVE de estado (ej. 'critico'/'ok'), no el objeto Color en
    sí (no es serializable); la resolución a Color va en la capa de dibujo."""
    row_h = 8 * mm
    head_h = 8 * mm

    def draw_header(current_y):
        pdf.setFillColor(COLOR_TABLE_HEAD)
        pdf.setStrokeColor(COLOR_BORDER)
        pdf.rect(x, current_y - head_h, sum(col_widths), head_h, fill=1, stroke=1)
        pdf.setFillColor(COLOR_MUTED)
        pdf.setFont('Helvetica-Bold', 7)
        cx = x
        for idx, col in enumerate(columns):
            pdf.drawString(cx + 2 * mm, current_y - 5 * mm, col[0].upper())
            cx += col_widths[idx]
        return current_y - head_h

    y = draw_header(y)
    pdf.setFont('Helvetica', 8)

    for row in rows:
        if y < 25 * mm:
            page_number += 1
            y = _new_page(pdf, width, height, page_number, titulo, subtitulo)
            y = draw_header(y)
            pdf.setFont('Helvetica', 8)

        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(COLOR_BORDER)
        pdf.rect(x, y - row_h, sum(col_widths), row_h, fill=1, stroke=1)

        cx = x
        for idx, col in enumerate(columns):
            key = col[1]
            max_chars = col[2]
            value = _fit_text(row.get(key, ''), max_chars)
            pdf.setFillColor(row.get(f'{key}_color', COLOR_TEXT))
            pdf.drawString(cx + 2 * mm, y - 5 * mm, str(value))
            cx += col_widths[idx]

        y -= row_h

    return y, page_number
