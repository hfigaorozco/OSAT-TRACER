from django.db import models
from django.core.cache import cache

# Modelo para poder configurar el horario del sistema
class HorarioSistema(models.Model):
    hora_inicio = models.TimeField(default='07:00')
    hora_fin = models.TimeField(default='17:00')
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Horario del sistema"
        verbose_name_plural = "Horario del sistema"

    def __str__(self):
        return f"Horario: {self.hora_inicio} - {self.hora_fin}"

    def save(self, *args, **kwargs):
        self.pk = 1  # patron singleton: siempre el mismo registro
        super().save(*args, **kwargs)
        cache.delete('horario_sistema')

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj