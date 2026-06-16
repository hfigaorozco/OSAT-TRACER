from django.db import models

# Create your models here.
class Estado_Orden(models.Model):
    codigo = models.CharField(default="", max_length=5)
    descripcion = models.CharField(default="", max_length=10)
    
    def __str__(self):
        return self.descripcion
    
class Estado_Oblea(models.Model):
    codigo = models.CharField(default="", max_length=5)
    descripcion = models.CharField(default="", max_length=15)
    
    def __str__(self):
        return self.descripcion
    
class Estado_Oblea(models.Model):
    codigo = models.CharField(default="", max_length=5)
    descripcion = models.CharField(default="", max_length=25)
    cantidadDies = models.IntegerField(default=0)
    
    def __str__(self):
        return self.descripcion
    
class Semaforo(models.Model):
    codigo = models.CharField(default="", max_length=5)
    descripcion = models.CharField(default="", max_length=10)
    
    def __str__(self):
        return self.descripcion

class Linea(models.Model):
    codigo = models.CharField(default="", max_length=5)
    nombre = models.CharField(default="", max_length=20)
    
    def __str__(self):
        return self.nombre
    
class Proceso(models.Model):
    codigo = models.CharField(default="", max_length=5)
    nombre = models.CharField(default=(""), max_length=20)
    descripcion = models.CharField(default=(""), max_length=80)
    imagen = models.CharField(default=(""), max_length=100)
    
    def __str__(self):
        return self.nombre
    
class Paso(models.Model):
    codigo = models.CharField(default="", max_length=5)
    nombre = models.CharField(default=(""), max_length=20)
    descripcion = models.CharField(default=(""), max_length=80)
    tiempoEstimado = models.IntegerField(default=(0))
    
    def __str__(self):
        return self.nombre    

class Orden(models.Model):
    numero = models.AutoField(primary_key=True)
    horaIni = models.DateTimeField(_auto_now=False, auto_now_add=False)
    horaFin = models.DateTimeField(auto_now=False, auto_now_add=False)
    fechaReg = models.DateTimeField(auto_now=False, auto_now_add=True)
    proceso = models.CharField(default=(""), max_length=5)
    estado = models.CharField(default=(""), max_length=5)
    empleado = models.IntegerField(default=(0))

    
    def __str__(self):
        return self.numero 


class Oblea(models.Model):
    numero = models.AutoField(primary_key=True)
    diesGenerados = models.IntegerField(default=(0))
    orden = models.IntegerField(default=(0))
    estado = models.CharField(default=(""), max_length=5)
    tipo = models.CharField(default=(""), max_length=5)

    
    def __str__(self):
        return self.numero 
    
class LineaProceso(models.Model):
    num = models.AutoField(primary_key=True)
    linea = models.CharField(default=(""), max_length=5)
    proceso = models.CharField(default=(""), max_length=5)

    def __str__(self):
        return self.num 
    
    
class PasoProceso(models.Model):
    num = models.AutoField(primary_key=True)
    paso = models.CharField(default=(""), max_length=5)
    proceso = models.CharField(default=(""), max_length=5)
    orden = models.IntegerField(default=(0))

    def __str__(self):
        return self.num 
    
class ProcesoPieza(models.Model):
    num = models.AutoField(primary_key=True)
    proceso = models.CharField(default=(""), max_length=5)
    pieza = models.CharField(default=(""), max_length=5)
    cantPiezas = models.IntegerField(default=(0))

    def __str__(self):
        return self.num 
    
class MaquinaPaso(models.Model):
    num = models.AutoField(primary_key=True)
    maquina = models.CharField(default=(""), max_length=5)
    paso = models.CharField(default=(""), max_length=5)

    def __str__(self):
        return self.num 
    
    
    
class Paso_Realizado(models.Model):
    numero = models.AutoField(primary_key=True)
    hora = models.TimeField(_auto_now=False, auto_now_add=True)
    fecha = models.DateTimeField(auto_now=False, auto_now_add=True)
    paso = models.CharField(default=(""), max_length=5)
    estado = models.CharField(default=(""), max_length=5)
    oblea = models.IntegerField(default=(0))
    alerta = models.CharField(default=(""), max_length=5)

    
    def __str__(self):
        return self.numero 
