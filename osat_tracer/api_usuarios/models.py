from django.db import models

# Create your models here.
class Empleado(models.Model):
    numero = models.AutoField(primary_key=True)
    nombre = models.CharField(default=(""), max_length=40)
    primerApell = models.CharField(default=(""), max_length=40)
    seguApell = models.CharField(default=(""), max_length=40)
    rfc = models.CharField(default=(""), max_length=13)
    email = models.CharField(default=(""), max_length=50)
    fechaReg = models.DateField(auto_now=False, auto_now_add=True)
    estado = models.CharField(default=(""), max_length=5)
    rol = models.CharField(default=(""), max_length=5)    
    
    def __str__(self):
        return self.nombre
    
class Rol(models.Model):
    codigo = models.CharField(default="", max_length=5)
    descripcion = models.CharField(default="", max_length=20)
    
    def __str__(self):
        return self.descripcion

class Estado_Empleado(models.Model):
    codigo = models.CharField(default="", max_length=5)
    descripcion = models.CharField(default="", max_length=15)
    
    def __str__(self):
        return self.descripcion