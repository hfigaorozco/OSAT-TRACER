# Generated manually for inventory movement history.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_inventario', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MovimientoInventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('entrada', 'Entrada'), ('salida', 'Salida'), ('ajuste', 'Ajuste')], max_length=10)),
                ('cantidad', models.IntegerField(default=0)),
                ('stockAnterior', models.IntegerField(default=0)),
                ('stockPosterior', models.IntegerField(default=0)),
                ('stockMinimoAnterior', models.IntegerField(blank=True, null=True)),
                ('stockMinimoPosterior', models.IntegerField(blank=True, null=True)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.CharField(blank=True, default='', max_length=80)),
                ('comentario', models.CharField(blank=True, default='', max_length=160)),
                ('pieza', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='movimientos', to='api_inventario.pieza')),
            ],
            options={
                'db_table': 'movimiento_inventario',
                'ordering': ['-fecha', '-id'],
            },
        ),
    ]
