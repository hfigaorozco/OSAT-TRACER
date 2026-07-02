from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.Semaforo)
class SemaforoAdmin(admin.ModelAdmin):
    list_display = [
        "codigo",
        "descripcion"
    ]
    
@admin.register(models.EstadoAlerta)
class EstadoAlertaAdmin(admin.ModelAdmin):
    list_display = [
        "codigo",
        "descripcion"
    ]
    
@admin.register(models.Kpi)
class KpiAdmin(admin.ModelAdmin):
    list_display = [
        "clave",
        "nombre",
        "descripcion",
        "unidad",
        "umbralVerde",
        "umbralAmarillo",
        "umbralRojo"
    ]
    
@admin.register(models.Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = [
        "numero",
        "descripcion",
        "estadoAlerta"
    ]
    
@admin.register(models.Registro_Kpi)
class RegistroKpiAdmin(admin.ModelAdmin):
    list_display = [
        "numero", 
        "fecha", 
        "hora", 
        "valor",
        "oblea", 
        "kpi", 
        "semaforo" 
    ]
    
    
@admin.register(models.Historial_Alertas)
class HistorialAlertasAdmin(admin.ModelAdmin):
    list_display = [
        "registroKPI",
        "alerta",
        "fecha",
        "hora"
    ]