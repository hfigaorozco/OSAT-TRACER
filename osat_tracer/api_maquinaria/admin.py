from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.Maquina)
class MaquinaAdmin(admin.ModelAdmin):
    list_display = [
        "numSerie",
        "nombre",
        "tipoMaquina",
        "estado",
        "empleado",
        "linea",
    ]
    
@admin.register(models.Tipo_Maquina)
class TipoMaquinaAdmin(admin.ModelAdmin):
    list_display = [
        "clave",
        "descripcion",
    ]
    
@admin.register(models.Estado_Maquina)
class EstadoMaquinaAdmin(admin.ModelAdmin):
    list_display = [
        "clave",
        "descripcion",
    ]