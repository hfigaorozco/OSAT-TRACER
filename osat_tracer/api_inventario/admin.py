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


@admin.register(models.MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'pieza',
        'tipo',
        'cantidad',
        'stockAnterior',
        'stockPosterior',
        'fecha',
        'usuario',
    ]
    list_filter = ['tipo', 'fecha']
    search_fields = ['pieza__codigo', 'pieza__nombre', 'usuario', 'comentario']
