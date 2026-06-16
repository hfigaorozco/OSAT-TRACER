from django.db import models

# Create your models here.
class Maquina(models.Model):
    numSerie = models.CharField(default="ABCDE", max_length=5)
    fechaReg = models.TimeField(auto_now=False, auto_now_add=True)
    tipoMaquina = models.CharField(default="", max_length=5)
    estado = models.CharField(default="", max_length=5)
    empleado = models.IntegerField(default=0)
    linea = models.CharField(default="", max_length=5)
    
    def __str__(self):
        return self.numSerie

class Tipo_Maquina(models.Model):
    clave = models.CharField(default="", max_length=5)
    descripcion = models.CharField(default="", max_length=30)
    
    def __str__(self):
        return self.descripcion
    
class Estado_Maquina(models.Model):
    clave = models.CharField(default="", max_length=5)
    descripcion = models.CharField(default="", max_length=15)
    
    def __str__(self):
        return self.descripcion