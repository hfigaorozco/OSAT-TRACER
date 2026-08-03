from django.db import models

# Create your models here.

class Reporte(models.Model):
    """Reporte de producción — de toda una orden (oblea=None) o de un lote
    específico (oblea=<pk>). El auto-generado al cerrar una orden sigue
    creándose exactamente igual que antes (_generar_reporte_orden); esto solo
    agrega la posibilidad de generarlo manualmente y a nivel de un solo lote."""
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField(auto_now=False, auto_now_add=True)
    hora = models.TimeField(auto_now=False, auto_now_add=True)
    unidades_apro = models.IntegerField()
    unidaes_defect = models.IntegerField()
    comentarios = models.TextField(default="Sin comentarios")
    orden = models.ForeignKey("api_produccion.Orden", on_delete=models.RESTRICT, related_name='reporte')
    oblea = models.ForeignKey(
        "api_produccion.Oblea", on_delete=models.RESTRICT, related_name='reporte',
        null=True, blank=True
    )
    tipo_generacion = models.CharField(
        max_length=6, choices=[('auto', 'Automático'), ('manual', 'Manual')], default='auto'
    )
    generado_por = models.ForeignKey(
        "api_usuarios.Empleado", on_delete=models.SET_NULL, related_name='reportes_generados',
        null=True, blank=True
    )

    class Meta:
        db_table = 'reporte'

    def __str__(self):
        return str(self.numero)


class ReporteInventario(models.Model):
    """Foto congelada de inventario (stock, movimientos, consumo) para un
    rango de fechas — se calcula UNA VEZ al generar y se guarda en snapshot,
    para que verlo/imprimirlo después muestre siempre lo mismo que se generó
    ese día, sin importar qué haya cambiado en el inventario desde entonces."""
    numero = models.AutoField(primary_key=True)
    fecha_generado = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    tipo_generacion = models.CharField(
        max_length=6, choices=[('auto', 'Automático'), ('manual', 'Manual')], default='manual'
    )
    generado_por = models.ForeignKey(
        "api_usuarios.Empleado", on_delete=models.SET_NULL, related_name='reportes_inventario',
        null=True, blank=True
    )
    snapshot = models.JSONField()

    class Meta:
        db_table = 'reporte_inventario'

    def __str__(self):
        return str(self.numero)


class ReporteKpi(models.Model):
    """Foto congelada del KPI por línea (mismo cálculo que el semáforo del
    dashboard, calcular_kpi_por_linea) para un rango de fechas.
    fecha_fin puede ser nula: significa "sin límite superior", igual que el
    semáforo en vivo del dashboard, para no dejar fuera lecturas recientes."""
    numero = models.AutoField(primary_key=True)
    fecha_generado = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    tipo_generacion = models.CharField(
        max_length=6, choices=[('auto', 'Automático'), ('manual', 'Manual')], default='manual'
    )
    generado_por = models.ForeignKey(
        "api_usuarios.Empleado", on_delete=models.SET_NULL, related_name='reportes_kpi',
        null=True, blank=True
    )
    snapshot = models.JSONField()

    class Meta:
        db_table = 'reporte_kpi'

    def __str__(self):
        return str(self.numero)


class ReporteMensual(models.Model):
    """Bundle de los 3 tipos de reporte para un mes completo. Producción no
    tiene un rango de fechas natural (es por orden/lote), así que su resumen
    mensual agrega todas las órdenes/lotes activos o cerrados ese mes —
    snapshot_produccion tiene una forma distinta a la de un Reporte normal.
    El UniqueConstraint es lo que permite la generación diferida: antes de
    generar, solo hay que preguntar si ya existe fila para ese (anio, mes)."""
    numero = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    mes = models.IntegerField()
    fecha_generado = models.DateTimeField(auto_now_add=True)
    tipo_generacion = models.CharField(
        max_length=6, choices=[('auto', 'Automático'), ('manual', 'Manual')], default='auto'
    )
    generado_por = models.ForeignKey(
        "api_usuarios.Empleado", on_delete=models.SET_NULL, related_name='reportes_mensuales',
        null=True, blank=True
    )
    snapshot_produccion = models.JSONField()
    snapshot_inventario = models.JSONField()
    snapshot_kpi = models.JSONField()

    class Meta:
        db_table = 'reporte_mensual'
        constraints = [
            models.UniqueConstraint(fields=['anio', 'mes'], name='uk_reporte_mensual_periodo')
        ]

    def __str__(self):
        return f"{self.mes:02d}/{self.anio}"
