from django.contrib import admin
from . import models

# Register your models here.
@admin.register(models.Pieza)
class PiezaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo',
        'nombre',
        'descripcion',
        'stockMinimo',
        'stockActual',
        'imagen'
    ]