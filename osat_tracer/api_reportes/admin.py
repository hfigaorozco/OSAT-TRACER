from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = [
        "unidades_apro",
        "unidaes_defect",
        "comentarios",
        "orden",
    ]
    