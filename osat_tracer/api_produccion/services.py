from io import BytesIO
from pathlib import Path

import qrcode

from django.conf import settings
from django.db.models import Sum
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from api_reportes.models import Reporte
from .models import Oblea, Orden, Paso_Realizado


COLOR_BG = colors.HexColor('#1C2433')
COLOR_GREEN = colors.HexColor('#16A85E')
COLOR_TEXT = colors.HexColor('#1A202C')
COLOR_MUTED = colors.HexColor('#718096')
COLOR_BORDER = colors.HexColor('#E2E8F0')
COLOR_LIGHT = colors.HexColor('#F7FAFC')


def generarQR(oblea):
    carpeta = Path(settings.MEDIA_ROOT) / "qr_obleas"
    carpeta.mkdir(parents=True, exist_ok=True)

    nombre_archivo = f"lote_{oblea.pk}.png"
    ruta_archivo = carpeta / nombre_archivo

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(str(oblea.pk))
    qr.make(fit=True)
    imagen = qr.make_image(fill_color="black", back_color="white")
    imagen.save(ruta_archivo)

    oblea.codigoQR = f"qr_obleas/{nombre_archivo}"
    oblea.save(update_fields=["codigoQR"])
    return ruta_archivo


def asegurar_qr(oblea):
    if not oblea.codigoQR or not (Path(settings.MEDIA_ROOT) / oblea.codigoQR).exists():
        generarQR(oblea)
    return oblea


def _draw_qr_header(pdf, page_width, page_height, id_orden, page_number):
    pdf.setFillColor(COLOR_BG)
    pdf.rect(0, page_height - 35 * mm, page_width, 35 * mm, fill=1, stroke=0)
    pdf.setFillColor(COLOR_GREEN)
    pdf.rect(0, page_height - 35 * mm, 5 * mm, 35 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(16 * mm, page_height - 16 * mm, "OSAT TRACER")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(16 * mm, page_height - 23 * mm, "Etiquetas QR de produccion")
    pdf.setFillColor(colors.HexColor('#C4C5D0'))
    pdf.drawRightString(page_width - 16 * mm, page_height - 16 * mm, f"Orden ORD-{int(id_orden):04d}")
    pdf.setStrokeColor(COLOR_BORDER)
    pdf.line(15 * mm, 13 * mm, page_width - 15 * mm, 13 * mm)
    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(page_width - 15 * mm, 8 * mm, f"Pagina {page_number}")


def generar_pdf_etiquetas_QR(id_orden):
    obleas = Oblea.objects.filter(orden_id=id_orden)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Etiquetas Orden #{id_orden}")
    page_width, page_height = A4
    page_number = 1

    _draw_qr_header(pdf, page_width, page_height, id_orden, page_number)
    x = 18 * mm
    y = page_height - 88 * mm
    card_w = 52 * mm
    card_h = 58 * mm
    gap_x = 8 * mm
    gap_y = 10 * mm

    for oblea in obleas:
        asegurar_qr(oblea)
        ruta = Path(settings.MEDIA_ROOT) / oblea.codigoQR
        imagen = ImageReader(str(ruta))

        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(COLOR_BORDER)
        pdf.roundRect(x, y - 25, card_w, card_h, 5, fill=1, stroke=1)
        pdf.setFillColor(COLOR_LIGHT)
        pdf.roundRect(x + 4 * mm, y+3 * mm, card_w - 8 * mm, 44 * mm, 3, fill=1, stroke=0)
        pdf.drawImage(
            imagen,
            x + 6 * mm,
            y + 5 * mm,
            width=40 * mm,
            height=40 * mm,
        )
        pdf.setFillColor(COLOR_TEXT)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(x + card_w / 2, y - 2 * mm, f"LOT-{oblea.numero:04d}")
        pdf.setFillColor(COLOR_MUTED)
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(x + card_w / 2, y -5 * mm, f"ID oblea: {oblea.pk}")

        x += card_w + gap_x

        if x + card_w > page_width - 15 * mm:
            x = 18 * mm
            y -= card_h + gap_y

        if y < 25 * mm:
            page_number += 1
            pdf.showPage()
            _draw_qr_header(pdf, page_width, page_height, id_orden, page_number)
            x = 18 * mm
            y = page_height - 88 * mm

    pdf.save()
    buffer.seek(0)
    return buffer


def generar_pdf_etiqueta_qr_lote(oblea):
    asegurar_qr(oblea)
    ruta = Path(settings.MEDIA_ROOT) / oblea.codigoQR
    imagen = ImageReader(str(ruta))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    _draw_qr_header(pdf, page_width, page_height, oblea.orden_id, 1)
    size = 80 * mm
    x = (page_width - size) / 2
    y = page_height - 125 * mm

    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(COLOR_BORDER)
    pdf.roundRect(x - 15 * mm, y - 30 * mm, size + 30 * mm, size + 45 * mm, 6, fill=1, stroke=1)
    pdf.drawImage(imagen, x, y, width=size, height=size)
    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(page_width / 2, y - 14 * mm, f"Lote LOT-{oblea.numero:04d}")
    pdf.setFillColor(COLOR_MUTED)
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(page_width / 2, y - 22 * mm, f"Orden ORD-{oblea.orden_id:04d}")

    pdf.save()
    buffer.seek(0)
    return buffer

def _draw_header(pdf, width, height, titulo, subtitulo):
    pdf.setFillColor(COLOR_BG)
    pdf.rect(0, height - 35 * mm, width, 35 * mm, fill=1, stroke=0)
    pdf.setFillColor(COLOR_GREEN)
    pdf.rect(0, height - 35 * mm, 5 * mm, 35 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(16 * mm, height - 16 * mm, 'OSAT TRACER')
    pdf.setFont('Helvetica', 12)
    pdf.drawString(16 * mm, height - 24 * mm, titulo)
    pdf.setFont('Helvetica-Bold', 12)
    pdf.setFillColor(colors.HexColor('#C4C5D0'))
    pdf.drawRightString(width - 16 * mm, height - 17 * mm, subtitulo)

def _draw_section(pdf, x, y, tag, contenido):

    # Etiqueta
    pdf.setFillColor(COLOR_GREEN)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x, y, tag)

    # Valor
    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(x + 42 * mm, y, str(contenido))

    # Línea divisoria
    pdf.setStrokeColor(colors.HexColor("#E2E8F0"))
    pdf.setLineWidth(0.5)
    pdf.line(x, y - 3 * mm, 190 * mm, y - 3 * mm)

def _draw_text_block(pdf, x, y, tag, contenido, max_chars=80):
    # Título
    pdf.setFillColor(COLOR_GREEN)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x, y, tag)
    pdf.setStrokeColor(colors.HexColor("#E2E8F0"))
    pdf.setLineWidth(0.5)
    pdf.line(x, y - 3 * mm, 190 * mm, y - 3 * mm)

    # Si viene una lista de comentarios
    if isinstance(contenido, (list, tuple)):
        comentarios = contenido if contenido else ["Sin comentarios."]
    else:
        comentarios = [str(contenido or "Sin comentarios.")]

    lineas = []

    for comentario in comentarios:
        # Agrega una viñeta a cada comentario
        if comentario == "Generado automáticamente al cerrar la orden.":
            break
        texto = f"• {comentario}"
        while texto:
            if len(texto) <= max_chars:
                lineas.append(texto)
                break
            corte = texto.rfind(" ", 0, max_chars)

            if corte == -1:
                corte = max_chars

            lineas.append(texto[:corte])

            # En las líneas siguientes agrega una pequeña sangría
            texto = "   " + texto[corte:].strip()

    alto = max(18 * mm, (len(lineas) * 6 + 8) * mm)

    # Caja
    pdf.setFillColor(colors.HexColor("#F8FAFC"))
    pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
    pdf.roundRect(
        x,
        y - alto - 5,
        170 * mm,
        alto,
        4,
        fill=1,
        stroke=1
    )

    # Texto
    pdf.setFillColor(COLOR_TEXT)
    pdf.setFont("Helvetica", 10)

    current_y = y - 7 * mm

    for linea in lineas:
        pdf.drawString(x + 5 * mm, current_y, linea)
        current_y -= 6 * mm
