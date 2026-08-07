# api_produccion/migrations/0018_estado_orden_recha.py

from django.db import migrations


def crear_estado_recha(apps, schema_editor):
    Estado_Orden = apps.get_model('api_produccion', 'Estado_Orden')
    Estado_Orden.objects.get_or_create(codigo='recha', defaults={'descripcion': 'Rechazada'})


def borrar_estado_recha(apps, schema_editor):
    Estado_Orden = apps.get_model('api_produccion', 'Estado_Orden')
    Estado_Orden.objects.filter(codigo='recha').delete()


class Migration(migrations.Migration):
    """Agrega el código 'recha' al catálogo Estado_Orden — mismo patrón que
    0016_estado_orden_enhol. Una orden en Hold ahora se puede rechazar
    explícitamente desde la UI (antes solo existía 'rechazado' como estado
    VISUAL derivado, calculado en _estado_orden_display cuando una orden
    'cerra' terminaba con todos sus lotes rechazados; esto agrega el código
    real para un rechazo explícito, manual, de una orden en Hold)."""

    dependencies = [
        ('api_produccion', '0017_alter_linea_options_alter_linea_nombre'),
    ]

    operations = [
        migrations.RunPython(crear_estado_recha, borrar_estado_recha),
    ]
