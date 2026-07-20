from django.db import models
from api_usuarios.models import Empleado

# Create your models here.
class Tipo_Maquina(models.Model):
    clave = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(default="", max_length=30)
    
    class Meta: 
        db_table = 'tipo_maquina'
        
    def __str__(self):
        return self.descripcion
    
    
class Estado_Maquina(models.Model):
    clave = models.CharField(primary_key=True, max_length=5)
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
    linea = models.ForeignKey('api_produccion.Linea', on_delete=models.CASCADE, related_name='maquina')
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'maquina'

    def __str__(self):
        return self.numSerie