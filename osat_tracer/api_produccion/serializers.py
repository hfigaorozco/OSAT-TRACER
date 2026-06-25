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
            "codigo",
            "descripcion",
            "imagen",
        ] 

#SERIALIZERS  Paso
#CREATE
class CreatePasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paso
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "tiempoEstimado",
        ] 
#LIST
class ListPasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paso
        fields = [
            "nombre",
            "descripcion",
            "tiempoEstimado",
        ] 
#DETAIL
class DetailPasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paso
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "tiempoEstimado",
        ] 
#UPDATE
class UpdatePasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paso
        fields = [
            "codigo",
            "descripcion",
            "tiempoEstimado",
        ] 

#SERIALIZERS  Orden
#CREATE
class CreateOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Orden
        fields = [
            "horaIni",
            "horaFin",
            "proceso",
            "estado",
            "empleado",
        ] 
#LIST
class ListOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Orden
        fields = [
            "numero",
            "horaIni",
            "horaFin",
            "fechaReg",
            "proceso",
            "estado",
        ] 
#DETAIL
class DetailOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Orden
        fields = [
            "numero",
            "horaIni",
            "horaFin",
            "fechaReg",
            "proceso",
            "estado",
            "empleado",
        ] 
                   
#UPDATE


#SERIALIZERS Oblea
#CREATE
class CreateObleaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Oblea
        fields = [
            "diesGenerados",
            "orden",
            "estado",
            "tipo",
        ]

#LIST
class ListObleaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Oblea
        fields = [
            "numero",
            "diesGenerados",
            "orden",
            "estado",
        ] 
#DETAIL
class DetailObleaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Oblea
        fields = [
            "numero",
            "diesGenerados",
            "orden",
            "estado",
            "tipo",
        ] 
#UPDATE

#SERIALIZERS  LineaProceso
#CREATE
class CreateLineaProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LineaProceso
        fields = [
           "linea",
           "proceso",  
        ] 
#LIST
class ListLineaProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LineaProceso
        fields = [
           "linea",
           "proceso",  
        ] 
#DETAIL
#UPDATE

#SERIALIZERS  PasoProceso
#CREATE
class CreatePasoProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PasoProceso
        fields = [
            "paso",
            "proceso",
            "orden",    
        ] 
#LIST
class ListPasoProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PasoProceso
        fields = [
            "paso",
            "proceso",
            "orden",    
        ] 
#DETAIL
class DetailPasoProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PasoProceso
        fields = [
            "paso",
            "proceso",
            "orden",    
        ] 
#UPDATE
class UpdatePasoProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PasoProceso
        fields = [
            "orden",    
        ] 
    


#SERIALIZERS  Proceso
#CREATE
class CreateProcesoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProcesoPieza
        fields = [
            "proceso",
            "pieza",
            "cantPiezas",   
        ] 
#LIST
class ListProcesoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProcesoPieza
        fields = [
            "proceso",
            "pieza",
            "cantPiezas",   
        ] 
#DETAIL
class DetailProcesoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProcesoPieza
        fields = [
            "proceso",
            "pieza",
            "cantPiezas",   
        ] 
#UPDATE
class UpdateProcesoPiezaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProcesoPieza
        fields = [
            "cantPiezas",   
        ] 



#SERIALIZERS  MaquinaPaso
#CREATE
class CreateMaquinaPasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MaquinaPaso
        fields = [
            "maquina",
            "paso",   
        ] 
#LIST
class ListMaquinaPasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MaquinaPaso
        fields = [
            "maquina",
            "paso",   
        ] 
#DETAIL
#UPDATE

#SERIALIZERS  PasoRealizado
#CREATE
class CreatePasoRealizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paso_Realizado
        fields = [
            "paso",
            "estado",
            "oblea",
            "alerta",  
        ] 
#LIST
class ListPasoRealizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Paso_Realizado
        fields = [
            "hora",
            "fecha",
            "paso",
            "estado",
            "oblea",
            "alerta",  
        ] 
#DETAIL
#UPDATE

#SERIALIZERS   HistorialDefecto
#CREATE
class CreateHistorialDefectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Historial_Defectos
        fields = [
            "defecto",
            "pasoRealizado",  
        ] 
#LIST
class ListHistorialDefectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Historial_Defectos
        fields = [
            "defecto",
            "pasoRealizado",  
        ] 
#DETAIL
#UPDATE Jiji