def generar_pdf_reporte_produccion(orden_id):
    try:
        orden = Orden.objects.select_related('proceso', 'empleado').get(numero=orden_id)
        obleas = Oblea.objects.filter(orden_id=orden_id)
        
        scrapTotal = 0
        inicialTotal = 0
        for oblea in obleas:
            num = oblea.numero
            scrapTotal += Paso_Realizado.objects.filter(oblea_id=num).aggregate(total = Sum("scrap"))["total"] or 0

    except Orden.DoesNotExist:
        raise ValueError('La orden solicitada no existe.')

    try:
        reportes = Reporte.objects.filter(orden=orden)
        comentarios = [
            r.comentarios
            for r in reportes
            if r.comentarios
        ]
        if not comentarios:
            comentarios = ["Sin comentarios."]
    except Reporte.DoesNotExist:
        raise ValueError('La orden aun no tiene un reporte de produccion.')

    dies_finales = Oblea.objects.filter(orden_id=orden_id).aggregate(total=Sum("diesGenerados"))["total"] or 0
    scrap = scrapTotal
    dies_iniciales = dies_finales + scrap
    yield_pct = round((dies_finales / dies_iniciales) * 100, 1) if dies_iniciales else 0
    fecha_orden = f"{orden.fecha:%Y-%m-%d} {orden.horaFin:%H:%M}"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    codigo_orden = f"ORD-{orden.numero:04d}"
    pdf.setTitle("Reporte de producción")
    _draw_header(pdf, width, height,"Reporte de producción", codigo_orden)
    _draw_section(pdf, 20 * mm, height - 55 * mm, "Proceso", orden.proceso.nombre)
    _draw_section(pdf, 20 * mm, height - 70 * mm, "Operador", str(orden.empleado))
    _draw_section(pdf, 20 * mm, height - 85 * mm, "Fecha", fecha_orden)
    _draw_section(pdf, 20 * mm, height - 100 * mm, "Dies iniciales", dies_iniciales)
    _draw_section(pdf, 20 * mm, height - 115 * mm, "Dies finales", dies_finales)
    _draw_section(pdf, 20 * mm, height - 130 * mm, "Scrap", scrap)
    _draw_section(pdf, 20 * mm, height - 145 * mm, "Yield", f"{yield_pct}%")
    _draw_text_block(pdf, 20 * mm, height - 165 * mm, "Comentarios", comentarios)
    
    pdf.save()
    buffer.seek(0)
    return buffer
