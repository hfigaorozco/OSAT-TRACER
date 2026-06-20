from django.db import models
from api_usuarios.models import Empleado
from api_inventario.models import Pieza
from api_maquinaria.models import Maquina

# Create your models here.
class Tipo_Oblea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(max_length=25)
    cantidadDies = models.IntegerField(default=0, unique=True)


class Estado_Paso(models.Model):
    codigo = models.CharField(primary_key=True, default="", max_length=5)
    descripcion = models.CharField(default="Estado generico de paso", max_length=15)
    
    class Meta:
        db_table = 'estado_paso' 
        
    def __str__(self):
        return self.descripcion


class Estado_Orden(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(unique=True, max_length=10)
    
    class Meta:
        db_table = 'estado_orden'
    
    def __str__(self):
        return self.descripcion
    
    
class Estado_Oblea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(unique=True, max_length=15)
    
    class Meta:
        db_table = 'estado_oblea'
    
    def __str__(self):
        return self.descripcion
    
    
class Semaforo(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(unique=True, max_length=10)
    
    class Meta:
        db_table = 'semaforo'
        
    def __str__(self):
        return self.descripcion


class Linea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=20)
    
    class Meta:
        db_table = 'linea'
        
    def __str__(self):
        return self.nombre
    
    
class Proceso(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=20)
    descripcion = models.CharField(max_length=80)
    imagen = models.ImageField(upload_to='proceso/', null=True, blank=True)
    
    class Meta:
        db_table = 'proceso'
        
    def __str__(self):
        return self.nombre
    
    
class Paso(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=20)
    descripcion = models.CharField(max_length=80)
    tiempoEstimado = models.DurationField()
    
    class Meta:
        db_table = 'paso' 
    
    def __str__(self):
        return self.nombre 
  

class Orden(models.Model):
    numero = models.AutoField(primary_key=True)
    horaIni = models.DateTimeField(auto_now=False, auto_now_add=False)
    horaFin = models.DateTimeField(auto_now=False, auto_now_add=False)
    fechaReg = models.DateTimeField(auto_now=False, auto_now_add=True)
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE, related_name='orden')
    estado = models.ForeignKey(Estado_Orden, on_delete=models.CASCADE, related_name='orden')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='orden')

    class Meta:
        db_table = 'orden' 
    
    def __str__(self):
        return self.numero 


class Oblea(models.Model):
    numero = models.AutoField(primary_key=True)
    diesGenerados = models.IntegerField(default=(0))
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='oblea')
    estado = models.ForeignKey(Estado_Oblea, on_delete=models.CASCADE, related_name='oblea')
    tipo = models.ForeignKey(Tipo_Oblea, on_delete=models.CASCADE, related_name='oblea')

    class Meta:
        db_table = 'oblea' 
    
    def __str__(self):
        return self.numero 
    
    
class LineaProceso(models.Model):
    linea = models.ForeignKey(Linea, on_delete=models.CASCADE, related_name='linea_proceso')
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE, related_name='linea_proceso')

    class Meta:
        db_table = 'linea-proceso'
        constraints = [
            models.UniqueConstraint(
                fields=['linea', 'proceso'],
                name='uk_linea_proceso'
            )
        ]
        
    def __str__(self):
        return f"{self.linea} - {self.proceso}"

    
class PasoProceso(models.Model):
    paso = models.ForeignKey(Paso, on_delete=models.CASCADE, related_name='paso')
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE, related_name='paso')
    orden = models.IntegerField(default=(0))

    class Meta:
        db_table = 'paso-proceso'
        constraints = [
            models.UniqueConstraint(
                fields=['paso', 'proceso'],
                name='uk_paso_proceso'
            )
        ]
        
    def __str__(self):
        return f"{self.paso} - {self.proceso}"
    
    
class ProcesoPieza(models.Model):
    proceso = models.ForeignKey(Proceso, on_delete=models.CASCADE, related_name='proceso_pieza')
    pieza = models.ForeignKey(Pieza, on_delete=models.CASCADE, related_name='proceso_pieza')
    cantPiezas = models.IntegerField(default=(0))

    class Meta:
        db_table = 'proceso-pieza'
        constraints = [
            models.UniqueConstraint(
                fields=['proceso', 'pieza'],
                name='uk_proceso_pieza'
            )
        ] 
        
    def __str__(self):
        return f"{self.proceso} - {self.pieza}"
    
    
class MaquinaPaso(models.Model):
    maquina = models.ForeignKey(Maquina, on_delete=models.CASCADE, related_name='maquina_paso')
    paso = models.ForeignKey(Paso, on_delete=models.CASCADE, related_name='maquina_paso')

    class Meta:
        db_table = 'maquina-paso' 
        
    def __str__(self):
        return f"{self.maquina} - {self.paso}"
    

class Paso_Realizado(models.Model):
    numero = models.AutoField(primary_key=True)
    hora = models.TimeField(auto_now=False, auto_now_add=True)
    fecha = models.DateTimeField(auto_now=False, auto_now_add=True)
    paso = models.ForeignKey(Paso, on_delete=models.CASCADE, related_name='paso_realizado')
    estado = models.ForeignKey(Estado_Paso, on_delete=models.CASCADE, related_name='paso_realizado')
    oblea = models.ForeignKey(Oblea, on_delete=models.CASCADE, related_name='paso_realizado')
    #alerta = models.ForeignKey(Alerta, on_delete=models.CASCADE, related_name='paso_realizado') # Falta crear modelo de alerta

    class Meta:
        db_table = 'paso_realizado' 
        
    def __str__(self):
        return self.numero 