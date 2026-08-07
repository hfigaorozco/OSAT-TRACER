from django.db import migrations


class Migration(migrations.Migration):
    """Agrega la vista v_requerimientos_de_un_proceso y los procedimientos
    sp_enlazarPasoAProceso / sp_asignarPiezaAPlantilla (SQL de un compañero,
    Héctor) para mover a la BD la validación de existencia y duplicado que
    hoy hace admin_organizacion_plantilla_paso_asignar / _pieza_asignar en
    Python (traen TODA la lista de PasoProceso/ProcesoPieza vía REST y la
    recorren en memoria — ver client/produccion/views.py). Con esta vista +
    SPs esa validación pasa a ser una sola consulta SQL, igual que ya se
    hizo con sp_agregar_lotesAorden y sp_calcularYieldLote.

    Adaptaciones sobre el SQL original para que compile y funcione con la
    lógica correcta:

    1. Se quitaron los bloques 'DELIMITER $$ ... DELIMITER ;': son una
       instrucción del cliente 'mysql' (CLI) para poder escribir ';' dentro
       del cuerpo del procedimiento sin que corte la sentencia antes de
       tiempo. Django ejecuta cada CREATE PROCEDURE como una sola sentencia
       vía cursor (RunSQL), así que no aplica — igual que en 0019/0020/0021.

    2. sp_asignarPiezaAPlantilla declaraba 'codigoPieza VARCHAR(50)', pero
       la columna real pieza.codigo es VARCHAR(5) (como todas las PK
       "codigo" de este proyecto — proceso.codigo, paso.codigo, etc.). Se
       corrigió a VARCHAR(5) para que el parámetro coincida con la columna
       que compara/inserta, igual que ya hacía el propio SP con
       codigoProceso y codigoPaso.

    3. La vista hace dos LEFT JOIN independientes desde proceso (uno hacia
       paso-proceso/paso, otro hacia proceso-pieza/pieza) sin encadenarlos
       entre sí, por lo que un proceso con N pasos y M piezas ligadas
       produce N×M filas (cruce, no una fila por requerimiento). Se dejó
       así porque no rompe ninguna de las dos validaciones que la usan:
       ambos SP solo hacen 'SELECT COUNT(*) ... WHERE Codigo_proceso = X
       AND Codigo_paso/Codigo_pieza = Y' para decidir si ya existe el
       enlace (count > 0) — ese resultado es invariante a que las filas
       estén multiplicadas por el cruce, solo cambia cuántas veces se repite
       la fila que sí matchea, no si matchea o no. No se reestructuró el
       JOIN para no apartarse del diseño que pidió el compañero ("vista
       única para ambos SP") sin necesidad real.

    Los nombres/columnas de las tablas puente (`paso-proceso`, con guion,
    columnas paso_id/proceso_id/orden; `proceso-pieza`, con guion, columnas
    proceso_id/pieza_id/cantPiezas) ya venían correctos en el SQL original,
    incluido el uso de comillas invertidas para los nombres con guion.
    """

    dependencies = [
        ('api_produccion', '0021_vista_yield_oblea_y_sp_calcular_yield'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP VIEW IF EXISTS v_requerimientos_de_un_proceso;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='''
CREATE VIEW v_requerimientos_de_un_proceso AS
SELECT
    p.codigo AS Codigo_proceso,
    p.nombre AS Proceso,
    pp.paso_id AS Codigo_paso,
    pa.nombre AS Paso,
    pp.orden AS Orden_paso,
    ppz.pieza_id AS Codigo_pieza,
    pz.nombre AS Pieza,
    ppz.cantPiezas AS Piezas_requeridas
FROM proceso AS p
LEFT JOIN `paso-proceso` AS pp ON pp.proceso_id = p.codigo
LEFT JOIN paso AS pa ON pp.paso_id = pa.codigo
LEFT JOIN `proceso-pieza` AS ppz ON ppz.proceso_id = p.codigo
LEFT JOIN pieza AS pz ON ppz.pieza_id = pz.codigo;
''',
            reverse_sql='DROP VIEW IF EXISTS v_requerimientos_de_un_proceso;'
        ),
        migrations.RunSQL(
            sql='DROP PROCEDURE IF EXISTS sp_enlazarPasoAProceso;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='''
CREATE PROCEDURE sp_enlazarPasoAProceso(
    IN codigoProceso VARCHAR(5),
    IN codigoPaso VARCHAR(5),
    IN ordenPaso INT
)
BEGIN
    DECLARE pasoExistente INT;
    DECLARE procesoExistente INT;
    DECLARE pasoEnlazadoAProceso INT;

    SELECT COUNT(*) INTO pasoExistente
    FROM paso
    WHERE codigo = codigoPaso;

    IF pasoExistente = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El paso no existe';
    END IF;

    SELECT COUNT(*) INTO procesoExistente
    FROM proceso
    WHERE codigo = codigoProceso;

    IF procesoExistente = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La plantilla no existe';
    END IF;

    SELECT COUNT(*) INTO pasoEnlazadoAProceso
    FROM v_requerimientos_de_un_proceso
    WHERE Codigo_proceso = codigoProceso AND Codigo_paso = codigoPaso;

    IF pasoEnlazadoAProceso > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ese paso ya está enlazado a esta plantilla';
    END IF;

    INSERT INTO `paso-proceso` (orden, paso_id, proceso_id)
    VALUES (ordenPaso, codigoPaso, codigoProceso);

END
''',
            reverse_sql='DROP PROCEDURE IF EXISTS sp_enlazarPasoAProceso;'
        ),
        migrations.RunSQL(
            sql='DROP PROCEDURE IF EXISTS sp_asignarPiezaAPlantilla;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='''
CREATE PROCEDURE sp_asignarPiezaAPlantilla(
    IN codigoProceso VARCHAR(5),
    IN codigoPieza VARCHAR(5),
    IN cantidadPiezas INT
)
BEGIN
    DECLARE procesoExistente INT;
    DECLARE piezaExistente INT;
    DECLARE piezaEnlazadaAProceso INT;

    SELECT COUNT(*) INTO procesoExistente
    FROM proceso
    WHERE codigo = codigoProceso;

    IF procesoExistente = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La plantilla no existe';
    END IF;

    SELECT COUNT(*) INTO piezaExistente
    FROM pieza
    WHERE codigo = codigoPieza;

    IF piezaExistente = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La pieza no existe';
    END IF;

    SELECT COUNT(*) INTO piezaEnlazadaAProceso
    FROM v_requerimientos_de_un_proceso
    WHERE Codigo_proceso = codigoProceso AND Codigo_pieza = codigoPieza;

    IF piezaEnlazadaAProceso > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Esa pieza ya está asignada a esta plantilla';
    END IF;

    IF cantidadPiezas IS NULL OR cantidadPiezas < 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cantidad debe ser mayor a 0';
    END IF;

    INSERT INTO `proceso-pieza` (proceso_id, pieza_id, cantPiezas)
    VALUES (codigoProceso, codigoPieza, cantidadPiezas);

END
''',
            reverse_sql='DROP PROCEDURE IF EXISTS sp_asignarPiezaAPlantilla;'
        ),
    ]
