from django.db import models

# Create your models here.

class Semaforo(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(unique=True, max_length=10)
    
    class Meta:
        db_table = 'semaforo'
        
    def __str__(self):
        return self.descripcion
    

class EstadoAlerta(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(max_length=15, unique=True)
    
    class Meta:
        db_table = 'estado_alerta'
        
    def __str__(self):
        return self.codigo
    

class Kpi(models.Model):
    clave = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=20)
    descripcion = models.CharField(max_length=50)
    unidad = models.CharField(max_length=20, default='Porcentaje')
    umbralVerde = models.IntegerField(unique=True, default=1)
    umbralAmarillo = models.IntegerField(unique=True, default=2)
    umbralRojo = models.IntegerField(unique=True, default=3)
    
    class Meta:
        db_table = 'kpi'
        
    def __str__(self):
        return f"{self.clave} - {self.nombre}"
    

class Alerta(models.Model):
    numero = models.AutoField(primary_key=True)
    descripcion = models.CharField(unique=False, max_length=255)
    fecha = models.DateField(auto_now=False, auto_now_add=True)
    hora = models.TimeField(auto_now=False, auto_now_add=True)
    estadoAlerta = models.ForeignKey(EstadoAlerta, on_delete=models.RESTRICT, related_name='alerta')
    
    class Meta:
        db_table = 'alerta'
        
    def __str__(self):
        return self.descripcion


class Registro_Kpi(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField(auto_now=False, auto_now_add=True)
    hora = models.TimeField(auto_now=False, auto_now_add=True)
    valor = models.IntegerField()
    oblea = models.ForeignKey("api_produccion.Oblea", on_delete=models.RESTRICT, related_name='registro_kpi')
    kpi = models.ForeignKey(Kpi, on_delete=models.RESTRICT, related_name='registro_kpi')
    semaforo = models.ForeignKey(Semaforo, on_delete=models.RESTRICT, related_name='registro_kpi')
    alerta = models.ForeignKey(Alerta, on_delete=models.RESTRICT, related_name='registro_kpi')
    
    class Meta:
        db_table = 'registro_kpi'
        
    def __str__(self):
        return str(self.numero)