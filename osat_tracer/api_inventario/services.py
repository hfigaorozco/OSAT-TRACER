from io import BytesIO
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .models import MovimientoInventario, Pieza


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


@transaction.atomic
def registrar_movimiento_inventario(
    pieza,
    tipo,
    cantidad=0,
    cantidad_minima=None,
    usuario='',
    comentario='',
):
    stock_anterior = pieza.stockActual
    minimo_anterior = pieza.stockMinimo
    cantidad = int(cantidad or 0)

    if tipo == MovimientoInventario.TIPO_ENTRADA:
        stock_posterior = stock_anterior + cantidad
        minimo_posterior = minimo_anterior
    elif tipo == MovimientoInventario.TIPO_SALIDA:
        stock_posterior = max(0, stock_anterior - cantidad)
        minimo_posterior = minimo_anterior
    elif tipo == MovimientoInventario.TIPO_AJUSTE:
        if cantidad_minima is None:
            raise ValueError('cantidad_minima es requerida para ajustes.')
        stock_posterior = stock_anterior
        minimo_posterior = int(cantidad_minima)
    else:
        raise ValueError('Tipo de movimiento no valido.')

    pieza.stockActual = stock_posterior
    pieza.stockMinimo = minimo_posterior
    pieza.save(update_fields=['stockActual', 'stockMinimo'])

    return MovimientoInventario.objects.create(
        pieza=pieza,
        tipo=tipo,
        cantidad=cantidad,
        stockAnterior=stock_anterior,
        stockPosterior=stock_posterior,
        stockMinimoAnterior=minimo_anterior,
        stockMinimoPosterior=minimo_posterior,
        usuario=usuario or '',
        comentario=comentario or '',
    )


def _parse_fecha(fecha):
    if not fecha:
        return None
    parsed = datetime.strptime(fecha, '%Y-%m-%d')
    return timezone.make_aware(parsed)


def _rango_fechas(fecha_inicio, fecha_fin):
    inicio = _parse_fecha(fecha_inicio)
    fin = _parse_fecha(fecha_fin)
    if fin:
        fin = fin + timedelta(days=1)
    return inicio, fin


def _filtrar_movimientos(fecha_inicio, fecha_fin):
    inicio, fin = _rango_fechas(fecha_inicio, fecha_fin)
    movimientos = MovimientoInventario.objects.select_related('pieza').all()
    if inicio:
        movimientos = movimientos.filter(fecha__gte=inicio)
    if fin:
        movimientos = movimientos.filter(fecha__lt=fin)
    return movimientos.order_by('fecha', 'id')


def _estado_pieza(pieza):
    if pieza.stockActual == 0:
        return 'Critico', COLOR_RED
    if pieza.stockActual <= pieza.stockMinimo:
        return 'Bajo minimo', COLOR_GOLD
    return 'OK', COLOR_GREEN


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


