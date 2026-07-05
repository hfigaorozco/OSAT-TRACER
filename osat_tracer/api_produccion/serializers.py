from rest_framework import serializers
from . import models
from api_kpi.models import Alerta

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
class UpdateLineaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Linea
        fields = [
            'nombre',
    
        ]


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
            "fecha",
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
            "fecha",
            "horaIni",
            "horaFin",
            "proceso",
            "estado",
        ] 
#DETAIL
class DetailOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Orden
        fields = [
            "numero",
            "fecha",
            "horaIni",
            "horaFin",
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
            "proceso",
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
            "proceso",
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
    defectos = serializers.ListField(
        child=serializers.DictField(), required=False, write_only=True
    )
    unidades_defecto = serializers.IntegerField(required=False, write_only=True, default=0)
    observaciones = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, write_only=True
    )

    class Meta:
        model = models.Paso_Realizado
        fields = [
            "paso",
            "estado",
            "oblea",
            "alerta",
            "defectos",
            "unidades_defecto",
            "observaciones",
        ]
        extra_kwargs = {
            'alerta': {'required': False},
        }

    def create(self, validated_data):
        defectos_data = validated_data.pop('defectos', [])
        unidades_defecto = validated_data.pop('unidades_defecto', 0)
        observaciones = validated_data.pop('observaciones', None)

        # Si no se manda alerta y el resultado es Hold/Rechazado, crear una
        if 'alerta' not in validated_data or validated_data.get('alerta') is None:
            from api_kpi.models import Alerta, EstadoAlerta
            estado_str = str(validated_data.get('estado', '')).lower()
            if 'hold' in estado_str or 'rechaz' in estado_str:
                try:
                    estado_activo = EstadoAlerta.objects.get(descripcion__iexact='activo')
                except EstadoAlerta.DoesNotExist:
                    estado_activo = EstadoAlerta.objects.first()
                alerta = Alerta.objects.create(
                    descripcion=f'Etapa marcada como {validated_data.get("estado")} '
                                f'con {unidades_defecto} unidades con defecto',
                    estadoAlerta=estado_activo,
                )
                validated_data['alerta'] = alerta
            else:
                # Alerta es FK requerida en el modelo actual — usar una "sin novedad"
                from api_kpi.models import Alerta, EstadoAlerta
                try:
                    estado_resuelto = EstadoAlerta.objects.get(descripcion__iexact='resuelto')
                except EstadoAlerta.DoesNotExist:
                    estado_resuelto = EstadoAlerta.objects.first()
                alerta, _ = Alerta.objects.get_or_create(
                    descripcion='Sin novedad',
                    defaults={'estadoAlerta': estado_resuelto},
                )
                validated_data['alerta'] = alerta

        paso_realizado = models.Paso_Realizado.objects.create(**validated_data)

        # Guardar cada defecto en Historial_Defectos
        for d in defectos_data:
            codigo_defecto = d.get('defecto')
            if not codigo_defecto:
                continue
            try:
                defecto_obj = models.Defecto.objects.get(pk=codigo_defecto)
                models.Historial_Defectos.objects.create(
                    defecto=defecto_obj,
                    pasoRealizado=paso_realizado,
                )
            except models.Defecto.DoesNotExist:
                continue

        return paso_realizado

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



##Seguimiento Paso a Paso App Movil
class DetailObleaConEtapasSerializer(serializers.ModelSerializer):
    """
    Serializer especial para la app móvil (PasoProceso + Paso_Realizado) en un solo response.
    """
    etapas = serializers.SerializerMethodField()
    orden_numero = serializers.SerializerMethodField()

    class Meta:
        model = models.Oblea
        fields = [
            "numero",
            "diesGenerados",
            "orden",
            "orden_numero",
            "estado",
            "tipo",
            "etapas",
        ]

    def get_orden_numero(self, obj):
        return obj.orden.numero if obj.orden else None

    def get_etapas(self, obj):
        if not obj.orden or not obj.orden.proceso:
            return []

        pasos_proceso = models.PasoProceso.objects.filter(
            proceso=obj.orden.proceso
        ).select_related('paso').order_by('orden')

        etapas = []
        for pp in pasos_proceso:
            paso_realizado = models.Paso_Realizado.objects.filter(
                oblea=obj, paso=pp.paso
            ).select_related('estado').order_by('-numero').first()

            if paso_realizado:
                estado_desc = paso_realizado.estado.descripcion if paso_realizado.estado else 'pendiente'
                etapas.append({
                    'codigo': pp.paso.codigo,
                    'nombre': pp.paso.nombre,
                    'estado': estado_desc,
                    'operador': None,  # ajustar cuando el back tenga FK a empleado en paso_realizado
                    'maquina': None,   # ajustar cuando se agregue FK a maquina en paso_realizado
                    'hora_inicio': str(paso_realizado.hora) if paso_realizado.hora else None,
                    'hora_fin': None,
                    'unidades_defecto': 0,
                    'observaciones': None,
                })
            else:
                etapas.append({
                    'codigo': pp.paso.codigo,
                    'nombre': pp.paso.nombre,
                    'estado': 'pendiente',
                    'operador': None,
                    'maquina': None,
                    'hora_inicio': None,
                    'hora_fin': None,
                    'unidades_defecto': 0,
                    'observaciones': None,
                })

        # Marcar la primera etapa pendiente como "en_curso"
        for e in etapas:
            if e['estado'] == 'pendiente':
                e['estado'] = 'en_curso'
                break

        return etapas


##Update que acepta hold_motivo
class UpdateObleaSerializer(serializers.ModelSerializer):
    hold_motivo = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = models.Oblea
        fields = [
            "estado",
            "hold_motivo",
        ]

    def update(self, instance, validated_data):
        hold_motivo = validated_data.pop('hold_motivo', None)
        instance.estado = validated_data.get('estado', instance.estado)
        instance.save()

        # Si se manda hold_motivo, registrar una alerta automática
        if hold_motivo:
            from api_kpi.models import Alerta, EstadoAlerta
            try:
                estado_activo = EstadoAlerta.objects.get(descripcion__iexact='activo')
            except EstadoAlerta.DoesNotExist:
                estado_activo = EstadoAlerta.objects.first()

            if estado_activo:
                Alerta.objects.create(
                    descripcion=f'Lote LOT-{instance.numero:04d} puesto en Hold: {hold_motivo}',
                    estadoAlerta=estado_activo,
                )

        return instance
