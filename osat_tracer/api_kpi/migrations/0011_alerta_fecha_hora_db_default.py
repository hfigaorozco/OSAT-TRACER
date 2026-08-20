from django.db import migrations, models
from django.db.models.functions import Now


class Migration(migrations.Migration):

    dependencies = [
        ('api_kpi', '0010_remove_historial_alertas_uk_historial_alertas_and_more'),
    ]

    # Alerta.fecha/hora se agregaron en la migración anterior con
    # auto_now_add=True — eso solo aplica el valor cuando el INSERT pasa
    # por el ORM de Django. Los triggers de MySQL ya existentes
    # (t_alerta_stock_critico, en orden) insertan en `alerta` con SQL
    # crudo sin esos campos, y como la columna no tenía un DEFAULT a nivel
    # de base de datos, cualquier INSERT disparado por el trigger fallaba
    # con "Field 'fecha' doesn't have a default value" — y como el trigger
    # corre dentro de la misma transacción que el INSERT en `orden`, el
    # error se veía como si fuera `orden` el que fallaba. No se toca el
    # trigger — se le da a la columna un default real a nivel de BD para
    # que cualquier INSERT que la omita (ORM o SQL crudo) siga funcionando.
    operations = [
        migrations.AlterField(
            model_name='alerta',
            name='fecha',
            field=models.DateField(auto_now_add=True, db_default=Now()),
        ),
        migrations.AlterField(
            model_name='alerta',
            name='hora',
            field=models.TimeField(auto_now_add=True, db_default=Now()),
        ),
    ]
