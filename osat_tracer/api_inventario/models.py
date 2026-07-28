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


class MovimientoInventario(models.Model):
    TIPO_ENTRADA = 'entrada'
    TIPO_SALIDA = 'salida'
    TIPO_AJUSTE = 'ajuste'

    TIPOS = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SALIDA, 'Salida'),
        (TIPO_AJUSTE, 'Ajuste'),
    ]

    pieza = models.ForeignKey(Pieza, on_delete=models.RESTRICT, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.IntegerField(default=0)
    stockAnterior = models.IntegerField(default=0)
    stockPosterior = models.IntegerField(default=0)
    stockMinimoAnterior = models.IntegerField(null=True, blank=True)
    stockMinimoPosterior = models.IntegerField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=80, blank=True, default='')
    comentario = models.CharField(max_length=160, blank=True, default='')

    class Meta:
        db_table = 'movimiento_inventario'
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"{self.pieza_id} - {self.tipo} - {self.cantidad}"
