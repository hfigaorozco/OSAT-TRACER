from io import BytesIO
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from api_reportes.pdf_utils import (
    COLOR_GREEN, COLOR_TURQUOISE, COLOR_GOLD, COLOR_RED,
    _draw_header, _draw_footer, _new_page, _draw_metric, _draw_section_title, _draw_table,
)
from .models import MovimientoInventario, Pieza


ESTADO_COLOR = {'ok': COLOR_GREEN, 'bajo': COLOR_GOLD, 'critico': COLOR_RED}
ESTADO_LABEL = {'ok': 'OK', 'bajo': 'Bajo minimo', 'critico': 'Critico'}


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
    """Devuelve la CLAVE de estado ('ok'/'bajo'/'critico'), no el color —
    así el resultado se puede guardar tal cual en un snapshot JSON."""
    if pieza.stockActual == 0:
        return 'critico'
    if pieza.stockActual <= pieza.stockMinimo:
        return 'bajo'
    return 'ok'


def computar_snapshot_inventario(fecha_inicio, fecha_fin):
    """Calcula todos los datos del reporte de inventario (métricas + las 3
    tablas) en un dict 100% serializable a JSON — es la foto que se guarda en
    ReporteInventario.snapshot y con la que se dibuja el PDF, tanto en el
    momento de generarlo como después, al volver a verlo/imprimirlo."""
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

    inventario_rows = []
    for pieza in piezas:
        estado_clave = _estado_pieza(pieza)
        inventario_rows.append({
            'codigo': pieza.codigo,
            'material': pieza.nombre,
            'minimo': pieza.stockMinimo,
            'actual': pieza.stockActual,
            'estado_clave': estado_clave,
            'estado': ESTADO_LABEL[estado_clave],
        })

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

    return {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'materiales': len(piezas),
        'bajo_minimo': len(bajo_minimo),
        'consumo_total': consumo_total,
        'movimientos_count': len(movimientos),
        'inventario_rows': inventario_rows,
        'consumo_rows': sorted(consumo_por_pieza.values(), key=lambda r: r['material']),
        'movimiento_rows': movimiento_rows,
    }


def dibujar_pdf_inventario(snapshot):
    """Dibuja el PDF a partir de un snapshot ya calculado (por
    computar_snapshot_inventario, en el momento o guardado previamente) —
    no vuelve a consultar la base de datos."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    titulo = 'Reporte de inventario'
    subtitulo = f'{snapshot.get("fecha_inicio") or "Inicio"} a {snapshot.get("fecha_fin") or "Actual"}'
    pdf.setTitle(f'{titulo} - {subtitulo}')
    page_number = 1
    y = _new_page(pdf, width, height, page_number, titulo, subtitulo)

    metric_w = (width - 40 * mm) / 4
    _draw_metric(pdf, 15 * mm, y - 23 * mm, metric_w, 'Materiales', snapshot['materiales'], COLOR_TURQUOISE)
    _draw_metric(pdf, 17 * mm + metric_w, y - 23 * mm, metric_w, 'Bajo minimo', snapshot['bajo_minimo'], COLOR_RED)
    _draw_metric(pdf, 19 * mm + metric_w * 2, y - 23 * mm, metric_w, 'Consumo total', snapshot['consumo_total'], COLOR_GOLD)
    _draw_metric(pdf, 21 * mm + metric_w * 3, y - 23 * mm, metric_w, 'Movimientos', snapshot['movimientos_count'], COLOR_GREEN)
    y -= 36 * mm

    inventario_rows = [
        {**r, 'estado_color': ESTADO_COLOR[r['estado_clave']]}
        for r in snapshot['inventario_rows']
    ]
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

    consumo_rows = snapshot['consumo_rows']
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

    movimiento_rows = snapshot['movimiento_rows']
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


def generar_pdf_reporte_inventario(fecha_inicio, fecha_fin):
    """Comportamiento sin cambios respecto a antes de este refactor — sigue
    aceptando (fecha_inicio, fecha_fin) y devolviendo el PDF, solo que ahora
    por dentro separa el cálculo de datos del dibujo, para poder reusar
    ambas mitades desde el nuevo modelo ReporteInventario."""
    snapshot = computar_snapshot_inventario(fecha_inicio, fecha_fin)
    return dibujar_pdf_inventario(snapshot)
