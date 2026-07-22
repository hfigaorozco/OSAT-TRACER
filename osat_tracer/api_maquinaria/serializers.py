from rest_framework import serializers
from . import models

# SERIALIZERS maquina
#CREATE
class CreateMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = [
            "numSerie",
            "nombre",
            "tipoMaquina",
            "estado",
            "empleado",
            "linea",
        ]
        
#LIST
class ListMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = [
            "numSerie",
            "nombre",
            "fechaReg",
            "tipoMaquina",
            "estado",
            "empleado",
            "linea",
        ]
        
#DETAIL
class DetailMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = [
            "numSerie",
            "nombre",
            "fechaReg",
            "tipoMaquina",
            "estado",
            "empleado",
            "linea",
        ]
        
#UPDATE
class UpdateMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Maquina
        fields = [
            "nombre",
            "estado",
            "empleado",
            "linea",
        ]
        
           
# SERIALIZERS estado_maquina
#CREATE
class CreateEstadoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estado_Maquina
        fields = [
            "codigo",
            "descripcion",
        ]
#LIST
class ListEstadoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estado_Maquina
        fields = [
            "codigo",
            "descripcion",
        ]
#DETAIL
#UPDATE


# SERIALIZERS tipo_maquina
#CREATE
class CreateTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tipo_Maquina
        fields = [
            "codigo",
            "descripcion",
        ]
#LIST
class ListTipoMaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tipo_Maquina
        fields = [
            "codigo",
            "descripcion",
        ]
#DETAIL
#UPDATE
