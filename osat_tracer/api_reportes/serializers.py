from rest_framework import serializers
from . import models

# SERIALIZERS Reporte
#CREATE
class CreateReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reporte
        fields = [
            "unidades_apro",
            "unidaes_defect",
            "comentarios",
            "orden",
        ]
#LIST
class ListReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reporte
        fields = [
            "numero",
            "unidades_apro",
            "unidaes_defect",
            "comentarios",
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