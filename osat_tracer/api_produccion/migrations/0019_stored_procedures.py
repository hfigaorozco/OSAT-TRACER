from django.db import migrations


class Migration(migrations.Migration):
    """Procedimientos almacenados que reemplazan lógica que antes vivía en
    Python puro (client/produccion/views.py). Mismo estilo que las triggers
    de la migración 0015 (RunSQL sin DELIMITER — solo hace falta en el
    cliente `mysql`, no al ejecutar vía cursor.execute()).

    - sp_agregar_lotesAorden: dado por un compañero. Tenía un bug: el
      SELECT de cantidadDies no filtraba por numeroOrden (le faltaba el
      WHERE), así que MySQL tomaba una fila cualquiera de la tabla orden en
      vez de la orden real — se corrige agregando 'WHERE o.numero =
      numeroOrden'. Se llama una vez por lote a crear (el bucle vive en
      Python, en _crear_lotes_para_orden).

    - sp_calcularYieldLote: dado por un compañero, sin cambios — la lógica
      ya es correcta.

    - sp_lotestotalesXstock: nuevo, diseñado para esta tarea. Calcula
      cuántos lotes completos se pueden armar con el stock actual de
      inventario para un proceso y tipo de oblea dados: para cada pieza que
      requiere el proceso (tabla proceso-pieza), pieza_necesaria_por_lote =
      cantidadDies (del tipo de oblea) * cantPiezas (por proceso) — misma
      fórmula que ya usa el trigger t_alerta_stock_insuficiente (migración
      0015) para validar stock al crear una orden, no una inventada nueva.
      El máximo de lotes producibles es el mínimo de (stockActual / pieza
      necesaria por lote) entre todas las piezas requeridas — la pieza más
      escasa es la que limita cuántos lotes se pueden hacer.
    """

    dependencies = [
        ('api_produccion', '0018_estado_orden_recha'),
    ]

    operations = [
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

    SELECT tob.cantidadDies INTO diesIniciales
    FROM orden AS o
    INNER JOIN tipo_oblea AS tob ON o.tipoOblea_id = tob.codigo
    WHERE o.numero = numeroOrden;

    INSERT INTO oblea (diesGenerados, codigoQR, estado_id, orden_id)
    VALUES (diesIniciales, codigoQRvar, 'proce', numeroOrden);
END
''',
            reverse_sql='DROP PROCEDURE IF EXISTS sp_agregar_lotesAorden;'
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

    SELECT tio.cantidadDies, ob.diesGenerados
    INTO diesTotales, diesActivos
    FROM oblea AS ob
    INNER JOIN orden AS o ON ob.orden_id = o.numero
    INNER JOIN tipo_oblea AS tio ON o.tipoOblea_id = tio.codigo
    WHERE ob.numero = lote;

    IF diesTotales IS NOT NULL AND diesTotales > 0 THEN
        SET yield_pct = (diesActivos * 100.0) / diesTotales;
    ELSE
        SET yield_pct = 0;
    END IF;
END
''',
            reverse_sql='DROP PROCEDURE IF EXISTS sp_calcularYieldLote;'
        ),
        migrations.RunSQL(
            sql='DROP PROCEDURE IF EXISTS sp_lotestotalesXstock;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='''
CREATE PROCEDURE sp_lotestotalesXstock(
    IN procesoCod VARCHAR(5),
    IN tipoObleaCod VARCHAR(5),
    OUT lotesMax INT
)
BEGIN
    DECLARE diesPorLote INT DEFAULT 0;

    SELECT cantidadDies INTO diesPorLote
    FROM tipo_oblea
    WHERE codigo = tipoObleaCod;

    IF diesPorLote IS NULL OR diesPorLote <= 0 THEN
        SET lotesMax = 0;
    ELSE
        SELECT MIN(FLOOR(p.stockActual / (diesPorLote * pp.cantPiezas)))
        INTO lotesMax
        FROM `proceso-pieza` AS pp
        INNER JOIN pieza AS p ON p.codigo = pp.pieza_id
        WHERE pp.proceso_id = procesoCod
          AND pp.cantPiezas > 0;

        IF lotesMax IS NULL THEN
            SET lotesMax = 0;
        END IF;
    END IF;
END
''',
            reverse_sql='DROP PROCEDURE IF EXISTS sp_lotestotalesXstock;'
        ),
    ]