def generar_pdf_reporte_inventario(fecha_inicio, fecha_fin):
    piezas = list(Pieza.objects.all().order_by('nombre'))
    movimientos = list(_filtrar_movimientos(fecha_inicio, fecha_fin))
    bajo_minimo = [p for p in piezas if p.stockActual <= p.stockMinimo]
    salidas = [m for m in movimientos if m.tipo == MovimientoInventario.TIPO_SALIDA]
    consumo_total = sum(m.cantidad for m in salidas)

    consumo_por_pieza = {}
    for mov in salidas:
        item = consumo_por_pieza.setdefault(
            mov.pieza_id,
            {'codigo': mov.pieza_id, 'material': mov.pieza.nombre, 'consumo': 0},
        )
        item['consumo'] += mov.cantidad

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    titulo = 'Reporte de inventario'
    subtitulo = f'{fecha_inicio or "Inicio"} a {fecha_fin or "Actual"}'
    pdf.setTitle(f'{titulo} - {subtitulo}')
    page_number = 1
    y = _new_page(pdf, width, height, page_number, titulo, subtitulo)

    metric_w = (width - 40 * mm) / 4
    _draw_metric(pdf, 15 * mm, y - 23 * mm, metric_w, 'Materiales', len(piezas), COLOR_TURQUOISE)
    _draw_metric(pdf, 17 * mm + metric_w, y - 23 * mm, metric_w, 'Bajo minimo', len(bajo_minimo), COLOR_RED)
    _draw_metric(pdf, 19 * mm + metric_w * 2, y - 23 * mm, metric_w, 'Consumo total', consumo_total, COLOR_GOLD)
    _draw_metric(pdf, 21 * mm + metric_w * 3, y - 23 * mm, metric_w, 'Movimientos', len(movimientos), COLOR_GREEN)
    y -= 36 * mm

    inventario_rows = []
    for pieza in piezas:
        estado, color = _estado_pieza(pieza)
        inventario_rows.append({
            'codigo': pieza.codigo,
            'material': pieza.nombre,
            'minimo': pieza.stockMinimo,
            'actual': pieza.stockActual,
            'estado': estado,
            'estado_color': color,
        })

    _draw_section_title(pdf, 15 * mm, y, 'Stock actual')
    y -= 6 * mm
    y, page_number = _draw_table(
        pdf,
        inventario_rows,
        [('Codigo', 'codigo', 8), ('Material', 'material', 22), ('Minimo', 'minimo', 8),
         ('Actual', 'actual', 8), ('Estado', 'estado', 16)],
        15 * mm,
        y,
        [25 * mm, 65 * mm, 25 * mm, 25 * mm, 40 * mm],
        width,
        height,
        page_number,
        titulo,
        subtitulo,
    )
    y -= 10 * mm

    consumo_rows = sorted(consumo_por_pieza.values(), key=lambda r: r['material'])
    if y < 70 * mm:
        page_number += 1
        y = _new_page(pdf, width, height, page_number, titulo, subtitulo)
    _draw_section_title(pdf, 15 * mm, y, 'Consumo por material')
    y -= 6 * mm
    y, page_number = _draw_table(
        pdf,
        consumo_rows or [{'codigo': '-', 'material': 'Sin salidas en el periodo', 'consumo': 0}],
        [('Codigo', 'codigo', 8), ('Material', 'material', 45), ('Consumo', 'consumo', 12)],
        15 * mm,
        y,
        [30 * mm, 100 * mm, 35 * mm],
        width,
        height,
        page_number,
        titulo,
        subtitulo,
    )
    y -= 10 * mm

    movimiento_rows = []
    for mov in movimientos:
        movimiento_rows.append({
            'fecha': timezone.localtime(mov.fecha).strftime('%Y-%m-%d %H:%M'),
            'material': mov.pieza.nombre,
            'tipo': mov.get_tipo_display(),
            'cantidad': mov.cantidad,
            'antes': mov.stockAnterior,
            'despues': mov.stockPosterior,
        })

    if y < 70 * mm:
        page_number += 1
        y = _new_page(pdf, width, height, page_number, titulo, subtitulo)
    _draw_section_title(pdf, 15 * mm, y, 'Movimientos registrados')
    y -= 6 * mm
    _draw_table(
        pdf,
        movimiento_rows or [{
            'fecha': '-',
            'material': 'Sin movimientos en el periodo',
            'tipo': '-',
            'cantidad': 0,
            'antes': '-',
            'despues': '-',
        }],
        [('Fecha', 'fecha', 18), ('Material', 'material', 24), ('Tipo', 'tipo', 10),
         ('Cant.', 'cantidad', 8), ('Antes', 'antes', 8), ('Despues', 'despues', 8)],
        15 * mm,
        y,
        [35 * mm, 52 * mm, 26 * mm, 20 * mm, 20 * mm, 22 * mm],
        width,
        height,
        page_number,
        titulo,
        subtitulo,
    )

    pdf.save()
    buffer.seek(0)
    return buffer
