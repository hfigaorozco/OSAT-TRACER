from django.db import migrations


def crear_estado_hold(apps, schema_editor):
    Estado_Oblea = apps.get_model('api_produccion', 'Estado_Oblea')
    Estado_Oblea.objects.get_or_create(codigo='enhol', defaults={'descripcion': 'En Hold'})


def eliminar_estado_hold(apps, schema_editor):
    Estado_Oblea = apps.get_model('api_produccion', 'Estado_Oblea')
    Estado_Oblea.objects.filter(codigo='enhol').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api_produccion', '0007_orden_linea_alter_historial_defectos_id_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_estado_hold, eliminar_estado_hold),
    ]
