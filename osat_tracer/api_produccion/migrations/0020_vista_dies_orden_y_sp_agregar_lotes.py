from django.db import migrations


class Migration(migrations.Migration):
    """Agrega la vista v_cantDies_por_obleaDeOrden (requisito académico: usar
    una vista desde un procedimiento almacenado) y reescribe
    sp_agregar_lotesAorden para leer cantidadDies a través de ella en vez del
    JOIN directo que tenía.

    El SQL que dio el usuario para el procedimiento no traía WHERE en el
    SELECT sobre la vista — mismo bug que ya se había corregido en la
    versión anterior (migración 0019): sin filtrar por orden, MySQL toma una
    fila cualquiera de la vista. Se agrega 'WHERE v.numeroOrden = numeroOrden'.

    Ojo con el nombre: la vista expone una columna 'numeroOrden' y el
    parámetro de entrada del procedimiento también se llama 'numeroOrden' —
    si se compara sin calificar la columna, MySQL no sabe si es la columna o
    el parámetro (ambigüedad). Por eso la columna se referencia calificada
    como 'v.numeroOrden' (alias de la vista) y el parámetro se deja sin
    calificar.
    """

    dependencies = [
        ('api_produccion', '0019_stored_procedures'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP VIEW IF EXISTS v_cantDies_por_obleaDeOrden;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='''
CREATE VIEW v_cantDies_por_obleaDeOrden AS
SELECT o.numero AS numeroOrden, tob.cantidadDies AS cantidadDies
FROM orden AS o
INNER JOIN tipo_oblea AS tob ON o.tipoOblea_id = tob.codigo;
''',
            reverse_sql='DROP VIEW IF EXISTS v_cantDies_por_obleaDeOrden;'
        ),
        migrations.RunSQL(
            sql='DROP PROCEDURE IF EXISTS sp_agregar_lotesAorden;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='''
CREATE PROCEDURE sp_agregar_lotesAorden(
    IN numeroOrden INT,
    IN codigoQRvar VARCHAR(100)
)
BEGIN
    DECLARE diesIniciales INT;

    SELECT v.cantidadDies INTO diesIniciales
    FROM v_cantDies_por_obleaDeOrden AS v
    WHERE v.numeroOrden = numeroOrden;

    INSERT INTO oblea (diesGenerados, codigoQR, estado_id, orden_id)
    VALUES (diesIniciales, codigoQRvar, 'proce', numeroOrden);
END
''',
            reverse_sql='DROP PROCEDURE IF EXISTS sp_agregar_lotesAorden;'
        ),
    ]
