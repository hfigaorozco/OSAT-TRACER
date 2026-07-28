from io import BytesIO
from pathlib import Path

import qrcode

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import Oblea


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
