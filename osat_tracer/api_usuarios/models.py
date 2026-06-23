from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Rol(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(default="Rol genérico", unique=True, max_length=20)
    
    class Meta:
        db_table = 'rol'
    
    def __str__(self):
        return self.descripcion


class Estado_Empleado(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(default="Estado de empleado genérico", unique=True, max_length=15)
    
    class Meta:
        db_table = 'estado_empleado'
    
    def __str__(self):
        return self.descripcion
    

class Empleado(models.Model):
    numero = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)
    primerApell = models.CharField(max_length=40)
    seguApell = models.CharField(max_length=40)
    rfc = models.CharField(unique=True, max_length=13)
    email = models.EmailField(unique=True, max_length=50)
    fechaReg = models.DateField(auto_now_add=True)
    estado = models.ForeignKey(Estado_Empleado, on_delete=models.RESTRICT, related_name='empleado')
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, related_name='empleado')
    usuario = models.OneToOneField(User, on_delete=models.RESTRICT, related_name='empleado')

    class Meta:
        db_table = 'empleado'

    def __str__(self):
        return f"{self.nombre} {self.primerApell}"