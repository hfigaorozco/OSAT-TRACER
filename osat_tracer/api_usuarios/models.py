from django.db import models
from django.contrib.auth.models import User


class Rol(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(unique=True, max_length=20, default="Rol genérico")

    class Meta:
        db_table = 'rol'

    def __str__(self):
        return self.descripcion


class Estado_Empleado(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(unique=True, max_length=15, default="Estado de empleado genérico")

    class Meta:
        db_table = 'estado_empleado'

    def __str__(self):
        return self.descripcion


class Empleado(models.Model):
    numero = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)
    primerApell = models.CharField(max_length=40)
    seguApell = models.CharField(max_length=40, blank=True, default='')
    rfc = models.CharField(max_length=13, unique=True)
    estado = models.ForeignKey(Estado_Empleado, on_delete=models.RESTRICT, related_name='empleados', default='act')
    rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, related_name='empleados')
    usuario = models.OneToOneField(User, on_delete=models.RESTRICT, related_name='empleado')

    class Meta:
        db_table = 'empleado'

    @property
    def email(self):
        return self.usuario.email

    def __str__(self):
        return f"{self.nombre} {self.primerApell} {self.seguApell}"    