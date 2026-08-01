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
            'stockActual',
            'imagen'
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


class CreateMovimientoInventarioSerializer(serializers.Serializer):
    pieza = serializers.PrimaryKeyRelatedField(queryset=models.Pieza.objects.all())
    tipo = serializers.ChoiceField(choices=models.MovimientoInventario.TIPOS)
    cantidad = serializers.IntegerField(required=False, min_value=0, default=0)
    cantidad_minima = serializers.IntegerField(required=False, min_value=0)
    usuario = serializers.CharField(required=False, allow_blank=True, max_length=80)
    comentario = serializers.CharField(required=False, allow_blank=True, max_length=160)


class ListMovimientoInventarioSerializer(serializers.ModelSerializer):
    pieza = serializers.CharField(source='pieza.codigo', read_only=True)
    piezaNombre = serializers.CharField(source='pieza.nombre', read_only=True)
    tipoLabel = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = models.MovimientoInventario
        fields = [
            'id',
            'pieza',
            'piezaNombre',
            'tipo',
            'tipoLabel',
            'cantidad',
            'stockAnterior',
            'stockPosterior',
            'stockMinimoAnterior',
            'stockMinimoPosterior',
            'fecha',
            'usuario',
            'comentario',
        ]
