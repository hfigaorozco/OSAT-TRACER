from django.db import models

# Create your models here.

class Pieza(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(default="Pieza genérica", unique=True, max_length=20)
    descripcion = models.CharField(default="Descripción genérica", max_length=80)
    stockMinimo = models.IntegerField(default=0)
    stockActual = models.IntegerField(default=0)
    imagen = models.ImageField(upload_to='piezas/', null=True, blank=True)
    
    class Meta: 
        db_table = 'pieza'
        
    def __str__(self):
        return self.nombre 