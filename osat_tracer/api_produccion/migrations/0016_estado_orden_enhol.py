from django.db import migrations


def crear_estado_enhol(apps, schema_editor):
    Estado_Orden = apps.get_model('api_produccion', 'Estado_Orden')
    Estado_Orden.objects.get_or_create(codigo='enhol', defaults={'descripcion': 'En Hold'})


def borrar_estado_enhol(apps, schema_editor):
    Estado_Orden = apps.get_model('api_produccion', 'Estado_Orden')
    Estado_Orden.objects.filter(codigo='enhol').delete()


class Migration(migrations.Migration):
    """El trigger t_scrap_excedente_del_permitido (migración 0015) hace
    UPDATE orden SET estado_id = 'enhol', pero ese código solo existía en el
    catálogo de Estado_Oblea, no en Estado_Orden — sin esta fila, ese UPDATE
    viola la foreign key y tumba el INSERT de paso_realizado que lo dispara.
    Esto solo agrega el dato de catálogo que le falta; no toca el trigger."""

    dependencies = [
        ('api_produccion', '0015_auto_20260729_2039'),
    ]

    operations = [
        migrations.RunPython(crear_estado_enhol, borrar_estado_enhol),

        migrations.RemoveField(
            model_name='linea',
            name='proceso',
        ),
    ]
