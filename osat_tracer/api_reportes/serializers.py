from rest_framework import serializers
from . import models

# SERIALIZERS Reporte (producción — de toda una orden o de un lote)
#CREATE
class CreateReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reporte
        fields = [
            "unidades_apro",
            "unidaes_defect",
            "comentarios",
            "orden",
            "oblea",
            "tipo_generacion",
            "generado_por",
        ]
#LIST
class ListReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reporte
        fields = [
            "numero",
            "fecha",
            "hora",
            "unidades_apro",
            "unidaes_defect",
            "comentarios",
            "orden",
            "oblea",
            "tipo_generacion",
            "generado_por",
        ]
#DETAIL
class DetailReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reporte
        fields = [
            "numero",
            "fecha",
            "hora",
            "unidades_apro",
            "unidaes_defect",
            "comentarios",
            "orden",
            "oblea",
            "tipo_generacion",
            "generado_por",
        ]
#UPDATE
class UpdateReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reporte
        fields = [
            "unidades_apro",
            "unidaes_defect",
            "comentarios",
        ]


# SERIALIZERS ReporteInventario
class CreateReporteInventarioSerializer(serializers.ModelSerializer):
    snapshot = serializers.JSONField(read_only=True)

    class Meta:
        model = models.ReporteInventario
        fields = ["fecha_inicio", "fecha_fin", "tipo_generacion", "generado_por", "snapshot"]


class ListReporteInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteInventario
        fields = [
            "numero", "fecha_generado", "fecha_inicio", "fecha_fin",
            "tipo_generacion", "generado_por", "snapshot",
        ]


class DetailReporteInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteInventario
        fields = [
            "numero", "fecha_generado", "fecha_inicio", "fecha_fin",
            "tipo_generacion", "generado_por", "snapshot",
        ]


# SERIALIZERS ReporteKpi
class CreateReporteKpiSerializer(serializers.ModelSerializer):
    snapshot = serializers.JSONField(read_only=True)

    class Meta:
        model = models.ReporteKpi
        fields = ["fecha_inicio", "fecha_fin", "tipo_generacion", "generado_por", "snapshot"]


class ListReporteKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteKpi
        fields = [
            "numero", "fecha_generado", "fecha_inicio", "fecha_fin",
            "tipo_generacion", "generado_por", "snapshot",
        ]


class DetailReporteKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteKpi
        fields = [
            "numero", "fecha_generado", "fecha_inicio", "fecha_fin",
            "tipo_generacion", "generado_por", "snapshot",
        ]


# SERIALIZERS ReporteMensual
class CreateReporteMensualSerializer(serializers.ModelSerializer):
    snapshot_produccion = serializers.JSONField(read_only=True)
    snapshot_inventario = serializers.JSONField(read_only=True)
    snapshot_kpi = serializers.JSONField(read_only=True)

    class Meta:
        model = models.ReporteMensual
        fields = [
            "anio", "mes", "tipo_generacion", "generado_por",
            "snapshot_produccion", "snapshot_inventario", "snapshot_kpi",
        ]


class ListReporteMensualSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteMensual
        fields = [
            "numero", "anio", "mes", "fecha_generado", "tipo_generacion", "generado_por",
            "snapshot_produccion", "snapshot_inventario", "snapshot_kpi",
        ]


class DetailReporteMensualSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteMensual
        fields = [
            "numero", "anio", "mes", "fecha_generado", "tipo_generacion", "generado_por",
            "snapshot_produccion", "snapshot_inventario", "snapshot_kpi",
        ]
