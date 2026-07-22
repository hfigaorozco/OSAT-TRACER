from io import BytesIO
from pathlib import Path

import qrcode

from django.conf import settings
from django.core.files import File

from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import Oblea

# Generar QR de una oblea y guardar la ruta de la imagen en la DD

def generarQR(oblea):
    # Crear la carpeta si no existe
    carpeta = Path(settings.MEDIA_ROOT) / "qr_obleas"
    carpeta.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo
    nombre_archivo = f"lote_{oblea.pk}.png"
    
    # Ruta completa donde se guardará
    ruta_archivo = carpeta / nombre_archivo

    # Crear QR
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )
    qr.add_data(str(oblea.pk))
    qr.make(fit=True)
    imagen = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    # Guardar imagen
    imagen.save(ruta_archivo)

    # Guardar la ruta relativa en la BD
    oblea.codigoQR = f"qr_obleas/{nombre_archivo}"
    oblea.save(update_fields=["codigoQR"])
    return ruta_archivo


def generar_pdf_etiquetas_QR(id_orden):
    obleas = Oblea.objects.filter(orden_id=id_orden)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    x = 20 * mm
    y = page_height - 60 * mm

    for oblea in obleas:
        ruta = Path(settings.MEDIA_ROOT) / oblea.codigoQR
        imagen = ImageReader(str(ruta))
        pdf.drawImage(
            imagen,
            x,
            y,
            width=40 * mm,
            height=40 * mm
        )
        pdf.drawString(
            x,
            y - 5 * mm,
            f"Lote {oblea.numero}"
        )

        x += 70 * mm

        if x > page_width - 60 * mm:
            x = 20 * mm
            y -= 60 * mm

        if y < 40 * mm:
            pdf.showPage()
            x = 20 * mm
            y = page_height - 60 * mm

    pdf.save()
    buffer.seek(0)
    return buffer
