from django.db import migrations


class Migration(migrations.Migration):
    """Agrega la vista v_cantidadDies_diesTotales_oblea (requisito académico:
    usar una vista desde un procedimiento almacenado) y reescribe
    sp_calcularYieldLote para leer diesTotales/diesActivos a través de ella
    en vez del JOIN directo que tenía.

    El SQL que dio el usuario para el procedimiento no compilaba tal cual:
    consultaba la vista sin alias ('FROM v_cantidadDies_diesTotales_oblea')
    pero filtraba con 'WHERE ob.numero = lote' — 'ob' es el alias interno de
    la tabla oblea DENTRO de la definición de la vista, no algo visible desde
    afuera; una vista no expone los alias de las tablas que usa por dentro,
    solo sus columnas de salida (obleaIdentificador, cantidadDies,
    diesGenerados). Se corrige dándole alias a la vista ('AS v') y filtrando
    por su columna real: 'WHERE v.obleaIdentificador = lote'.

    El parámetro de salida se deja como 'yield_pct' (no 'yield', como lo
    escribió el usuario) por la misma razón que en la versión anterior de
    este procedimiento: evitar cualquier ambigüedad de parseo con la palabra
    reservada de MySQL — mismo comportamiento, solo un nombre más seguro.
    """

    dependencies = [
        ('api_produccion', '0020_vista_dies_orden_y_sp_agregar_lotes'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP VIEW IF EXISTS v_cantidadDies_diesTotales_oblea;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='''
CREATE VIEW v_cantidadDies_diesTotales_oblea AS
SELECT ob.numero AS obleaIdentificador, tio.cantidadDies AS cantidadDies, ob.diesGenerados AS diesGenerados
FROM oblea AS ob
INNER JOIN orden AS o ON ob.orden_id = o.numero
INNER JOIN tipo_oblea AS tio ON o.tipoOblea_id = tio.codigo;
''',
            reverse_sql='DROP VIEW IF EXISTS v_cantidadDies_diesTotales_oblea;'
        ),
        migrations.RunSQL(
            sql='DROP PROCEDURE IF EXISTS sp_calcularYieldLote;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='''
CREATE PROCEDURE sp_calcularYieldLote(
    IN lote INT,
    OUT yield_pct FLOAT
)
BEGIN
    DECLARE diesActivos INT DEFAULT 0;
    DECLARE diesTotales INT DEFAULT 0;

    SELECT v.cantidadDies, v.diesGenerados
    INTO diesTotales, diesActivos
    FROM v_cantidadDies_diesTotales_oblea AS v
    WHERE v.obleaIdentificador = lote;

    IF diesTotales IS NOT NULL AND diesTotales > 0 THEN
        SET yield_pct = (diesActivos * 100.0) / diesTotales;
    ELSE
        SET yield_pct = 0;
    END IF;
END
''',
            reverse_sql='DROP PROCEDURE IF EXISTS sp_calcularYieldLote;'
        ),
    ]
