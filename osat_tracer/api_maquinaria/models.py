from django.db import models
from api_usuarios.models import Empleado

# Create your models here.
class Tipo_Maquina(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(default="", max_length=30)
    
    class Meta: 
        db_table = 'tipo_maquina'
        
    def __str__(self):
        return self.descripcion
    
    
class Estado_Maquina(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(default="Estado genérico", unique=True, max_length=15)
    
    class Meta: 
        db_table = 'estado_maquina'
        
    def __str__(self):
        return self.descripcion
    

class Maquina(models.Model):
    numSerie = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(default="Máquina genérica", unique=True, max_length=30)
    fechaReg = models.DateField(auto_now=False, auto_now_add=True)
    tipoMaquina = models.ForeignKey(Tipo_Maquina, on_delete=models.CASCADE, related_name='maquina')
    estado = models.ForeignKey(Estado_Maquina, on_delete=models.CASCADE, related_name='maquina')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='maquina')
    # Ya no se elige a mano en el form de crear/editar máquina — la línea de
    # una máquina se deriva de a qué Pasos está ligada (MaquinaPaso -> Paso ->
    # PasoProceso -> Proceso -> LineaProceso -> Linea), ver
    # client/produccion/views.py::_lineas_por_maquina. Se deja el campo
    # nullable (no se borra la columna) para no perder los datos históricos
    # que sí se capturaron a mano antes de este cambio.
    linea = models.ForeignKey('api_produccion.Linea', on_delete=models.SET_NULL, related_name='maquina', null=True, blank=True)

    class Meta:
        db_table = 'maquina'

    def __str__(self):
        return self.numSerie