from django.db import models

# Create your models here.

class Reporte(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField(auto_now=True, auto_now_add=False)
    hora = models.TimeField(auto_now=True, auto_now_add=False)
    unidades_apro = models.IntegerField()
    unidaes_defect = models.IntegerField()
    comentarios = models.TextField(default="Sin comentarios")
    orden = models.ForeignKey("api_produccion.Orden", on_delete=models.RESTRICT, related_name='reporte')
    
    class Meta:
        db_table = 'reporte'
        
    def __str__(self):
        return self.numero