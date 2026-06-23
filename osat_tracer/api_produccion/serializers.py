from rest_framework import serializers
from . import models

#SERIALIZERS defecto
#CREATE
class CreateDefectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Defecto
        fields = [
            "codigo",
            "descripcion"
        ]
#LIST
class ListDefectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Defecto
        fields = [
            "codigo",
            "descripcion"
        ]
#DETAIL
#UPDATE

#SERIALIZERS TipoOblea
#CREATE
class CreateTipoObleaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tipo_Oblea
        fields = [
            "codigo",
            "descripcion",
            "cantidadDies"
    ]
#LIST 
class ListTipoObleaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tipo_Oblea
        fields = [
            "codigo",
            "descripcion",
            "cantidadDies"
        ]
#DETAIL
#UPDATE

#SERIALIZERS EstadoPaso
#CREATE
class CreateEstadoPasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estado_Paso
        fields = [
            "codigo",
            "descripcion",
        ]
#LIST 
class ListEstadoPasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estado_Paso
        fields = [
            "codigo",
            "descripcion",
        ]
#DETAIL
#UPDATE

#SERIALIZERS  EstadoOrden
#CREATE
class CreateEstadoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estado_Orden
        fields = [
            "codigo",
            "descripcion",
        ]
#LIST
class ListEstadoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estado_Orden
        fields = [
            "codigo",
            "descripcion",
        ]
#DETAIL
#UPDATE

#SERIALIZERS  EstadoOblea
#CREATE
class CreateEstadoObleaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estado_Oblea
        fields = [
            "codigo",
            "descripcion",
        ]
#LIST
class ListEstadoObleaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estado_Oblea
        fields = [
            "codigo",
            "descripcion",
        ]
#DETAIL
#UPDATE

#SERIALIZERS  Linea
#CREATE
class CreateLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = [
            "codigo",
            "nombre",
        ]
#LIST
class ListLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = [
            "codigo",
            "nombre",
        ]
#DETAIL
class DetailLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = [
            "codigo",
            "nombre",
        ]
#UPDATE


#SERIALIZERS  proceso
#CREATE
class CreateProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proceso
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "imagen",
        ]
#LIST
class ListProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proceso
        fields = [
            "codigo",
            "nombre",
            "descripcion",
        ]
#DETAIL
class DetailProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proceso
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "imagen",
        ]
#UPDATE
class UpdateProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proceso
        fields = [
            "descripcion",
            "imagen",
        ] 

#SERIALIZERS  Paso
#CREATE
class CreatePasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proceso
        fields = [
            "descripcion",
            "imagen",
        ] 
#LIST
#DETAIL
#UPDATE


class PasoAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "nombre",
        "descripcion",
        "tiempoEstimado",
    ]  
    

class OrdenAdmin(admin.ModelAdmin):
    list_display= [
        "horaIni",
        "horaFin",
        "fechaReg",
        "proceso",
        "estado",
        "empleado",
    ]  


class ObleaAdmin(admin.ModelAdmin):
    list_display= [
        "diesGenerados",
        "orden",
        "estado",
        "tipo",        
    ]  
    

class LineaProcesoAdmin(admin.ModelAdmin):
    list_display= [
        "linea",
        "proceso",      
    ]  


class PasoProcesoAdmin(admin.ModelAdmin):
    list_display= [
        "paso",
        "proceso",
        "orden",      
    ]  


class ProcesoPiezaAdmin(admin.ModelAdmin):
    list_display= [
        "proceso",
        "pieza",
        "cantPiezas",      
    ]  


class MaquinaPasoAdmin(admin.ModelAdmin):
    list_display= [
        "maquina",
        "paso",    
    ]  


class PasoRealizadoAdmin(admin.ModelAdmin):
    list_display= [
        "hora",
        "fecha",
        "paso",
        "estado",
        "oblea",
        "alerta",    
    ]  
    

class HistorialDefectosAdmin(admin.ModelAdmin):
    list_display= [
        "defecto",
        "pasoRealizado",
    ]  
