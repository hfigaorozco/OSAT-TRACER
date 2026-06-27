from rest_framework import serializers
from . import models

## SERIALIZERS semaforo
# CREATE
class CreateSemaforoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Semaforo
        fields = [
            'codigo',
            'descripcion'
        ]

# LIST
class ListSemaforoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Semaforo
        fields = [
            'codigo',
            'descripcion'
        ]

# DETAIL
class DetailSemaforoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Semaforo
        fields = [
            'codigo',
            'descripcion'
        ]


## SERIALIZERS estado_alerta
# CREATE
class CreateEstadoAlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoAlerta
        fields = [
            'codigo',
            'descripcion'
        ]

# LIST
class ListEstadoAlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoAlerta
        fields = [
            'codigo',
            'descripcion'
        ]

# DETAIL
class DetailEstadoAlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoAlerta
        fields = [
            'codigo',
            'descripcion'
        ]


## SERIALIZER kpi
# CREATE
class CreateKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Kpi
        fields = [
            'clave',
            'nombre',
            'descripcion',
            'unidad',
            'umbralVerde',
            'umbralAmarillo',
            'umbralRojo'
        ]

# LIST
class ListKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Kpi
        fields = [
            'nombre',
            'unidad',
            'umbralVerde',
            'umbralAmarillo',
            'umbralRojo'
        ]

# DETAIL
class DetailKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Kpi
        fields = '__all__'

# UPDATE
class UpdateKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Kpi
        fields = [
            'umbralVerde',
            'umbralAmarillo',
            'umbralRojo'
        ]


## SERIALIZER Alerta
# CREATE
class CreateAlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alerta
        fields = [
            'descripcion',
            'estadoAlerta'
        ]

# LIST
class ListAlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alerta
        fields = [
            'descripcion',
            'estadoAlerta'
        ]

# DETAIL
class DetailAlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alerta
        fields = [
            'numero',
            'descripcion',
            'estadoAlerta'
        ]

# UPDATE
class UpdateAlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alerta
        fields = [
            'estadoAlerta'
        ]


## SERIALIZER Registro_kpi
# CREATE
class CreateRegistroKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Registro_Kpi
        fields = [
            'codigo',
            'valor',
            'oblea',
            'kpi',
            'semaforo'
        ]

# LIST
class ListRegistroKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Registro_Kpi
        fields = [
            'fecha',
            'hora',
            'valor',
            'oblea',
            'kpi',
            'semaforo'
        ]

# DETAIL
class DetailRegistroKpiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Registro_Kpi
        fields = '__all__'


## SERIALIZER Historial_alertas
# CREATE
class CreateHistorialAlertasSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Historial_Alertas
        fields = [
            'registro_kpi',
            'alerta'
        ]

# LIST
class ListHistorialAlertasSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Historial_Alertas
        fields = '__all__'

# DETAIL
class DetailHistorialAlertasSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Historial_Alertas
        fields = '__all__'