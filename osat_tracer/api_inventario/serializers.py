from rest_framework import serializers
from . import models

# SERIALIZERS PIEZA

## Create Pieza Serializer
class CreatePiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pieza
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'stockMinimo',
            'stockActual',
            'imagen'
        ]
        
## Retrieve Pieza Serializer
### List Pieza Serializer
class ListPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pieza
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'stockMinimo',
            'stockActual'
        ]
        
### Detail Pieza Serializer
class DetailPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pieza
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'stockMinimo',
            'stockActual',
            'imagen'
        ]
        

### Update Pieza Serializer
class UpdatePiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pieza
        fields = [
            'nombre',
            'descripcion',
            'stockMinimo',
            'stockActual',
            'imagen'
        ]