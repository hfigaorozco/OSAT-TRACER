from django.db import models

# Create your models here.

class Pieza(models.Model):
    codigo = models.CharField(default="ABCDE", max_length=5)
    nombre = models.CharField(default="Nombre de pieza", max_length=64)
    descripcion = models.CharField(default="Descripción", max_length=40)
    stockMinimo = models.IntegerField(default=0)
    stockActual = models.IntegerField(default=0)
    
    class Meta: 
        db_table = 'pieza'
    def __str__(self):
        return self.nombre