from django.contrib import admin
from api_produccion import models
    
@admin.register(models.Defecto)
class DefectoAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "descripcion",
    ]
    
@admin.register(models.Tipo_Oblea)
class TipoObleaAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "descripcion",
        "cantidadDies"
    ]

@admin.register(models.Estado_Paso)
class EstadoPasoAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "descripcion",
    ]

@admin.register(models.Estado_Orden)
class EstadoOrdenAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "descripcion",
    ]

@admin.register(models.Estado_Oblea)
class EstadoObleaAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "descripcion",
    ] 
    
@admin.register(models.Linea)
class LineaAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "nombre",
    ] 
    
@admin.register(models.Proceso)
class ProcesoAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "nombre",
        "descripcion",
    ]

@admin.register(models.Paso)
class PasoAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "nombre",
        "descripcion",
        "tiempoEstimado",
    ]  
    
@admin.register(models.Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display= [
        "horaIni",
        "horaFin",
        "fecha",
        "tipoOblea",
        "proceso",
        "estado",
        "empleado",
    ]  

@admin.register(models.Oblea)
class ObleaAdmin(admin.ModelAdmin):
    list_display= [
        "diesGenerados",
        "orden",
        "estado",        
    ]  
    
@admin.register(models.LineaProceso)
class LineaProcesoAdmin(admin.ModelAdmin):
    list_display= [
        "linea",
        "proceso",      
    ]  

@admin.register(models.PasoProceso)
class PasoProcesoAdmin(admin.ModelAdmin):
    list_display= [
        "paso",
        "proceso",
        "orden",      
    ]  

@admin.register(models.ProcesoPieza)
class ProcesoPiezaAdmin(admin.ModelAdmin):
    list_display= [
        "proceso",
        "pieza",
        "cantPiezas",      
    ]  

@admin.register(models.MaquinaPaso)
class MaquinaPasoAdmin(admin.ModelAdmin):
    list_display= [
        "maquina",
        "paso",    
    ]  

@admin.register(models.Paso_Realizado)
class PasoRealizadoAdmin(admin.ModelAdmin):
    list_display= [
        "hora",
        "fecha",
        "observaciones",
        "paso",
        "estado",
        "oblea",
        "alerta",    
    ]  
    
@admin.register(models.Historial_Defectos)
class HistorialDefectosAdmin(admin.ModelAdmin):
    list_display= [
        "defecto",
        "pasoRealizado",
    ] 