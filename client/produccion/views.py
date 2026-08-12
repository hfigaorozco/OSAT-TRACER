import json
import re
import uuid
from datetime import date, timedelta
from urllib.parse import urlencode
from django.db import connection
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
from home.views import _base_ctx, _get, _get_many, _post, _patch, _delete, _FakeObj, BACKEND_URL

PAGE_SIZE_ORGANIZACION = 7
PAGE_SIZE_PRODUCCION = 7

_CODIGO_RE = re.compile(r'^[a-z0-9-]+$')
_HORA_RE = re.compile(r'^\d{2}:\d{2}:\d{2}$')
_ESTADOS_ORDEN_VALIDOS = {'abier', 'proce', 'cerra'}

def _duracion_str(segundos):
    """Convierte segundos a un string que DurationField acepta (formato de str(timedelta))."""
    try:
        return str(timedelta(seconds=int(segundos or 0)))
    except (TypeError, ValueError):
        return '0:00:00'


_MENSAJE_ORDEN_CERRADA = 'Esta orden ya está cerrada — no se pueden hacer más cambios sobre ella ni sus lotes.'


def _orden_cerrada(orden_num):
    """Una orden en estado 'cerra' ya no admite más cambios sobre ella ni
    sobre sus lotes — se usa como guardia en todas las vistas mutadoras."""
    if not orden_num:
        return False
    orden = _get(f'/v1/detail/Orden/{orden_num}/') or {}
    return str(orden.get('estado', '')).lower() == 'cerra'


def _organizacion_redirect(tab=None, editar=None):
    url = reverse('admin_organizacion')
    if tab:
        url += f'?tab={tab}'
        if editar:
            url += f'&editar={editar}'
    return redirect(url)


# ── Helpers de negocio para Órdenes/Lotes ─────────────────────────────────────

ESTADOS_ORDEN_LABEL = {'abier': 'Abierta', 'proce': 'En proceso', 'cerra': 'Cerrada'}
ESTADOS_OBLEA_LABEL = {'proce': 'En proceso', 'termi': 'Terminada', 'recha': 'Rechazada', 'enhol': 'En Hold'}


def _fecha_display(iso_str):
    """Convierte una fecha/fechahora ISO a 'DD/MM/YYYY' para mostrar (el filtro |date de Django no formatea strings planos)."""
    partes = str(iso_str or '')[:10].split('-')
    if len(partes) == 3 and all(partes):
        return f'{partes[2]}/{partes[1]}/{partes[0]}'
    return '—'


def _hora_display(iso_str):
    """Extrae HH:MM:SS de un datetime ISO para mostrarlo como hora del día."""
    s = str(iso_str or '')
    if 'T' in s:
        parte_hora = s.split('T', 1)[1]
    elif ' ' in s:
        parte_hora = s.split(' ', 1)[1]
    else:
        return '—'
    return parte_hora[:8] if len(parte_hora) >= 5 else '—'


def _normalizar_hora(valor):
    """Asegura formato HH:MM:SS a partir de lo que entregue <input type='time'> (HH:MM o HH:MM:SS)."""
    valor = (valor or '').strip()
    if not valor:
        return None
    return valor if len(valor) > 5 else f'{valor}:00'


def _get_linea_proceso(linea_pk):
    """Devuelve el código de proceso asignado a una línea, o None.
    La relación real vive en la tabla puente LineaProceso — Linea.proceso
    (el campo directo del modelo) no se usa y siempre está en null."""
    relaciones = _get('/v1/list/LineaProceso/', [])
    rel = next((r for r in relaciones if str(r.get('linea')) == str(linea_pk)), None)
    return rel.get('proceso') if rel else None


def _asignar_proceso_a_linea(linea_pk, proceso_pk):
    """Asigna (o desasigna, si proceso_pk viene vacío) un proceso a una
    línea a través de la tabla puente LineaProceso real — nunca del campo
    muerto Linea.proceso. Antes de asignar valida que el proceso tenga al
    menos un paso y una pieza configurados, para que no se pueda apuntar
    una línea a un proceso a medio armar (eso rompía la creación de
    Órdenes más adelante sin ningún aviso claro de por qué).
    Devuelve (ok, error_o_None, proceso_nombre_o_None).
    """
    relaciones = _get('/v1/list/LineaProceso/', [])
    existente = next((r for r in relaciones if str(r.get('linea')) == str(linea_pk)), None)

    if not proceso_pk:
        if existente:
            ok, resp = _delete(f"/v1/delete/LineaProceso/{existente['id']}/")
            if not ok:
                return False, f'Error al quitar el proceso asignado: {resp}', None
        return True, None, None

    if existente and str(existente.get('proceso')) == str(proceso_pk):
        procesos_bd = _get('/v1/list/Proceso/', [])
        proceso = next((p for p in procesos_bd if str(p.get('codigo')) == str(proceso_pk)), {})
        return True, None, proceso.get('nombre', proceso_pk)

    procesos_bd = _get('/v1/list/Proceso/', [])
    proceso = next((p for p in procesos_bd if str(p.get('codigo')) == str(proceso_pk)), None)
    proceso_nombre = proceso.get('nombre', proceso_pk) if proceso else proceso_pk

    pasos_proceso = [p for p in _get('/v1/list/PasoProceso/', []) if str(p.get('proceso')) == str(proceso_pk)]
    piezas_proceso = [p for p in _get('/v1/list/ProcesoPieza/', []) if str(p.get('proceso')) == str(proceso_pk)]
    faltantes = []
    if not pasos_proceso:
        faltantes.append('pasos')
    if not piezas_proceso:
        faltantes.append('piezas')
    if faltantes:
        return False, (
            f'El proceso "{proceso_nombre}" no tiene {" ni ".join(faltantes)} configurado(s) — '
            f'complétalo en Organización antes de asignarlo a una línea.'
        ), None

    if existente:
        ok, resp = _delete(f"/v1/delete/LineaProceso/{existente['id']}/")
        if not ok:
            return False, f'Error al reasignar el proceso: {resp}', None

    ok, resp = _post('/v1/create/LineaProceso/', {'linea': linea_pk, 'proceso': proceso_pk})
    if not ok:
        return False, f'Error al asignar el proceso: {resp}', None
    return True, None, proceso_nombre


def _crear_lotes_para_orden(orden_pk, tipo_oblea_pk, cantidad):
    """Crea `cantidad` lotes/obleas para una orden llamando al procedimiento
    almacenado sp_agregar_lotesAorden una vez por lote (diesGenerados sale
    de TipoOblea.cantidadDies dentro del procedimiento — tipo_oblea_pk ya no
    se usa aquí, se deja en la firma para no tocar los 3 call sites).

    codigoQR es solo un valor único temporal: la imagen QR real (el PNG que
    se imprime/escanea) se genera después, la primera vez que alguien la
    pide, en api_produccion/services.py::asegurar_qr — esa función
    sobreescribe codigoQR con la ruta real basada en el número de lote ya
    asignado por MySQL (auto_increment), que no existe todavía en el
    momento de este INSERT. Este valor solo evita dejar el campo vacío."""
    if cantidad <= 0:
        return 0, []
    errores = []
    creados = 0
    with connection.cursor() as cursor:
        for _ in range(cantidad):
            qr_temporal = f'ORD{orden_pk}-{uuid.uuid4().hex[:12]}'
            try:
                cursor.callproc('sp_agregar_lotesAorden', [orden_pk, qr_temporal])
                creados += 1
            except Exception as e:
                errores.append(str(e))
    return creados, errores


def _mensaje_sp(e):
    """Extrae el texto de un SIGNAL SQLSTATE '45000' lanzado por un
    procedimiento almacenado (MySQLdb lo entrega como args=(1644, 'texto'))
    en vez de mostrarle al usuario la tupla de error cruda."""
    args = getattr(e, 'args', None)
    if args and len(args) > 1 and isinstance(args[1], str):
        return args[1]
    return str(e)


def _enlazar_paso_a_proceso(proceso_pk, paso_pk, orden):
    """Vincula un paso a una plantilla (proceso) vía sp_enlazarPasoAProceso
    — la existencia de paso/proceso y el duplicado ya no se validan en
    Python trayendo toda la lista de PasoProceso por REST, los valida el
    procedimiento almacenado directo contra la BD. Devuelve (ok, error)."""
    with connection.cursor() as cursor:
        try:
            cursor.callproc('sp_enlazarPasoAProceso', [proceso_pk, paso_pk, orden])
            return True, None
        except Exception as e:
            return False, _mensaje_sp(e)


def _asignar_pieza_a_plantilla(proceso_pk, pieza_pk, cantidad):
    """Asigna una pieza a una plantilla (proceso) vía sp_asignarPiezaAPlantilla
    — mismo reemplazo que _enlazar_paso_a_proceso pero para proceso-pieza."""
    with connection.cursor() as cursor:
        try:
            cursor.callproc('sp_asignarPiezaAPlantilla', [proceso_pk, pieza_pk, cantidad])
            return True, None
        except Exception as e:
            return False, _mensaje_sp(e)


def _lotes_max_por_stock(proceso_pk, tipo_oblea_pk):
    """Cuántos lotes completos se pueden armar con el stock actual de
    inventario para un proceso y tipo de oblea dados — vía el procedimiento
    almacenado sp_lotestotalesXstock. Se usa en el modal de Nueva Orden para
    avisar, antes de guardar, cuántos lotes alcanza a producir el stock
    disponible (la pieza más escasa entre las que requiere el proceso es la
    que limita el máximo)."""
    if not proceso_pk or not tipo_oblea_pk:
        return None
    with connection.cursor() as cursor:
        cursor.callproc('sp_lotestotalesXstock', [proceso_pk, tipo_oblea_pk, 0])
        cursor.execute('SELECT @_sp_lotestotalesXstock_2')
        row = cursor.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _descontar_stock_lotes(proceso_pk, tipo_oblea_pk, cantidad_lotes):
    """Descuenta del stock de piezas lo que consumen `cantidad_lotes` lotes
    de este proceso + tipo de oblea — misma fórmula que usa el trigger
    t_alerta_stock_insuficiente (cantidadDies del tipo de oblea x
    cantPiezas del proceso). Ese trigger solo corre UNA vez, al INSERT de
    la orden, y solo contempla su primer lote — nunca los adicionales que
    _crear_lotes_para_orden agrega después (ni al crear la orden con
    cantidad_lotes > 1, ni al agregar lotes a una orden ya existente, que
    ni siquiera pasan por un INSERT en la tabla orden). Sin este descuento
    el stock quedaba con lecturas infladas después de cualquier orden
    multi-lote, y sp_lotestotalesXstock empezaba a mentir."""
    if cantidad_lotes <= 0 or not proceso_pk or not tipo_oblea_pk:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE pieza p "
            "JOIN `proceso-pieza` pp ON p.codigo = pp.pieza_id "
            "JOIN tipo_oblea tob ON tob.codigo = %s "
            "SET p.stockActual = p.stockActual - (tob.cantidadDies * pp.cantPiezas * %s) "
            "WHERE pp.proceso_id = %s",
            [tipo_oblea_pk, cantidad_lotes, proceso_pk],
        )


def _piezas_insuficientes(proceso_pk, tipo_oblea_pk):
    """Identifica qué pieza(s) tienen stock insuficiente, con el mismo
    criterio que usa el trigger t_alerta_stock_insuficiente (stockActual de
    la pieza vs. cantidadDies del tipo de oblea × cantPiezas del proceso).

    OJO: la validación real que bloquea la creación de la orden la sigue
    haciendo el trigger (SIGNAL SQLSTATE '45000') — eso no se toca ni se
    duplica aquí. Esta función solo se llama DESPUÉS de que el trigger ya
    rechazó la orden, únicamente para poder mostrar qué pieza fue y su
    imagen, ya que desde MySQL no se pudo concatenar el nombre de la pieza
    dentro del mensaje del trigger."""
    proceso_pieza_bd, piezas_bd, tipos_oblea_bd = _get_many(
        '/v1/list/ProcesoPieza/', '/v1/list/piezas/', '/v1/list/TipoOblea/'
    )
    tipo_data = next((t for t in tipos_oblea_bd if str(t.get('codigo')) == str(tipo_oblea_pk)), {})
    cantidad_dies = int(tipo_data.get('cantidadDies', 0) or 0)
    piezas_map = {str(p.get('codigo')): p for p in piezas_bd}

    faltantes = []
    for rel in proceso_pieza_bd:
        if str(rel.get('proceso')) != str(proceso_pk):
            continue
        pieza = piezas_map.get(str(rel.get('pieza')))
        if not pieza:
            continue
        necesario = cantidad_dies * int(rel.get('cantPiezas', 0) or 0)
        disponible = int(pieza.get('stockActual', 0) or 0)
        if disponible < necesario:
            faltantes.append({
                'codigo': pieza.get('codigo'),
                'nombre': pieza.get('nombre', pieza.get('codigo')),
                'imagen': pieza.get('imagen'),
                'disponible': disponible,
                'necesario': necesario,
                'faltante': necesario - disponible,
            })
    return faltantes


def _crear_orden(request):
    linea_pk   = request.POST.get('linea', '').strip()
    tipo_oblea = request.POST.get('tipo_oblea', '').strip()
    empleado_pk = request.session.get('user_id')
    cantidad_raw = request.POST.get('cantidad_lotes', '').strip()
    hora_inicio = _normalizar_hora(request.POST.get('hora_inicio', ''))
    hora_fin    = _normalizar_hora(request.POST.get('hora_fin', ''))

    if not linea_pk or not tipo_oblea:
        messages.error(request, 'Selecciona línea y tipo de oblea.')
        return
    if not hora_inicio or not hora_fin:
        messages.error(request, 'Indica hora de inicio y hora de fin.')
        return
    if not _HORA_RE.match(hora_inicio) or not _HORA_RE.match(hora_fin):
        messages.error(request, 'Las horas indicadas no son válidas.')
        return
    if hora_inicio >= hora_fin:
        messages.error(request, 'La hora de inicio debe ser anterior a la hora de fin.')
        return
    if cantidad_raw and not cantidad_raw.isdigit():
        messages.error(request, 'La cantidad de lotes debe ser un número.')
        return
    cantidad_lotes = int(cantidad_raw or 0)
    proceso_pk = _get_linea_proceso(linea_pk)
    if not proceso_pk:
        messages.error(request, 'La línea seleccionada no tiene un proceso asignado.')
        return

    if cantidad_lotes > 0:
        lotes_max = _lotes_max_por_stock(proceso_pk, tipo_oblea)
        if lotes_max is not None and cantidad_lotes > lotes_max:
            messages.error(
                request,
                f'El stock actual solo alcanza para {lotes_max} lote(s) de este tipo de oblea — se pidieron {cantidad_lotes}.'
            )
            return

    hoy = date.today().isoformat()
    ok, resp = _post('/v1/create/Orden/', {
        'horaIni': f'{hoy} {hora_inicio}',
        'horaFin': f'{hoy} {hora_fin}',
        'proceso': proceso_pk,
        'linea': linea_pk,
        'tipoOblea': tipo_oblea,
        'estado': 'abier',
        'empleado': empleado_pk,
    })
    if not ok:
        # El trigger t_alerta_stock_insuficiente ya rechazó la orden (o
        # cualquier otro error de BD que CreateOrdenAPIView haya limpiado).
        # Si fue por stock, identificamos aquí la pieza exacta solo para
        # mostrarla bonita — el trigger es quien realmente bloqueó la orden.
        if 'stock insuficiente' in str(resp).lower():
            faltantes = _piezas_insuficientes(proceso_pk, tipo_oblea)
            if faltantes:
                request.session['stock_insuficiente'] = faltantes
                nombres = ', '.join(f['nombre'] for f in faltantes)
                messages.error(request, f'No hay stock suficiente de: {nombres}.')
                return
        messages.error(request, f'Error: {resp}')
        return

    orden_pk = resp.get('numero') if isinstance(resp, dict) else None
    if cantidad_lotes > 0 and orden_pk:
        creados, errores = _crear_lotes_para_orden(orden_pk, tipo_oblea, cantidad_lotes)
        # El trigger t_alerta_stock_insuficiente ya descontó lo del primer
        # lote al crear la orden (arriba); los demás lotes de este bucle
        # nunca pasan por un INSERT en orden, así que su consumo de piezas
        # no se descuenta solo — hay que hacerlo aquí.
        if creados > 1:
            _descontar_stock_lotes(proceso_pk, tipo_oblea, creados - 1)
        if errores:
            messages.error(request, f'Orden creada, pero solo {creados} de {cantidad_lotes} lotes se registraron.')
        else:
            messages.success(request, f'Orden creada con {creados} lote(s).')
    else:
        messages.success(request, 'Orden creada.')


def _editar_orden(request, pk):
    orden_antes = _get(f'/v1/detail/Orden/{pk}/') or {}
    estado_anterior = str(orden_antes.get('estado', '')).lower()

    if estado_anterior == 'cerra':
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return

    linea_pk = request.POST.get('linea', '').strip()
    tipo_oblea = request.POST.get('tipo_oblea', '').strip()
    estado = request.POST.get('estado', '').strip()
    cantidad_extra_raw = request.POST.get('cantidad_lotes_extra', '').strip()
    hora_inicio = _normalizar_hora(request.POST.get('hora_inicio', ''))
    hora_fin    = _normalizar_hora(request.POST.get('hora_fin', ''))

    if not tipo_oblea:
        messages.error(request, 'Selecciona el tipo de oblea.')
        return
    if estado not in _ESTADOS_ORDEN_VALIDOS:
        messages.error(request, 'El estado indicado no es válido.')
        return
    if hora_inicio and not _HORA_RE.match(hora_inicio):
        messages.error(request, 'La hora de inicio no es válida.')
        return
    if hora_fin and not _HORA_RE.match(hora_fin):
        messages.error(request, 'La hora de fin no es válida.')
        return
    hora_inicio_efectiva = hora_inicio or _hora_display(orden_antes.get('horaIni', ''))
    hora_fin_efectiva    = hora_fin or _hora_display(orden_antes.get('horaFin', ''))
    if (hora_inicio_efectiva != '—' and hora_fin_efectiva != '—'
            and hora_inicio_efectiva >= hora_fin_efectiva):
        messages.error(request, 'La hora de inicio debe ser anterior a la hora de fin.')
        return
    if cantidad_extra_raw and not cantidad_extra_raw.isdigit():
        messages.error(request, 'La cantidad de lotes a agregar debe ser un número.')
        return
    cantidad_lotes_extra = int(cantidad_extra_raw or 0)

    proceso_para_stock = _get_linea_proceso(linea_pk) if linea_pk else orden_antes.get('proceso')
    if cantidad_lotes_extra > 0:
        lotes_max = _lotes_max_por_stock(proceso_para_stock, tipo_oblea)
        if lotes_max is not None and cantidad_lotes_extra > lotes_max:
            messages.error(
                request,
                f'El stock actual solo alcanza para {lotes_max} lote(s) nuevo(s) de este tipo de oblea — se pidieron {cantidad_lotes_extra}.'
            )
            return

    payload = {
        'tipoOblea': tipo_oblea,
        'estado':    estado,
    }
    hoy = date.today().isoformat()
    if hora_inicio:
        payload['horaIni'] = f'{hoy} {hora_inicio}'
    if hora_fin:
        payload['horaFin'] = f'{hoy} {hora_fin}'

    if linea_pk:
        if not proceso_para_stock:
            messages.error(request, 'La línea seleccionada no tiene un proceso asignado.')
            return
        payload['linea']   = linea_pk
        payload['proceso'] = proceso_para_stock

    ok, resp = _patch(f'/v1/update/Orden/{pk}/', payload)
    if not ok:
        messages.error(request, f'Error: {resp}')
        return

    if payload['estado'] == 'cerra' and estado_anterior != 'cerra':
        _generar_reporte_orden(pk)

    if cantidad_lotes_extra > 0 and tipo_oblea:
        creados, errores = _crear_lotes_para_orden(pk, tipo_oblea, cantidad_lotes_extra)
        # A diferencia de crear una orden nueva, este PATCH nunca dispara el
        # trigger de stock (solo corre en INSERT sobre orden) — el consumo
        # de piezas de estos lotes no se descuenta solo, hay que hacerlo.
        if creados > 0:
            _descontar_stock_lotes(proceso_para_stock, tipo_oblea, creados)
        if errores:
            messages.error(request, f'Orden actualizada, pero solo se agregaron {creados} de {cantidad_lotes_extra} lotes nuevos.')
        else:
            messages.success(request, f'Orden actualizada y se agregaron {creados} lote(s) nuevo(s).')
    else:
        messages.success(request, 'Orden actualizada.')


def _agregar_lotes(request):
    orden_pk = request.POST.get('orden_id', '').strip()
    cantidad_raw = request.POST.get('cantidad_lotes', '').strip()
    if not orden_pk or not cantidad_raw.isdigit() or int(cantidad_raw) <= 0:
        messages.error(request, 'Indica cuántos lotes quieres agregar.')
        return
    cantidad = int(cantidad_raw)
    orden = _get(f'/v1/detail/Orden/{orden_pk}/')
    if str((orden or {}).get('estado', '')).lower() == 'cerra':
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return
    tipo_oblea = (orden or {}).get('tipoOblea')
    if not tipo_oblea:
        messages.error(request, 'No se pudo determinar el tipo de oblea de la orden.')
        return
    creados, errores = _crear_lotes_para_orden(orden_pk, tipo_oblea, cantidad)
    if errores:
        messages.error(request, f'Se agregaron {creados} de {cantidad} lotes (algunos fallaron).')
    else:
        messages.success(request, f'{creados} lote(s) agregado(s).')


def _lote_hold(request, pk):
    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, 'Indica el motivo del hold.')
        return
    ob = _get(f'/v1/detail/Oblea/{pk}/') or {}
    edo = str(ob.get('estado', '')).lower()
    if _orden_cerrada(ob.get('orden')):
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return
    if edo in ('termi', 'recha'):
        messages.error(request, 'No se puede poner en hold un lote que ya está finalizado.')
        return
    if edo == 'enhol':
        messages.error(request, 'Este lote ya está en hold.')
        return
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'enhol', 'hold_motivo': motivo})
    if ok:
        messages.success(request, 'Lote puesto en hold.')
    else:
        messages.error(request, f'Error: {resp}')


def _lote_liberar(request, pk):
    ob = _get(f'/v1/detail/Oblea/{pk}/') or {}
    orden_pk = ob.get('orden')
    if _orden_cerrada(orden_pk):
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return
    if str(ob.get('estado', '')).lower() != 'enhol':
        messages.error(request, 'Este lote no está en hold.')
        return
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'proce'})
    if not ok:
        messages.error(request, f'Error: {resp}')
        return

    # Si la orden de este lote también está en Hold, liberarlo puede liberar
    # la orden — pero solo si este era el ÚLTIMO lote de la orden que seguía
    # en Hold (mismo criterio que _orden_liberar_rechazando_lote). Si hay
    # otros lotes todavía en 'enhol', la orden se queda en Hold hasta que
    # también se resuelvan esos.
    orden_data = _get(f'/v1/detail/Orden/{orden_pk}/') or {}
    if str(orden_data.get('estado', '')).lower() != 'enhol':
        messages.success(request, 'Lote liberado del hold.')
        return

    obleas_de_orden = _get('/v1/list/Oblea/', [])
    otros_en_hold = [
        o for o in obleas_de_orden
        if str(o.get('orden')) == str(orden_pk)
        and str(o.get('numero')) != str(pk)
        and str(o.get('estado', '')).lower() == 'enhol'
    ]
    if otros_en_hold:
        messages.success(
            request,
            f'Lote liberado del hold. La orden sigue en Hold: todavía hay '
            f'{len(otros_en_hold)} lote(s) más en Hold.'
        )
        return

    ok2, resp2 = _patch(f'/v1/update/Orden/{orden_pk}/', {'estado': 'proce'})
    if ok2:
        messages.success(request, 'Lote liberado del hold. Era el único lote en Hold, así que la orden también se liberó.')
    else:
        messages.error(request, f'El lote se liberó, pero no se pudo liberar la orden: {resp2}')


def _orden_liberar(request, pk):
    """Libera una orden que el trigger t_scrap_excedente_del_permitido puso
    en hold automáticamente porque el yield global de alguno de sus lotes
    cayó por debajo del 95%."""
    orden_data = _get(f'/v1/detail/Orden/{pk}/') or {}
    estado_orden = str(orden_data.get('estado', '')).lower()
    if estado_orden == 'cerra':
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return
    if estado_orden != 'enhol':
        messages.error(request, 'Esta orden no está en hold.')
        return
    ok, resp = _patch(f'/v1/update/Orden/{pk}/', {'estado': 'proce'})
    if ok:
        messages.success(request, 'Orden liberada del hold.')
    else:
        messages.error(request, f'Error: {resp}')


def _orden_rechazar(request, pk):
    """Rechaza una orden que está en Hold — alternativa a liberarla: en vez
    de reanudar producción, se da por perdida. Mismo punto de entrada que
    _orden_liberar (solo aplica sobre una orden en Hold), pero con la lógica
    respectiva de un rechazo: pone la orden en 'recha' (no 'proce') y genera
    una alerta real, ya que a diferencia del Hold automático (que dispara el
    trigger t_scrap_excedente_del_permitido) un rechazo manual no la crea
    por sí solo."""
    orden_data = _get(f'/v1/detail/Orden/{pk}/') or {}
    estado_orden = str(orden_data.get('estado', '')).lower()
    if estado_orden == 'cerra':
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return
    if estado_orden != 'enhol':
        messages.error(request, 'Esta orden no está en hold.')
        return
    motivo = request.POST.get('motivo', '').strip()
    ok, resp = _patch(f'/v1/update/Orden/{pk}/', {'estado': 'recha'})
    if ok:
        descripcion = f'Orden #{pk} rechazada'
        if motivo:
            descripcion += f': {motivo}'
        _post('/v1/create/alerta/', {'descripcion': descripcion, 'estadoAlerta': 'sinre'})
        messages.success(request, 'Orden rechazada.')
    else:
        messages.error(request, f'Error: {resp}')


def _orden_liberar_rechazando_lote(request, pk, lote_pk):
    """Libera una orden en Hold rechazando específicamente el lote cuyo
    scrap excedió el límite permitido — a diferencia de _orden_liberar
    (reanuda la orden sin tocar el lote, que se queda tal cual con el
    mismo yield bajo el 95% que causó el Hold) y de _orden_rechazar (da
    por perdida TODA la orden), esta opción sacrifica solo el lote
    responsable y deja que el resto de los lotes sigan en proceso."""
    orden_data = _get(f'/v1/detail/Orden/{pk}/') or {}
    estado_orden = str(orden_data.get('estado', '')).lower()
    if estado_orden == 'cerra':
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return
    if estado_orden != 'enhol':
        messages.error(request, 'Esta orden no está en hold.')
        return

    lote_data = _get(f'/v1/detail/Oblea/{lote_pk}/') or {}
    if not lote_data or str(lote_data.get('orden')) != str(pk):
        messages.error(request, 'Ese lote no pertenece a esta orden.')
        return
    edo_lote = str(lote_data.get('estado', '')).lower()
    if edo_lote in ('termi', 'recha'):
        messages.error(request, 'Ese lote ya está en un estado final.')
        return

    motivo = request.POST.get('motivo', '').strip()

    ok, resp = _patch(f'/v1/update/Oblea/{lote_pk}/', {'estado': 'recha'})
    if not ok:
        messages.error(request, f'Error al rechazar el lote: {resp}')
        return
    # KPI final del lote rechazado — mismo criterio que cualquier otro lote
    # que llega a un estado final (ver _avanzar_estado_lote_y_orden).
    _post(f'/v1/kpi/registrar_por_lote/{lote_pk}/', {})

    folio = f'LOT-{int(lote_pk):04d}' if str(lote_pk).isdigit() else str(lote_pk)
    descripcion = f'{folio} rechazado para liberar la Orden #{pk} del Hold'
    if motivo:
        descripcion += f': {motivo}'
    _post('/v1/create/alerta/', {'descripcion': descripcion, 'estadoAlerta': 'sinre'})

    obleas_bd = _get('/v1/list/Oblea/', [])
    obleas_de_orden = [o for o in obleas_bd if str(o.get('orden')) == str(pk)]
    for o in obleas_de_orden:
        if str(o.get('numero')) == str(lote_pk):
            o['estado'] = 'recha'

    # La orden solo sale del Hold si este era el ÚLTIMO lote que seguía en
    # Hold — si hay otros lotes de la misma orden todavía en 'enhol' (p. ej.
    # alguien los puso en Hold manualmente además del que causó el exceso de
    # scrap), la orden se queda en Hold hasta que también se resuelvan esos.
    otros_en_hold = [
        o for o in obleas_de_orden
        if str(o.get('numero')) != str(lote_pk) and str(o.get('estado', '')).lower() == 'enhol'
    ]
    if otros_en_hold:
        messages.success(
            request,
            f'{folio} rechazado. La orden sigue en Hold: todavía hay '
            f'{len(otros_en_hold)} lote(s) más en Hold.'
        )
        return

    # Si con este lote ya quedaron TODOS los lotes de la orden en estado
    # final, la orden debe cerrarse igual que en el flujo normal (ver
    # _avanzar_estado_lote_y_orden) en vez de quedarse en 'proce' sin más.
    if obleas_de_orden and all(str(o.get('estado', '')).lower() in ('termi', 'recha') for o in obleas_de_orden):
        _patch(f'/v1/update/Orden/{pk}/', {'estado': 'cerra'})
        _generar_reporte_orden(pk)
        messages.success(request, f'{folio} rechazado. Era el último lote pendiente, así que la orden se cerró.')
        return

    ok2, resp2 = _patch(f'/v1/update/Orden/{pk}/', {'estado': 'proce'})
    if not ok2:
        messages.error(request, f'El lote se rechazó, pero no se pudo liberar la orden: {resp2}')
        return
    messages.success(request, f'{folio} rechazado y orden liberada del Hold.')


def _lote_scrap(request, pk):
    ob = _get(f'/v1/detail/Oblea/{pk}/') or {}
    edo = str(ob.get('estado', '')).lower()
    if _orden_cerrada(ob.get('orden')):
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return
    if edo == 'termi':
        messages.error(request, 'No se puede rechazar un lote que ya fue terminado exitosamente.')
        return
    if edo == 'recha':
        messages.error(request, 'Este lote ya está marcado como rechazado.')
        return
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'recha'})
    if ok:
        messages.success(request, 'Lote marcado como rechazado (scrap).')
    else:
        messages.error(request, f'Error: {resp}')


def _etapa_completar(request, pk):
    paso          = request.POST.get('paso', '').strip()
    resultado     = request.POST.get('resultado', 'aprobado').strip()
    observaciones = request.POST.get('observaciones', '')
    unidades_defecto_raw = request.POST.get('unidades_defecto', '').strip()

    if not paso:
        messages.error(request, 'Selecciona el paso a completar.')
        return
    if resultado not in ('aprobado', 'rechazado'):
        messages.error(request, 'El resultado indicado no es válido.')
        return
    if unidades_defecto_raw and not unidades_defecto_raw.isdigit():
        messages.error(request, 'Las unidades con defecto deben ser un número.')
        return
    unidades_defecto = int(unidades_defecto_raw or 0)

    ob = _get(f'/v1/detail/Oblea/{pk}/') or {}
    edo_lote = str(ob.get('estado', '')).lower()
    if edo_lote == 'enhol':
        messages.error(request, 'Este lote está en Hold. No se pueden completar etapas.')
        return
    if edo_lote in ('termi', 'recha'):
        messages.error(request, 'Este lote fue rechazado o ya está terminado y no puede continuar con más etapas.')
        return

    orden_data = _get(f"/v1/detail/Orden/{ob.get('orden')}/") or {}
    estado_orden = str(orden_data.get('estado', '')).lower()
    if estado_orden == 'cerra':
        messages.error(request, _MENSAJE_ORDEN_CERRADA)
        return
    if estado_orden == 'enhol':
        messages.error(request, 'La orden de este lote está en Hold por exceso de scrap. Libérala antes de continuar.')
        return
    if estado_orden == 'recha':
        messages.error(request, 'La orden de este lote fue rechazada. No se pueden completar más etapas.')
        return

    if resultado == 'rechazado':
        # Rechazar una etapa es una decisión sobre el YIELD GLOBAL del lote,
        # no sobre el scrap de esta etapa sola: solo se permite si, al aplicar
        # este scrap, el yield del lote completo (dies activos tras este paso
        # / cantidadDies fijo del Tipo_Oblea) cae por debajo del 95% — el
        # mismo umbral que usa el trigger t_scrap_excedente_del_permitido
        # para poner la orden en hold.
        dies_activos = ob.get('diesGenerados', 0)
        orden_data = _get(f"/v1/detail/Orden/{ob.get('orden')}/") or {}
        tipo_data = _get(f"/v1/detail/TipoOblea/{orden_data.get('tipoOblea')}/") if orden_data.get('tipoOblea') else {}
        dies_iniciales = (tipo_data or {}).get('cantidadDies', 0)
        dies_activos_despues = dies_activos - unidades_defecto
        yield_pct_despues = (dies_activos_despues / dies_iniciales * 100) if dies_iniciales > 0 else 0
        if yield_pct_despues >= 95:
            messages.error(request, 'Solo se puede rechazar una etapa si el scrap hace que el yield global del lote caiga por debajo del 95%.')
            return

    estado_map = {'aprobado': 'compl', 'rechazado': 'nocom'}
    estado = estado_map.get(resultado, 'compl')

    payload = {
        'paso':             paso,
        'oblea':            pk,
        'estado':           estado,
        'observaciones':    observaciones,
        'unidades_defecto': unidades_defecto,
    }
    defectos_json = request.POST.get('defectos_json', '')
    if defectos_json:
        try:
            defectos = json.loads(defectos_json)
            if isinstance(defectos, list) and defectos:
                payload['defectos'] = defectos
        except (ValueError, TypeError):
            pass

    ok, resp = _post('/v1/create/PasoRealizado/', payload)
    if not ok:
        messages.error(request, f'Error al completar: {resp}')
        return

    puso_en_hold = _avanzar_estado_lote_y_orden(pk)
    if puso_en_hold:
        # No fue un cierre exitoso de la etapa — el scrap de este paso hizo
        # caer el yield del lote por debajo del 95% y puso el lote/orden en
        # Hold, así que no corresponde decir "correctamente".
        messages.success(request, 'Etapa completada.')
    else:
        messages.success(request, 'Etapa completada correctamente.')


def _avanzar_estado_lote_y_orden(oblea_pk):
    """
    Tras registrar un Paso_Realizado: si el lote ya tiene TODAS sus etapas
    registradas, avanza su estado real (termi si todo fue aprobado, recha
    si alguna etapa fue rechazada). Y, según cómo queden los lotes de la
    orden, avanza el estado de la orden (abier -> proce -> cerra), siguiendo
    el catálogo real: Estado_Orden abier/proce/cerra, Estado_Oblea proce/termi/recha/enhol.
    No toca lotes en Hold (enhol) — esos requieren resolverse aparte.

    Devuelve True si esta llamada puso el lote/orden en Hold por exceso de
    scrap (para que el llamador pueda avisar que la etapa no cerró como un
    éxito limpio), False/None en cualquier otro caso.
    """
    ob = _get(f'/v1/detail/Oblea/{oblea_pk}/')
    if not ob:
        return False
    orden_num = ob.get('orden')
    orden = _get(f'/v1/detail/Orden/{orden_num}/')
    if not orden:
        return False
    proceso_codigo = str(orden.get('proceso', ''))

    pasos_bd, pasos_realizados_bd, obleas_bd = _get_many(
        '/v1/list/PasoProceso/',
        '/v1/list/PasoRealizado/',
        '/v1/list/Oblea/',
    )
    pasos_de_proceso = [p for p in pasos_bd if str(p.get('proceso')) == proceso_codigo]
    realizados_de_esta_oblea = {
        str(pr.get('paso', '')): pr
        for pr in pasos_realizados_bd
        if str(pr.get('oblea', '')) == str(oblea_pk)
    }

    nuevo_estado_lote = None
    if pasos_de_proceso and all(str(p.get('paso', '')) in realizados_de_esta_oblea for p in pasos_de_proceso):
        hay_rechazo = any(
            str(realizados_de_esta_oblea[str(p.get('paso', ''))].get('estado', '')).lower() == 'nocom'
            for p in pasos_de_proceso
        )
        nuevo_estado_lote = 'recha' if hay_rechazo else 'termi'
        if str(ob.get('estado', '')).lower() not in ('termi', 'recha'):
            _patch(f'/v1/update/Oblea/{oblea_pk}/', {'estado': nuevo_estado_lote})
            # KPI final del lote (Yield/Throughput/OEE) — se calcula una sola
            # vez aquí, no después de cada paso, para que Throughput/OEE
            # reflejen el proceso completo y no salgan "críticos" solo por
            # faltar tiempo/pasos a medio camino.
            _post(f'/v1/kpi/registrar_por_lote/{oblea_pk}/', {})

    edo_orden_actual = str(orden.get('estado', '')).lower()
    if edo_orden_actual == 'abier':
        _patch(f'/v1/update/Orden/{orden_num}/', {'estado': 'proce'})
        edo_orden_actual = 'proce'

    if (edo_orden_actual == 'enhol' and nuevo_estado_lote is None
            and str(ob.get('estado', '')).lower() not in ('termi', 'recha', 'enhol')):
        # Este paso fue el que hizo caer el yield del lote por debajo del
        # 95% y disparó t_scrap_excedente_del_permitido (por eso la orden ya
        # aparece 'enhol' aquí — si ya estuviera en hold de antes, _etapa_completar
        # ni hubiera dejado registrar este paso). El lote responsable también
        # queda en Hold, igual que si alguien lo hubiera puesto en Hold
        # manualmente desde su propia trazabilidad (ver _lote_hold), para que
        # la UI pueda señalar con precisión cuál lote fue la causa.
        _patch(f'/v1/update/Oblea/{oblea_pk}/', {'estado': 'enhol'})
        folio = f'LOT-{oblea_pk:04d}' if isinstance(oblea_pk, int) else str(oblea_pk)
        _post('/v1/create/alerta/', {
            'descripcion': f'Orden #{orden_num} puesta en Hold: {folio} excedió el límite de scrap permitido (yield < 95%).',
            'estadoAlerta': 'sinre',
        })
        return True

    if edo_orden_actual == 'proce' and nuevo_estado_lote:
        obleas_de_orden = [o for o in obleas_bd if str(o.get('orden')) == str(orden_num)]
        for o in obleas_de_orden:
            if str(o.get('numero')) == str(oblea_pk):
                o['estado'] = nuevo_estado_lote
        if obleas_de_orden and all(str(o.get('estado', '')).lower() in ('termi', 'recha') for o in obleas_de_orden):
            _patch(f'/v1/update/Orden/{orden_num}/', {'estado': 'cerra'})
            _generar_reporte_orden(orden_num)

    return False
    

def _generar_reporte_orden(orden_num):
    obleas_bd, pasos_realizados_bd = _get_many('/v1/list/Oblea/', '/v1/list/PasoRealizado/')
    obleas_de_orden = [o for o in obleas_bd if str(o.get('orden')) == str(orden_num)]

    # dies_finales viene directo de diesGenerados, que el trigger
    # t_actualizar_dies_por_paso ya mantiene al día restando el scrap de cada
    # paso registrado — no se le resta el scrap otra vez aquí.
    dies_finales = sum(int(o.get('diesGenerados', 0) or 0) for o in obleas_de_orden)

    obleas_pks = {str(o.get('numero')) for o in obleas_de_orden}
    scrap_total = sum(
        int(pr.get('scrap', 0) or 0)
        for pr in pasos_realizados_bd
        if str(pr.get('oblea', '')) in obleas_pks
    )
    _post('/v1/create/reportes/', {
        'unidades_apro': dies_finales,
        'unidaes_defect': scrap_total,
        'comentarios': 'Generado automáticamente al cerrar la orden.',
        'orden': orden_num,
    })


def _generar_reporte_manual(request, orden_num, oblea_num=None, reportes_url_name='admin_reportes'):
    """Botón "generar reporte" desde el detalle de una orden (oblea_num=None,
    reporte de toda la orden) o de un lote específico (oblea_num=pk) — mismo
    cálculo que _generar_reporte_orden, pero puede acotarse a un solo lote y
    siempre queda marcado como generado manualmente por quien lo pidió."""
    obleas_bd, pasos_realizados_bd = _get_many('/v1/list/Oblea/', '/v1/list/PasoRealizado/')
    if oblea_num:
        obleas_incluidas = [o for o in obleas_bd if str(o.get('numero')) == str(oblea_num)]
    else:
        obleas_incluidas = [o for o in obleas_bd if str(o.get('orden')) == str(orden_num)]

    dies_finales = sum(int(o.get('diesGenerados', 0) or 0) for o in obleas_incluidas)
    obleas_pks = {str(o.get('numero')) for o in obleas_incluidas}
    scrap_total = sum(
        int(pr.get('scrap', 0) or 0)
        for pr in pasos_realizados_bd
        if str(pr.get('oblea', '')) in obleas_pks
    )
    ok, resp = _post('/v1/create/reportes/', {
        'unidades_apro': dies_finales,
        'unidaes_defect': scrap_total,
        'comentarios': 'Generado manualmente desde producción.',
        'orden': orden_num,
        'oblea': oblea_num,
        'tipo_generacion': 'manual',
        'generado_por': request.session.get('user_id'),
    })
    if ok:
        # Calcula a qué página/sub-pestaña de Reportes le toca este reporte
        # nuevo, con el mismo orden y el mismo PAGE_SIZE_REPORTES (=7) que usa
        # BaseReportesView.get() en reportes/views.py — duplicado aquí (en vez
        # de importado) porque reportes/views.py ya importa de este archivo
        # (_generar_reporte_manual) y un import cruzado sería circular.
        PAGE_SIZE_REPORTES = 7
        reportes_prod = _get('/v1/list/reportes/', [])
        reportes_prod = sorted(reportes_prod, key=lambda r: (r.get('fecha', ''), r.get('hora', '')), reverse=True)
        es_lote = bool(oblea_num)
        rows_subtab = [r for r in reportes_prod if bool(r.get('oblea')) == es_lote]
        pagina = 1
        for i, r in enumerate(rows_subtab):
            if r.get('numero') == resp.get('numero'):
                pagina = i // PAGE_SIZE_REPORTES + 1
                break
        subtab = 'lote' if es_lote else 'orden'
        page_param = f'page_prod_{subtab}'
        ver_url = f"{reverse(reportes_url_name)}?tab=produccion&subtab_prod={subtab}&{page_param}={pagina}"
        messages.success(request, 'Reporte generado correctamente.', extra_tags=ver_url)
    else:
        messages.error(request, f'Error al generar el reporte: {resp}')


# ── Cálculo de etapas de un lote (mismo criterio que usa la app móvil) ───────

def _maquinas_por_paso():
    """codigo_paso -> 'nombre1, nombre2' de las máquinas del catálogo
    (MaquinaPaso) que pueden correr ese paso. Es dato de catálogo (qué
    máquina está pensada para ese paso), no de esta ejecución en particular
    — el proyecto no rastrea qué máquina física corrió cada Paso_Realizado."""
    maquina_paso_bd, maquinas_bd = _get_many('/v1/list/MaquinaPaso/', '/v1/list/maquinaria/')
    nombres_map = {str(m.get('numSerie')): m.get('nombre', '') for m in maquinas_bd}
    agrupado = {}
    for mp in maquina_paso_bd:
        nombre = nombres_map.get(str(mp.get('maquina')))
        if nombre:
            agrupado.setdefault(str(mp.get('paso', '')), []).append(nombre)
    return {codigo: ', '.join(nombres) for codigo, nombres in agrupado.items()}


def _operador_por_paso():
    """codigo_paso -> nombre del operador (Empleado) asignado a la primera
    máquina del catálogo (MaquinaPaso) que puede correr ese paso, igual que
    _maquinas_por_paso pero resolviendo Maquina.empleado -> Empleado."""
    maquina_paso_bd, maquinas_bd, empleados_bd = _get_many(
        '/v1/list/MaquinaPaso/', '/v1/list/maquinaria/', '/v1/list/empleados/'
    )
    maquinas_map = {str(m.get('numSerie', '')): m for m in maquinas_bd}
    empleados_map = {str(e.get('numero', '')): e for e in empleados_bd}
    resultado = {}
    for mp in maquina_paso_bd:
        codigo_paso = str(mp.get('paso', ''))
        if codigo_paso in resultado:
            continue
        maquina = maquinas_map.get(str(mp.get('maquina', '')))
        if not maquina or not maquina.get('empleado'):
            continue
        emp = empleados_map.get(str(maquina.get('empleado')))
        if emp:
            nombre = f"{emp.get('nombre', '')} {emp.get('primerApell', '')}".strip()
            if nombre:
                resultado[codigo_paso] = nombre
    return resultado


def _construir_etapas(pasos_de_proceso, catalogo_map, pasos_realizados_de_oblea, maquinas_por_paso=None):
    """
    pasos_de_proceso: lista de PasoProceso (dicts) ya ordenados por 'orden'.
    pasos_realizados_de_oblea: dict {codigo_paso: paso_realizado} SOLO de esta oblea.
    maquinas_por_paso: dict {codigo_paso: 'nombre de máquina(s)'} de _maquinas_por_paso().
    Marca completado cada paso con Paso_Realizado propio; el primer paso pendiente
    queda en_curso. No avanza si el paso fue rechazado ('nocom'): se queda visible
    como completado igual (el registro ya existe), consistente con el criterio
    que ya usa el endpoint de la app móvil.
    """
    maquinas_por_paso = maquinas_por_paso or {}
    etapas = []
    for p in pasos_de_proceso:
        codigo = str(p.get('paso', ''))
        cat = catalogo_map.get(codigo, {})
        realizado = pasos_realizados_de_oblea.get(codigo)
        if realizado:
            edo_pr = str(realizado.get('estado', '')).lower()
            estado = 'rechazado' if edo_pr == 'nocom' else 'aprobado'
        else:
            estado = 'pendiente'
        etapas.append({
            'codigo':              codigo,
            'nombre':              cat.get('nombre', codigo),
            'descripcion':         cat.get('descripcion', ''),
            'estado':              estado,
            'meta':                realizado.get('observaciones') if realizado else None,
            'scrap':               int(realizado.get('scrap', 0) or 0) if realizado else None,
            'maquina_nombre':      maquinas_por_paso.get(codigo) or None,
            'tiempo_estimado_seg': cat.get('tiempoEstimado', 0),
            'hora_inicio_iso':     str(realizado.get('hora', '') or '') if realizado else '',
        })

    # La primera etapa pendiente pasa a "en_curso"
    for e in etapas:
        if e['estado'] == 'pendiente':
            e['estado'] = 'en_curso'
            break

    return etapas


def _calcular_yield(oblea_num, pasos_realizados_bd, dies_iniciales, dies_activos_actual):
    """dies_iniciales = Tipo_Oblea.cantidadDies (fijo, no cambia con el tiempo).
    dies_activos_actual = oblea.diesGenerados: el trigger t_actualizar_dies_por_paso
    ya le resta el scrap de cada paso registrado directo en la BD, así que aquí
    no se le vuelve a restar nada (restarlo otra vez lo contaba dos veces)."""
    scrap_total = sum(
        int(pr.get('scrap', 0) or 0)
        for pr in pasos_realizados_bd
        if str(pr.get('oblea', '')) == str(oblea_num)
    )
    dies_activos = max(0, dies_activos_actual)
    yield_pct = round(dies_activos / dies_iniciales * 100, 1) if dies_iniciales > 0 else 0
    return dies_activos, scrap_total, yield_pct


def _calcular_yield_sp(lote_pk):
    """Yield de un lote vía el procedimiento almacenado sp_calcularYieldLote
    — solo hace falta mandar el número de lote, el procedimiento hace el
    join contra tipo_oblea internamente. Se usa en la vista de detalle de UN
    solo lote (supervisor_lote_detalle); los listados con muchos lotes a la
    vez (admin_produccion, supervisor_ordenes) siguen usando _calcular_yield
    en Python puro sobre datos ya traídos en bloque por REST, para no
    convertir cada carga de esas páginas en una llamada a MySQL por lote."""
    with connection.cursor() as cursor:
        cursor.callproc('sp_calcularYieldLote', [lote_pk, 0])
        cursor.execute('SELECT @_sp_calcularYieldLote_1')
        row = cursor.fetchone()
    valor = row[0] if row and row[0] is not None else 0
    return round(float(valor), 1)


def _estado_orden_display(edo_orden, lotes_de_orden):
    """
    Determina el estado visual de una orden y cuántos de sus lotes ya quedaron
    resueltos (terminados o rechazados) — y por separado, cuántos de cada uno,
    para que un lote rechazado nunca se cuente silenciosamente como
    "completado". Único punto de esta lógica — admin y supervisor la
    comparten para no divergir entre sí.
    Catálogo real: Estado_Orden abier/proce/cerra/enhol/recha. 'enhol' lo pone
    automáticamente el trigger t_scrap_excedente_del_permitido cuando el yield
    global de algún lote de la orden cae por debajo del 95%. 'recha' lo pone
    explícitamente _orden_rechazar cuando alguien rechaza manualmente una
    orden que está en Hold — no confundir con el 'rechazado' derivado de una
    orden 'cerra' cuando TODOS sus lotes terminaron rechazados (ambos casos
    comparten la misma palabra visual porque para el usuario es el mismo
    concepto: la orden no se pudo completar). Una orden 'cerra' se muestra
    como 'rechazado' solo si TODOS sus lotes terminaron rechazados; si al
    menos uno se completó, se considera 'cerrada' (una orden cerrada ya no
    admite más cambios — ni sobre ella ni sobre sus lotes).
    """
    total = len(lotes_de_orden)
    terminados = sum(1 for ob in lotes_de_orden if str(ob.get('estado', '')).lower() == 'termi')
    rechazados = sum(1 for ob in lotes_de_orden if str(ob.get('estado', '')).lower() == 'recha')
    resueltos = terminados + rechazados
    pct = round(resueltos / total * 100) if total > 0 else 0

    edo = str(edo_orden or '').lower()
    if edo == 'enhol':
        edo_str = 'hold'
    elif edo == 'recha':
        edo_str = 'rechazado'
    elif edo == 'cerra':
        edo_str = 'rechazado' if (total > 0 and rechazados == total) else 'cerrada'
    elif edo == 'proce':
        edo_str = 'en_proceso'
    elif edo == 'abier':
        edo_str = 'abierta'
    else:
        edo_str = 'desconocido'

    # resueltos (compatibilidad con las tablas de listado, que muestran
    # "completados/total" junto a la barra de progreso — ahí "completado"
    # históricamente significa "ya no está activo", terminado o rechazado)
    # se sigue devolviendo igual; terminados y rechazados por separado son
    # para las vistas de detalle, que si necesitan distinguirlos.
    return edo_str, resueltos, pct, terminados, rechazados


# ── Helper compartido para construir ordenes y lotes ─────────────────────────

def _piezas_por_proceso_map(proceso_pieza_bd, piezas_bd):
    """codigo_proceso -> [{'nombre':..., 'cantidad':...}, ...]"""
    piezas_map = {str(z.get('codigo', '')): z for z in piezas_bd}
    resultado = {}
    for rel in proceso_pieza_bd:
        proceso_cod = str(rel.get('proceso', ''))
        pieza = piezas_map.get(str(rel.get('pieza', '')), {})
        resultado.setdefault(proceso_cod, []).append({
            'nombre': pieza.get('nombre', rel.get('pieza')),
            'cantidad': rel.get('cantPiezas', 0),
        })
    return resultado


def _build_ordenes_lotes():
    (ordenes_bd, obleas_bd, procesos_bd, lineas_bd, tipos_oblea_bd,
     pasos_bd, pasos_catalogo, pasos_realizados_bd, alertas_bd, linea_proceso_bd,
     proceso_pieza_bd, piezas_bd, empleados_bd) = _get_many(
        '/v1/list/Orden/',
        '/v1/list/Oblea/',
        '/v1/list/Proceso/',
        '/v1/list/Linea/',
        '/v1/list/TipoOblea/',
        '/v1/list/PasoProceso/',
        '/v1/list/pasos/',
        '/v1/list/PasoRealizado/',
        '/v1/list/alertas/',
        '/v1/list/LineaProceso/',
        '/v1/list/ProcesoPieza/',
        '/v1/list/piezas/',
        '/v1/list/empleados/',
    )
    catalogo_map = {str(p.get('codigo', '')): p for p in pasos_catalogo}
    procesos_map = {str(p.get('codigo', '')): p for p in procesos_bd}
    piezas_por_proceso = _piezas_por_proceso_map(proceso_pieza_bd, piezas_bd)
    empleados_map = {str(e.get('numero', '')): e for e in empleados_bd}
    # Linea.proceso (campo directo del modelo) no se usa realmente — la
    # relación línea↔proceso real vive en la tabla puente LineaProceso.
    proceso_por_linea = {str(lp.get('linea')): str(lp.get('proceso')) for lp in linea_proceso_bd}
    lineas_map   = {str(l.get('codigo', '')): l for l in lineas_bd}
    tipos_map    = {str(t.get('codigo', '')): t for t in tipos_oblea_bd}

    ordenes = []
    for o in ordenes_bd:
        num   = o.get('numero')
        obs   = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
        total = len(obs)
        en_proc = sum(1 for ob in obs if str(ob.get('estado', '')).lower() == 'proce')
        edo_str, comp, pct, terminados, rechazados = _estado_orden_display(o.get('estado'), obs)

        linea_pk = str(o.get('linea', '')) if o.get('linea') else ''
        tipo_pk  = str(o.get('tipoOblea', '')) if o.get('tipoOblea') else ''

        ordenes.append({
            'pk': num,
            'numero': f'ORD-{num:04d}' if isinstance(num, int) else str(num),
            'proceso': str(o.get('proceso', '—')),
            'proceso_nombre': procesos_map.get(str(o.get('proceso', '')), {}).get('nombre', o.get('proceso', '—')),
            'linea_pk': linea_pk,
            'linea_nombre': lineas_map.get(linea_pk, {}).get('nombre', '—') if linea_pk else '—',
            'tipo_oblea_pk': tipo_pk,
            'tipo_oblea_nombre': tipos_map.get(tipo_pk, {}).get('descripcion', '—') if tipo_pk else '—',
            'hora_inicio':         _hora_display(o.get('horaIni', '')),
            'hora_fin':            _hora_display(o.get('horaFin', '')),
            'hora_inicio_display': _hora_display(o.get('horaIni', '')),
            'hora_fin_display':    _hora_display(o.get('horaFin', '')),
            'fecha_creacion_display': _fecha_display(o.get('fecha', '')),
            'creado_por': (lambda e: f"{e.get('nombre','')} {e.get('primerApell','')}".strip() or '—')(empleados_map.get(str(o.get('empleado', '')), {})),
            'total_lotes': total,
            'completados': comp,
            'lotes_terminados': terminados,
            'lotes_rechazados': rechazados,
            'en_proceso': en_proc,
            'pct': pct,
            'estado': edo_str,
            'estado_pk': str(o.get('estado', '')),
            'tiene_hold': any(str(ob.get('estado', '')).lower() == 'enhol' for ob in obs),
        })

    maquinas_por_paso = _maquinas_por_paso()
    operador_por_paso = _operador_por_paso()

    lotes = []
    for ob in obleas_bd:
        num       = ob.get('numero')
        orden_num = ob.get('orden')
        edo       = str(ob.get('estado', '')).lower()

        edo_str = {'termi': 'aprobado', 'recha': 'rechazado', 'enhol': 'hold', 'proce': 'en_proceso'}.get(edo, 'pendiente')

        orden_data       = next((o for o in ordenes_bd if str(o.get('numero')) == str(orden_num)), {})
        proceso_codigo   = str(orden_data.get('proceso', ''))
        pasos_de_proceso = sorted(
            [p for p in pasos_bd if str(p.get('proceso')) == proceso_codigo],
            key=lambda x: x.get('orden', 0)
        )
        realizados_de_esta_oblea = {
            str(pr.get('paso', '')): pr
            for pr in pasos_realizados_bd
            if str(pr.get('oblea', '')) == str(num)
        }
        etapas = _construir_etapas(pasos_de_proceso, catalogo_map, realizados_de_esta_oblea, maquinas_por_paso)
        pasos_completados = sum(1 for e in etapas if e['estado'] in ('aprobado', 'rechazado'))
        etapa_activa = next((e for e in etapas if e['estado'] == 'en_curso'), None)

        tipo_pk_lote  = str(orden_data.get('tipoOblea', '')) if orden_data.get('tipoOblea') else ''
        dies_iniciales = tipos_map.get(tipo_pk_lote, {}).get('cantidadDies') or ob.get('diesGenerados', 0)
        dies_activos, scrap_total, yield_pct = _calcular_yield(
            num, pasos_realizados_bd, dies_iniciales, ob.get('diesGenerados', 0)
        )

        lote_linea_pk = str(orden_data.get('linea', '')) if orden_data.get('linea') else ''

        lotes.append({
            'pk': num,
            'folio': f'LOT-{num:04d}' if isinstance(num, int) else str(num),
            'orden_pk': orden_num,
            'proceso': str(orden_data.get('proceso', '—')),
            'proceso_nombre': procesos_map.get(str(orden_data.get('proceso', '')), {}).get('nombre', orden_data.get('proceso', '—')),
            'linea_nombre': lineas_map.get(lote_linea_pk, {}).get('nombre', '—') if lote_linea_pk else '—',
            'operador_nombre': operador_por_paso.get(etapa_activa['codigo'], '—') if etapa_activa else '—',
            'hora_inicio': _hora_display(orden_data.get('horaIni', '')),
            'hora_fin': _hora_display(orden_data.get('horaFin', '')),
            'total_pasos': len(etapas),
            'pasos_completados': pasos_completados,
            'estado': edo_str,
            'orden_en_hold': str(orden_data.get('estado', '')).lower() == 'enhol',
            'orden_rechazada': str(orden_data.get('estado', '')).lower() == 'recha',
            'dies_iniciales': dies_iniciales,
            'dies_activos': dies_activos,
            'scrap': scrap_total,
            'yield_pct': yield_pct,
            'etapas': etapas,
            'piezas': piezas_por_proceso.get(proceso_codigo, []),
        })

    plantillas = [
        _FakeObj(pk=p.get('codigo'), nombre=p.get('nombre', ''))
        for p in procesos_bd
    ]
    lineas_activas = [
        {'pk': l.get('codigo'), 'nombre': l.get('nombre', ''),
        'proceso_pk': proceso_por_linea.get(str(l.get('codigo', ''))),
        'proceso_nombre': procesos_map.get(proceso_por_linea.get(str(l.get('codigo', '')), ''), {}).get('nombre', '')}
        for l in lineas_bd
        if proceso_por_linea.get(str(l.get('codigo', '')))
    ]
    tipos_oblea_activos = [
        {'pk': t.get('codigo'), 'nombre': t.get('descripcion', '')}
        for t in tipos_oblea_bd
    ]

    return ordenes, lotes, plantillas, lineas_activas, tipos_oblea_activos, alertas_bd


# ════════════════════════════════════════════════════════════════
# ADMIN — PRODUCCIÓN
# ════════════════════════════════════════════════════════════════

def admin_produccion(request):
    # alertas_bd sin usar aquí: recent_notifications/unread_count del topbar
    # ahora los pone el context processor home.context_processors.notificaciones
    # para toda la app, en vez de recalcularlos por separado en cada vista.
    ordenes, lotes, plantillas, lineas, tipos_oblea, _alertas_bd = _build_ordenes_lotes()
    ctx = {
        'user_role': 'Administrador',
        'breadcrumbs': [],
    }

    # Filtro + paginación server-side de la tabla de órdenes — mismo patrón
    # que Personal/Maquinaria/Reportes/Organización/Inventario (numerado,
    # abajo de la tabla). "ordenes" (sin filtrar) se conserva completo para
    # ordenes_json, que el JS usa para abrir el detalle de CUALQUIER orden
    # sin importar en qué página de la tabla esté.
    q = request.GET.get('q', '').strip().lower()
    estado_filtro = request.GET.get('estado', '').strip()
    ordenes_filtradas = ordenes
    if q:
        ordenes_filtradas = [o for o in ordenes_filtradas if q in str(o.get('numero', '')).lower()]
    if estado_filtro:
        ordenes_filtradas = [o for o in ordenes_filtradas if o.get('estado') == estado_filtro]
    ordenes_page = Paginator(ordenes_filtradas, PAGE_SIZE_PRODUCCION).get_page(request.GET.get('page', 1))
    produccion_extra_params = urlencode({k: v for k, v in {'q': q, 'estado': estado_filtro}.items() if v})
    if produccion_extra_params:
        produccion_extra_params += '&'

    defectos_bd, paso_defecto_bd = _get_many('/v1/list/Defecto/', '/v1/list/PasoDefecto/')
    defectos_map = {str(d.get('codigo')): d for d in defectos_bd if d.get('activo', True)}
    defectos_por_paso = {}
    for rel in paso_defecto_bd:
        d = defectos_map.get(str(rel.get('defecto')))
        if d:
            defectos_por_paso.setdefault(str(rel.get('paso')), []).append(
                {'codigo': d.get('codigo'), 'descripcion': d.get('descripcion', '')}
            )

    ctx.update({
        'ordenes_page':         ordenes_page,
        'produccion_extra_params': produccion_extra_params,
        'q':                    q,
        'estado_filtro':        estado_filtro,
        'lotes':                lotes,
        'plantillas':           plantillas,
        'lineas':               lineas,
        'tipos_oblea':          tipos_oblea,
        'ordenes_json':         json.dumps(ordenes),
        'lotes_json':           json.dumps(lotes),
        'defectos_por_paso_json': json.dumps(defectos_por_paso),
        # Bandeja global de respaldo — si un paso no tiene defectos propios
        # ligados en PasoDefecto, se ofrece el catálogo completo en vez de
        # dejar al operador sin ninguna opción.
        'defectos_catalogo_json': json.dumps(
            [{'codigo': d.get('codigo'), 'descripcion': d.get('descripcion', '')} for d in defectos_map.values()]
        ),
        'maquinas_disponibles': [],
        'empleados':            [],
        'backend_url':          BACKEND_URL,
        'stock_insuficiente':   request.session.pop('stock_insuficiente', None),
        'breadcrumbs': [
            {'label': 'Dashboard',  'url': '/admin-dash/'},
            {'label': 'Producción', 'url': '/admin/produccion/'},
        ],
    })
    return render(request, 'admin/produccion.html', ctx)


def admin_produccion_plantilla_crear(request):
    return admin_organizacion_plantilla_crear(request)


def _admin_produccion_redirect(orden_pk=None, lote_pk=None):
    url = reverse('admin_produccion')
    params = []
    if orden_pk:
        params.append(f'orden={orden_pk}')
    if lote_pk:
        params.append(f'lote={lote_pk}')
    if params:
        url += '?' + '&'.join(params)
    return redirect(url)


def admin_orden_crear(request):
    if request.method == 'POST':
        _crear_orden(request)
    return redirect('admin_produccion')


def admin_lotes_max_stock(request):
    proceso_pk = request.GET.get('proceso', '') or _get_linea_proceso(request.GET.get('linea', ''))
    lotes_max = _lotes_max_por_stock(proceso_pk, request.GET.get('tipo_oblea', ''))
    return JsonResponse({'lotes_max': lotes_max})


def admin_orden_editar(request, pk):
    if request.method == 'POST':
        _editar_orden(request, pk)
    return _admin_produccion_redirect(orden_pk=pk)


def admin_lote_registrar(request):
    orden_pk = request.POST.get('orden_id', '') if request.method == 'POST' else None
    if request.method == 'POST':
        _agregar_lotes(request)
    return _admin_produccion_redirect(orden_pk=orden_pk)


def admin_lote_hold(request, pk):
    orden_pk = request.POST.get('orden_id', '') if request.method == 'POST' else None
    if request.method == 'POST':
        _lote_hold(request, pk)
    return _admin_produccion_redirect(orden_pk=orden_pk, lote_pk=pk)


def admin_lote_liberar(request, pk):
    orden_pk = request.POST.get('orden_id', '') if request.method == 'POST' else None
    if request.method == 'POST':
        _lote_liberar(request, pk)
    return _admin_produccion_redirect(orden_pk=orden_pk, lote_pk=pk)


def admin_orden_liberar(request, pk):
    if request.method == 'POST':
        _orden_liberar(request, pk)
    return _admin_produccion_redirect(orden_pk=pk)

def admin_orden_rechazar(request, pk):
    if request.method == 'POST':
        _orden_rechazar(request, pk)
    return _admin_produccion_redirect(orden_pk=pk)

def admin_orden_liberar_rechazando_lote(request, pk, lote_pk):
    if request.method == 'POST':
        _orden_liberar_rechazando_lote(request, pk, lote_pk)
    return _admin_produccion_redirect(orden_pk=pk)


def admin_lote_rechazar_liberando_orden(request, pk):
    """Misma acción que admin_orden_liberar_rechazando_lote, pero llamada
    desde la trazabilidad del propio lote (no desde el detalle de la orden)
    — resuelve la orden a partir del lote en vez de recibirla en la URL."""
    ob = _get(f'/v1/detail/Oblea/{pk}/') or {}
    orden_pk = ob.get('orden')
    if request.method == 'POST' and orden_pk:
        _orden_liberar_rechazando_lote(request, orden_pk, pk)
    return _admin_produccion_redirect(orden_pk=orden_pk, lote_pk=pk)


def admin_orden_generar_reporte(request, pk):
    if request.method == 'POST':
        _generar_reporte_manual(request, pk, reportes_url_name='admin_reportes')
    return _admin_produccion_redirect(orden_pk=pk)


def admin_lote_generar_reporte(request, pk):
    orden_pk = request.POST.get('orden_id', '') if request.method == 'POST' else None
    if request.method == 'POST':
        _generar_reporte_manual(request, orden_pk, oblea_num=pk, reportes_url_name='admin_reportes')
    return _admin_produccion_redirect(orden_pk=orden_pk, lote_pk=pk)


def admin_etapa_completar(request, pk):
    orden_pk = request.POST.get('orden_id', '') if request.method == 'POST' else None
    if request.method == 'POST':
        _etapa_completar(request, pk)
    return _admin_produccion_redirect(orden_pk=orden_pk, lote_pk=pk)


# ════════════════════════════════════════════════════════════════
# ADMIN — ORGANIZACIÓN (plantillas, obleas, líneas) — SOLO ADMIN
# ════════════════════════════════════════════════════════════════

def admin_organizacion(request):
    (procesos_bd, tipos_oblea, lineas_bd, _alertas_bd,
     pasos_bd, pasos_proceso_bd, proceso_pieza_bd, piezas_bd, linea_proceso_bd,
     maquina_paso_bd, maquinas_bd) = _get_many(
        '/v1/list/Proceso/',
        '/v1/list/TipoOblea/',
        '/v1/list/Linea/',
        '/v1/list/alertas/',
        '/v1/list/pasos/',
        '/v1/list/PasoProceso/',
        '/v1/list/ProcesoPieza/',
        '/v1/list/piezas/',
        '/v1/list/LineaProceso/',
        '/v1/list/MaquinaPaso/',
        '/v1/list/maquinaria/',
    )
    maquinas_map = {str(m.get('numSerie', '')): m for m in maquinas_bd}
    maquinas_por_paso = {}
    for mp in maquina_paso_bd:
        codigo_paso = str(mp.get('paso', ''))
        num_serie = str(mp.get('maquina', ''))
        m = maquinas_map.get(num_serie)
        if m:
            maquinas_por_paso.setdefault(codigo_paso, []).append(
                {'rel_pk': mp.get('id'), 'pk': num_serie, 'nombre': m.get('nombre', num_serie)}
            )
    proceso_por_linea = {str(lp.get('linea')): str(lp.get('proceso')) for lp in linea_proceso_bd}
    # recent_notifications/unread_count del topbar los pone el context
    # processor home.context_processors.notificaciones para toda la app.
    ctx = {
        'user_role': 'Administrador',
        'breadcrumbs': [],
    }

    pasos_map = {str(p.get('codigo', '')): p for p in pasos_bd}
    piezas_map = {str(z.get('codigo', '')): z for z in piezas_bd}
    procesos_map = {str(p.get('codigo', '')): p for p in procesos_bd}

    plantillas = []
    for p in procesos_bd:
        codigo = p.get('codigo')
        pasos_rel = sorted(
            [pp for pp in pasos_proceso_bd if str(pp.get('proceso')) == str(codigo)],
            key=lambda x: x.get('orden', 0)
        )
        piezas_rel = [pz for pz in proceso_pieza_bd if str(pz.get('proceso')) == str(codigo)]
        plantillas.append({
            'pk':          codigo,
            'nombre':      p.get('nombre', '—'),
            'descripcion': p.get('descripcion', ''),
            'pasos_count': len(pasos_rel),
            'pasos': [
                {
                    'rel_pk': pp.get('id'),
                    'codigo': pp.get('paso'),
                    'nombre': pasos_map.get(str(pp.get('paso', '')), {}).get('nombre', pp.get('paso')),
                }
                for pp in pasos_rel
            ],
            'piezas': [
                {
                    'rel_pk':   pz.get('id'),
                    'codigo':   pz.get('pieza'),
                    'nombre':   piezas_map.get(str(pz.get('pieza', '')), {}).get('nombre', pz.get('pieza')),
                    'cantidad': pz.get('cantPiezas', 0),
                }
                for pz in piezas_rel
            ],
        })

    tipos_oblea_front = [
        {
            'pk':           t.get('codigo'),
            'codigo':       t.get('codigo'),
            'nombre':       t.get('descripcion', ''),
            'dies_maximos': t.get('cantidadDies', 0),
        }
        for t in tipos_oblea
    ]

    lineas = [
        {
            'pk':               l.get('codigo'),
            'nombre':           l.get('nombre', ''),
            'proceso_pk':       proceso_por_linea.get(str(l.get('codigo', ''))),
            'proceso_asignado': procesos_map.get(proceso_por_linea.get(str(l.get('codigo', '')), ''), {}).get('nombre'),
        }
        for l in lineas_bd
    ]

    pasos = [
        {
            'pk':                  p.get('codigo'),
            'codigo':              p.get('codigo'),
            'nombre':              p.get('nombre', ''),
            'descripcion':         p.get('descripcion', ''),
            'tiempo_estimado_seg': p.get('tiempoEstimado', 0),
            'tiempo_estimado_min': round((p.get('tiempoEstimado', 0) or 0) / 60),
            'maquinas':            maquinas_por_paso.get(str(p.get('codigo', '')), []),
            'maquinas_json':       json.dumps(maquinas_por_paso.get(str(p.get('codigo', '')), [])),
        }
        for p in pasos_bd
    ]

    plantillas_page = Paginator(plantillas, PAGE_SIZE_ORGANIZACION).get_page(request.GET.get('page', 1))
    lineas_page     = Paginator(lineas, PAGE_SIZE_ORGANIZACION).get_page(request.GET.get('page_lineas', 1))
    obleas_page     = Paginator(tipos_oblea_front, PAGE_SIZE_ORGANIZACION).get_page(request.GET.get('page_obleas', 1))
    pasos_page      = Paginator(pasos, PAGE_SIZE_ORGANIZACION).get_page(request.GET.get('page_pasos', 1))

    ctx.update({
        'plantillas': plantillas,
        'plantillas_page':  plantillas_page,
        'plantillas_extra_params': 'tab=plantillas&',
        'tipos_oblea':      obleas_page,
        'obleas_extra_params': 'tab=obleas&',
        'lineas': lineas,
        'lineas_page': lineas_page,
        'lineas_extra_params': 'tab=lineas&',
        'procesos_activos': plantillas,
        'pasos': pasos_page,
        'pasos_extra_params': 'tab=pasos&',
        'pasos_activos': pasos,
        'piezas_catalogo': [{'pk': z.get('codigo'), 'nombre': z.get('nombre', '')} for z in piezas_bd],
        'maquinas_catalogo': [
            {'pk': m.get('numSerie'), 'nombre': m.get('nombre', '')}
            for m in maquinas_bd if str(m.get('estado', '')).lower() == 'act'
        ],
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/admin-dash/'},
            {'label': 'Organización', 'url': '/admin/organizacion/'},
        ],
    })
    return render(request, 'admin/organizacion.html', ctx)


def admin_organizacion_plantilla_crear(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().lower()
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()

        errores = []
        if not codigo:
            errores.append('El código de la plantilla es obligatorio.')
        elif len(codigo) > 5:
            errores.append('El código no puede tener más de 5 caracteres.')
        elif not _CODIGO_RE.match(codigo):
            errores.append('El código solo puede tener letras minúsculas, números y guiones.')

        if not nombre:
            errores.append('El nombre de la plantilla es obligatorio.')
        elif len(nombre) > 20:
            errores.append('El nombre no puede tener más de 20 caracteres.')

        if not descripcion:
            errores.append('La descripción de la plantilla es obligatoria.')
        elif len(descripcion) > 80:
            errores.append('La descripción no puede tener más de 80 caracteres.')

        if not errores:
            procesos_bd = _get('/v1/list/Proceso/', [])
            if any(str(p.get('codigo', '')).lower() == codigo for p in procesos_bd):
                errores.append(f'Ya existe una plantilla con el código "{codigo}".')
            if nombre and any(str(p.get('nombre', '')).strip().lower() == nombre.lower() for p in procesos_bd):
                errores.append(f'Ya existe una plantilla con el nombre "{nombre}".')

        # Validar los pasos nuevos definidos inline antes de crear nada
        nuevos_codigo = request.POST.getlist('paso_nuevo_codigo')
        nuevos_nombre = request.POST.getlist('paso_nuevo_nombre')
        nuevos_desc   = request.POST.getlist('paso_nuevo_descripcion')
        nuevos_tiempo = request.POST.getlist('paso_nuevo_tiempo')
        pasos_bd = _get('/v1/list/pasos/', []) if not errores else []
        codigos_nuevos_vistos = set()
        for i, pcod in enumerate(nuevos_codigo):
            pcod = pcod.strip().lower()
            if not pcod:
                continue
            pnom = (nuevos_nombre[i] if i < len(nuevos_nombre) else '').strip()
            pdesc = (nuevos_desc[i] if i < len(nuevos_desc) else '').strip()
            if len(pcod) > 5 or not _CODIGO_RE.match(pcod):
                errores.append(f'El código de paso "{pcod}" no es válido (máx. 5 caracteres, minúsculas/números/guiones).')
            elif any(str(p.get('codigo', '')).lower() == pcod for p in pasos_bd) or pcod in codigos_nuevos_vistos:
                errores.append(f'Ya existe un paso con el código "{pcod}".')
            codigos_nuevos_vistos.add(pcod)
            if not pnom:
                errores.append(f'El paso "{pcod}" necesita un nombre.')
            elif len(pnom) > 20:
                errores.append(f'El nombre del paso "{pcod}" no puede tener más de 20 caracteres.')
            if not pdesc:
                errores.append(f'El paso "{pcod}" necesita una descripción.')
            elif len(pdesc) > 80:
                errores.append(f'La descripción del paso "{pcod}" no puede tener más de 80 caracteres.')
            tiempo_raw = str(nuevos_tiempo[i]).strip() if i < len(nuevos_tiempo) else ''
            if tiempo_raw and not tiempo_raw.isdigit():
                errores.append(f'El tiempo del paso "{pcod}" debe ser un número.')

        # Validar piezas asignadas
        piezas_codigo   = request.POST.getlist('pieza_codigo')
        piezas_cantidad = request.POST.getlist('pieza_cantidad')
        for i, zcod in enumerate(piezas_codigo):
            zcod = zcod.strip()
            if not zcod:
                continue
            cant_raw = str(piezas_cantidad[i]).strip() if i < len(piezas_cantidad) else ''
            if not cant_raw.isdigit() or int(cant_raw) < 1:
                errores.append(f'La cantidad de la pieza "{zcod}" debe ser un número mayor a 0.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return _organizacion_redirect('plantillas')

        ok, resp = _post('/v1/create/Proceso/', {
            'codigo':      codigo,
            'nombre':      nombre,
            'descripcion': descripcion,
        })
        if not ok:
            messages.error(request, f'Error al crear la plantilla: {resp}')
            return _organizacion_redirect('plantillas')

        errores_post = []

        # 1. Crear los pasos nuevos definidos inline (modal apilado, plantilla nueva)
        for i, pcod in enumerate(nuevos_codigo):
            pcod = pcod.strip().lower()
            if not pcod:
                continue
            ok_p, resp_p = _post('/v1/create/Paso/', {
                'codigo':         pcod,
                'nombre':         nuevos_nombre[i] if i < len(nuevos_nombre) else pcod,
                'descripcion':    nuevos_desc[i] if i < len(nuevos_desc) else '',
                'tiempoEstimado': _duracion_str(int(nuevos_tiempo[i] or 0) * 60 if i < len(nuevos_tiempo) and nuevos_tiempo[i] else 0),
            })
            if not ok_p:
                errores_post.append(f'Paso {pcod}: {resp_p}')

        # 2. Enlazar pasos (existentes + recién creados) en el orden en que se agregaron
        orden_codigos = [c.strip().lower() for c in request.POST.getlist('paso_orden_codigo') if c.strip()]
        for idx, pcod in enumerate(orden_codigos):
            ok_pp, err_pp = _enlazar_paso_a_proceso(codigo, pcod, idx + 1)
            if not ok_pp:
                errores_post.append(f'Vincular paso {pcod}: {err_pp}')

        # 3. Piezas requeridas
        for i, zcod in enumerate(piezas_codigo):
            zcod = zcod.strip()
            if not zcod:
                continue
            cant = piezas_cantidad[i] if i < len(piezas_cantidad) else 0
            ok_z, err_z = _asignar_pieza_a_plantilla(codigo, zcod, int(cant or 0))
            if not ok_z:
                errores_post.append(f'Pieza {zcod}: {err_z}')

        if errores_post:
            messages.error(request, 'Plantilla creada con errores: ' + '; '.join(errores_post))
        else:
            messages.success(request, 'Plantilla creada.')
    return _organizacion_redirect('plantillas')


def admin_organizacion_plantilla_editar(request, pk):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()

        errores = []
        if not nombre:
            errores.append('El nombre de la plantilla es obligatorio.')
        elif len(nombre) > 20:
            errores.append('El nombre no puede tener más de 20 caracteres.')
        if not descripcion:
            errores.append('La descripción de la plantilla es obligatoria.')
        elif len(descripcion) > 80:
            errores.append('La descripción no puede tener más de 80 caracteres.')

        if not errores and nombre:
            procesos_bd = _get('/v1/list/Proceso/', [])
            if any(str(p.get('nombre', '')).strip().lower() == nombre.lower() and str(p.get('codigo')) != str(pk) for p in procesos_bd):
                errores.append(f'Ya existe una plantilla con el nombre "{nombre}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return _organizacion_redirect('plantillas', pk)

        ok, resp = _patch(f'/v1/update/Proceso/{pk}/', {
            'nombre':      nombre,
            'descripcion': descripcion,
        })
        if ok:
            messages.success(request, 'Plantilla actualizada.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('plantillas', pk)


def admin_organizacion_plantilla_paso_asignar(request, pk):
    if request.method == 'POST':
        paso_codigo = request.POST.get('paso', '').strip().lower()
        nuevo_codigo = request.POST.get('paso_nuevo_codigo', '').strip().lower()
        nuevo_nombre = request.POST.get('paso_nuevo_nombre', '').strip()
        nuevo_desc = request.POST.get('paso_nuevo_descripcion', '').strip()
        minutos = request.POST.get('paso_nuevo_tiempo', '').strip()

        if not paso_codigo and not nuevo_codigo:
            messages.error(request, 'Selecciona un paso existente o crea uno nuevo.')
            return _organizacion_redirect('plantillas', pk)

        if nuevo_codigo:
            errores = []
            if len(nuevo_codigo) > 5 or not _CODIGO_RE.match(nuevo_codigo):
                errores.append('El código del nuevo paso no es válido (máx. 5 caracteres, minúsculas/números/guiones).')
            if not nuevo_nombre:
                errores.append('El nombre del nuevo paso es obligatorio.')
            elif len(nuevo_nombre) > 20:
                errores.append('El nombre del nuevo paso no puede tener más de 20 caracteres.')
            if not nuevo_desc:
                errores.append('La descripción del nuevo paso es obligatoria.')
            elif len(nuevo_desc) > 80:
                errores.append('La descripción del nuevo paso no puede tener más de 80 caracteres.')
            if not minutos or not minutos.isdigit() or int(minutos) < 1:
                errores.append('El tiempo estimado es obligatorio y debe ser un número mayor a 0.')

            if not errores:
                pasos_bd = _get('/v1/list/pasos/', [])
                if any(str(p.get('codigo', '')).lower() == nuevo_codigo for p in pasos_bd):
                    errores.append(f'Ya existe un paso con el código "{nuevo_codigo}".')

            if errores:
                for e in errores:
                    messages.error(request, e)
                return _organizacion_redirect('plantillas', pk)

            ok_p, resp_p = _post('/v1/create/Paso/', {
                'codigo':         nuevo_codigo,
                'nombre':         nuevo_nombre,
                'descripcion':    nuevo_desc,
                'tiempoEstimado': _duracion_str(int(minutos) * 60),
            })
            if not ok_p:
                messages.error(request, f'Error al crear el paso: {resp_p}')
                return _organizacion_redirect('plantillas', pk)
            paso_codigo = nuevo_codigo

        pasos_proceso = _get('/v1/list/PasoProceso/', [])
        orden = sum(1 for pp in pasos_proceso if str(pp.get('proceso')) == str(pk)) + 1
        ok, err = _enlazar_paso_a_proceso(pk, paso_codigo, orden)
        if ok:
            messages.success(request, 'Paso agregado a la plantilla.')
        else:
            messages.error(request, err)
    return _organizacion_redirect('plantillas', pk)


def admin_organizacion_plantilla_paso_quitar(request, rel_pk):
    proceso_pk = request.POST.get('proceso', '') if request.method == 'POST' else ''
    if request.method == 'POST':
        ok, resp = _delete(f'/v1/delete/PasoProceso/{rel_pk}/')
        if ok:
            messages.success(request, 'Paso quitado de la plantilla.')
        else:
            messages.error(request, f'Error al quitar el paso: {resp}')
    return _organizacion_redirect('plantillas', proceso_pk)


def admin_organizacion_plantilla_pieza_asignar(request, pk):
    if request.method == 'POST':
        pieza_codigo = request.POST.get('pieza', '').strip()
        cantidad = request.POST.get('cantidad', '').strip()

        if not pieza_codigo:
            messages.error(request, 'Selecciona una pieza.')
            return _organizacion_redirect('plantillas', pk)
        if not cantidad.isdigit() or int(cantidad or 0) < 1:
            messages.error(request, 'La cantidad debe ser un número mayor a 0.')
            return _organizacion_redirect('plantillas', pk)

        ok, err = _asignar_pieza_a_plantilla(pk, pieza_codigo, int(cantidad))
        if ok:
            messages.success(request, 'Pieza asignada a la plantilla.')
        else:
            messages.error(request, err)
    return _organizacion_redirect('plantillas', pk)


def admin_organizacion_plantilla_pieza_quitar(request, rel_pk):
    proceso_pk = request.POST.get('proceso', '') if request.method == 'POST' else ''
    if request.method == 'POST':
        ok, resp = _delete(f'/v1/delete/ProcesoPieza/{rel_pk}/')
        if ok:
            messages.success(request, 'Pieza quitada de la plantilla.')
        else:
            messages.error(request, f'Error al quitar la pieza: {resp}')
    return _organizacion_redirect('plantillas', proceso_pk)


def admin_organizacion_oblea_crear(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().lower()
        nombre = request.POST.get('nombre', '').strip()
        dies_raw = request.POST.get('dies_maximos', '').strip()

        errores = []
        if not codigo:
            errores.append('El código es obligatorio.')
        elif len(codigo) > 5:
            errores.append('El código no puede tener más de 5 caracteres.')
        elif not _CODIGO_RE.match(codigo):
            errores.append('El código solo puede tener letras minúsculas, números y guiones.')

        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 25:
            errores.append('El nombre no puede tener más de 25 caracteres.')

        if not dies_raw.isdigit() or int(dies_raw or 0) < 1:
            errores.append('La cantidad de dies debe ser un número mayor a 0.')

        if not errores:
            tipos_bd = _get('/v1/list/TipoOblea/', [])
            if any(str(t.get('codigo', '')).lower() == codigo for t in tipos_bd):
                errores.append(f'Ya existe un tipo de oblea con el código "{codigo}".')
            if any(str(t.get('cantidadDies', '')) == dies_raw for t in tipos_bd):
                errores.append(f'Ya existe un tipo de oblea con {dies_raw} dies.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return _organizacion_redirect('obleas')

        ok, resp = _post('/v1/create/TipoOblea/', {
            'codigo':       codigo,
            'descripcion':  nombre,
            'cantidadDies': int(dies_raw),
        })
        if ok:
            messages.success(request, 'Tipo de oblea creado.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('obleas')


def admin_organizacion_oblea_editar(request, pk):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        dies_raw = request.POST.get('dies_maximos', '').strip()

        errores = []
        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 25:
            errores.append('El nombre no puede tener más de 25 caracteres.')

        if not dies_raw.isdigit() or int(dies_raw or 0) < 1:
            errores.append('La cantidad de dies debe ser un número mayor a 0.')

        if not errores:
            tipos_bd = _get('/v1/list/TipoOblea/', [])
            if any(str(t.get('cantidadDies', '')) == dies_raw and str(t.get('codigo')) != str(pk) for t in tipos_bd):
                errores.append(f'Ya existe un tipo de oblea con {dies_raw} dies.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return _organizacion_redirect('obleas')

        ok, resp = _patch(f'/v1/update/TipoOblea/{pk}/', {
            'descripcion':  nombre,
            'cantidadDies': int(dies_raw),
        })
        if ok:
            messages.success(request, 'Tipo de oblea actualizado.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('obleas')


def admin_organizacion_linea_crear(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().lower()
        nombre = request.POST.get('nombre', '').strip()
        proceso = request.POST.get('proceso', '').strip()

        errores = []
        if not codigo:
            errores.append('El código es obligatorio.')
        elif len(codigo) > 5:
            errores.append('El código no puede tener más de 5 caracteres.')
        elif not _CODIGO_RE.match(codigo):
            errores.append('El código solo puede tener letras minúsculas, números y guiones.')

        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 20:
            errores.append('El nombre no puede tener más de 20 caracteres.')

        if not errores:
            lineas_bd = _get('/v1/list/Linea/', [])
            if any(str(l.get('codigo', '')).lower() == codigo for l in lineas_bd):
                errores.append(f'Ya existe una línea con el código "{codigo}".')
            if nombre and any(str(l.get('nombre', '')).strip().lower() == nombre.lower() for l in lineas_bd):
                errores.append(f'Ya existe una línea con el nombre "{nombre}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return _organizacion_redirect('lineas')

        ok, resp = _post('/v1/create/Linea/', {
            'codigo':  codigo,
            'nombre':  nombre,
        })
        if not ok:
            messages.error(request, f'Error: {resp}')
            return _organizacion_redirect('lineas')

        ok, error, proceso_nombre = _asignar_proceso_a_linea(codigo, proceso)
        if not ok:
            messages.error(request, error)
        elif proceso_nombre:
            messages.success(request, f'Línea "{nombre}" creada — proceso "{proceso_nombre}" asignado.')
        else:
            messages.success(request, f'Línea "{nombre}" creada.')
    return _organizacion_redirect('lineas')


def admin_organizacion_linea_editar(request, pk):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        proceso = request.POST.get('proceso', '').strip()

        errores = []
        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 20:
            errores.append('El nombre no puede tener más de 20 caracteres.')

        if not errores and nombre:
            lineas_bd = _get('/v1/list/Linea/', [])
            if any(str(l.get('nombre', '')).strip().lower() == nombre.lower() and str(l.get('codigo')) != str(pk) for l in lineas_bd):
                errores.append(f'Ya existe una línea con el nombre "{nombre}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return _organizacion_redirect('lineas')

        ok, resp = _patch(f'/v1/update/Linea/{pk}/', {
            'nombre': nombre,
        })
        if not ok:
            messages.error(request, f'Error: {resp}')
            return _organizacion_redirect('lineas')

        ok, error, proceso_nombre = _asignar_proceso_a_linea(pk, proceso)
        if not ok:
            messages.error(request, error)
        elif proceso_nombre:
            messages.success(request, f'Línea "{nombre}" actualizada — proceso "{proceso_nombre}" asignado.')
        else:
            messages.success(request, f'Línea "{nombre}" actualizada — sin proceso asignado.')
    return _organizacion_redirect('lineas')


def admin_organizacion_paso_crear(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().lower()
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        minutos = request.POST.get('tiempo_estimado', '').strip()
        maquinas_codigos = [m for m in request.POST.getlist('maquina_codigo') if m]

        errores = []
        if not codigo:
            errores.append('El código es obligatorio.')
        elif len(codigo) > 5:
            errores.append('El código no puede tener más de 5 caracteres.')
        elif not _CODIGO_RE.match(codigo):
            errores.append('El código solo puede tener letras minúsculas, números y guiones.')

        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 20:
            errores.append('El nombre no puede tener más de 20 caracteres.')

        if not descripcion:
            errores.append('La descripción es obligatoria.')
        elif len(descripcion) > 80:
            errores.append('La descripción no puede tener más de 80 caracteres.')

        if not minutos or not minutos.isdigit() or int(minutos) < 1:
            errores.append('El tiempo estimado es obligatorio y debe ser un número mayor a 0.')

        if not maquinas_codigos:
            errores.append('Asigna al menos una máquina a este paso.')

        if not errores:
            pasos_bd = _get('/v1/list/pasos/', [])
            if any(str(p.get('codigo', '')).lower() == codigo for p in pasos_bd):
                errores.append(f'Ya existe un paso con el código "{codigo}".')
            if nombre and any(str(p.get('nombre', '')).strip().lower() == nombre.lower() for p in pasos_bd):
                errores.append(f'Ya existe un paso con el nombre "{nombre}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return _organizacion_redirect('pasos')

        ok, resp = _post('/v1/create/Paso/', {
            'codigo':         codigo,
            'nombre':         nombre,
            'descripcion':    descripcion,
            'tiempoEstimado': _duracion_str(int(minutos) * 60),
        })
        if ok:
            for maquina_codigo in maquinas_codigos:
                _post('/v1/create/MaquinaPaso/', {'maquina': maquina_codigo, 'paso': codigo})
            messages.success(request, 'Paso creado.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('pasos')


def admin_organizacion_paso_editar(request, pk):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        minutos = request.POST.get('tiempo_estimado', '').strip()
        maquinas_codigos = [m for m in request.POST.getlist('maquina_codigo') if m]

        errores = []
        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 20:
            errores.append('El nombre no puede tener más de 20 caracteres.')

        if not descripcion:
            errores.append('La descripción es obligatoria.')
        elif len(descripcion) > 80:
            errores.append('La descripción no puede tener más de 80 caracteres.')

        if minutos and not minutos.isdigit():
            errores.append('El tiempo estimado debe ser un número.')

        if not maquinas_codigos:
            errores.append('Asigna al menos una máquina a este paso.')

        if not errores and nombre:
            pasos_bd = _get('/v1/list/pasos/', [])
            if any(str(p.get('nombre', '')).strip().lower() == nombre.lower() and str(p.get('codigo')) != str(pk) for p in pasos_bd):
                errores.append(f'Ya existe un paso con el nombre "{nombre}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return _organizacion_redirect('pasos')

        ok, resp = _patch(f'/v1/update/Paso/{pk}/', {
            'nombre':         nombre,
            'descripcion':    descripcion,
            'tiempoEstimado': _duracion_str(int(minutos or 0) * 60),
        })
        if ok:
            # Sincroniza las máquinas asignadas: borra las que ya no vengan
            # marcadas y crea las nuevas — más simple que ir comparando
            # altas/bajas una por una desde el JS.
            maquina_paso_bd = _get('/v1/list/MaquinaPaso/', [])
            relaciones_actuales = [mp for mp in maquina_paso_bd if str(mp.get('paso', '')) == str(pk)]
            actuales_por_maquina = {str(mp.get('maquina', '')): mp.get('id') for mp in relaciones_actuales}
            for maquina_codigo, rel_pk in actuales_por_maquina.items():
                if maquina_codigo not in maquinas_codigos:
                    _delete(f'/v1/delete/MaquinaPaso/{rel_pk}/')
            for maquina_codigo in maquinas_codigos:
                if maquina_codigo not in actuales_por_maquina:
                    _post('/v1/create/MaquinaPaso/', {'maquina': maquina_codigo, 'paso': pk})
            messages.success(request, 'Paso actualizado.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('pasos')


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — PRODUCCIÓN (órdenes, lotes, hold, scrap)
# ════════════════════════════════════════════════════════════════

def supervisor_ordenes(request):
    ordenes_bd, obleas_bd, procesos_bd, lineas_bd, tipos_oblea_bd, _alertas_bd, linea_proceso_bd, empleados_bd = _get_many(
        '/v1/list/Orden/',
        '/v1/list/Oblea/',
        '/v1/list/Proceso/',
        '/v1/list/Linea/',
        '/v1/list/TipoOblea/',
        '/v1/list/alertas/',
        '/v1/list/LineaProceso/',
        '/v1/list/empleados/',
    )
    proceso_por_linea = {str(lp.get('linea')): str(lp.get('proceso')) for lp in linea_proceso_bd}
    # recent_notifications/unread_count del topbar los pone el context
    # processor home.context_processors.notificaciones para toda la app.
    ctx = {
        'user_role': 'Supervisor',
        'breadcrumbs': [],
        'backend_url': BACKEND_URL,
    }

    procesos_map = {str(p.get('codigo', '')): p for p in procesos_bd}
    lineas_map   = {str(l.get('codigo', '')): l for l in lineas_bd}
    tipos_map    = {str(t.get('codigo', '')): t for t in tipos_oblea_bd}
    empleados_map = {str(e.get('numero', '')): e for e in empleados_bd}

    # Construir lista de órdenes con los campos que espera supervisor/ordenes.html
    ordenes = []
    for o in ordenes_bd:
        num   = o.get('numero')
        obs   = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
        total = len(obs)
        en_proc = sum(1 for ob in obs if str(ob.get('estado', '')).lower() == 'proce')
        edo_str, comp, pct, terminados, rechazados = _estado_orden_display(o.get('estado'), obs)

        # proceso como FakeObj para que template acceda a orden.proceso.nombre
        proceso_codigo = str(o.get('proceso', ''))
        proceso_data   = procesos_map.get(proceso_codigo, {})
        proceso_obj    = _FakeObj(pk=proceso_codigo, nombre=proceso_data.get('nombre', proceso_codigo))

        linea_pk = str(o.get('linea', '')) if o.get('linea') else ''
        tipo_pk  = str(o.get('tipoOblea', '')) if o.get('tipoOblea') else ''
        creador  = empleados_map.get(str(o.get('empleado', '')), {})
        creador_nombre = f"{creador.get('nombre', '')} {creador.get('primerApell', '')}".strip() or '—'

        ordenes.append({
            'pk':               num,
            'numero':           f'ORD-{num:04d}' if isinstance(num, int) else str(num),
            'proceso':          proceso_obj,
            'linea_pk':         linea_pk,
            'linea_nombre':     lineas_map.get(linea_pk, {}).get('nombre', '—') if linea_pk else '—',
            'tipo_oblea_pk':    tipo_pk,
            'tipo_oblea_nombre': tipos_map.get(tipo_pk, {}).get('descripcion', '—') if tipo_pk else '—',
            'fecha_inicio':     str(o.get('horaIni', '—'))[:10],
            'fecha_fin':        str(o.get('horaFin', '—'))[:10],
            'fecha_inicio_display': _fecha_display(o.get('horaIni', '')),
            'fecha_fin_display':    _fecha_display(o.get('horaFin', '')),
            'fecha_creacion_display': _fecha_display(o.get('fecha', '')),
            'hora_inicio':      _hora_display(o.get('horaIni', '')),
            'hora_fin':         _hora_display(o.get('horaFin', '')),
            'creado_por':       creador_nombre,
            'total_lotes':      total,
            'lotes_completados': comp,
            'lotes_terminados': terminados,
            'lotes_rechazados': rechazados,
            'lotes_en_proceso': en_proc,
            'pct_completados':  pct,
            'estado':           edo_str,
            'estado_pk':        str(o.get('estado', '')),
            'tiene_hold':       any(str(ob.get('estado', '')).lower() == 'enhol' for ob in obs),
        })

    lineas_activas = [
        {'pk': l.get('codigo'), 'nombre': l.get('nombre', ''),
         'proceso_pk': proceso_por_linea.get(str(l.get('codigo', ''))),
         'proceso_nombre': procesos_map.get(proceso_por_linea.get(str(l.get('codigo', '')), ''), {}).get('nombre', '')}
        for l in lineas_bd
        if proceso_por_linea.get(str(l.get('codigo', '')))
    ]
    tipos_oblea_activos = [
        {'pk': t.get('codigo'), 'nombre': t.get('descripcion', '')}
        for t in tipos_oblea_bd
    ]

    ordenes_json_data = [
        {
            'pk':            o['pk'],
            'numero':        o['numero'],
            'linea_pk':      o['linea_pk'],
            'tipo_oblea_pk': o['tipo_oblea_pk'],
            'fecha_inicio':  o['fecha_inicio'],
            'fecha_fin':     o['fecha_fin'],
            'estado_pk':     o['estado_pk'],
            'total_lotes':   o['total_lotes'],
        }
        for o in ordenes
    ]

    # Filtro + paginación server-side (mismo patrón que admin_produccion) —
    # "ordenes" completo se conserva para ordenes_json_data, que el JS usa
    # para abrir el detalle de cualquier orden sin importar la página.
    q = request.GET.get('q', '').strip().lower()
    estado_filtro = request.GET.get('estado', '').strip()
    ordenes_filtradas = ordenes
    if q:
        ordenes_filtradas = [o for o in ordenes_filtradas if q in str(o.get('numero', '')).lower()]
    if estado_filtro:
        ordenes_filtradas = [o for o in ordenes_filtradas if o.get('estado') == estado_filtro]
    ordenes_page = Paginator(ordenes_filtradas, PAGE_SIZE_PRODUCCION).get_page(request.GET.get('page', 1))
    produccion_extra_params = urlencode({k: v for k, v in {'q': q, 'estado': estado_filtro}.items() if v})
    if produccion_extra_params:
        produccion_extra_params += '&'

    ctx.update({
        'ordenes_page':      ordenes_page,
        'produccion_extra_params': produccion_extra_params,
        'q':                 q,
        'estado_filtro':     estado_filtro,
        'ordenes_json_data': ordenes_json_data,
        'lineas':            lineas_activas,
        'tipos_oblea':       tipos_oblea_activos,
        'stock_insuficiente': request.session.pop('stock_insuficiente', None),
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Órdenes',   'url': '/supervisor/ordenes/'},
        ],
    })
    return render(request, 'supervisor/ordenes.html', ctx)


def supervisor_ordenes_crear(request):
    if request.method == 'POST':
        _crear_orden(request)
    return redirect('supervisor_ordenes')


def supervisor_lotes_max_stock(request):
    proceso_pk = request.GET.get('proceso', '') or _get_linea_proceso(request.GET.get('linea', ''))
    lotes_max = _lotes_max_por_stock(proceso_pk, request.GET.get('tipo_oblea', ''))
    return JsonResponse({'lotes_max': lotes_max})


def supervisor_orden_editar(request, pk):
    if request.method == 'POST':
        _editar_orden(request, pk)
    return redirect('supervisor_ordenes')


def supervisor_lotes(request):
    return redirect('supervisor_ordenes')


def supervisor_lote_registrar(request):
    orden_pk = request.POST.get('orden_id', '') if request.method == 'POST' else None
    if request.method == 'POST':
        _agregar_lotes(request)
    if orden_pk:
        return redirect('supervisor_orden_detalle', pk=orden_pk)
    return redirect('supervisor_ordenes')


def supervisor_lote_hold(request, pk):
    if request.method == 'POST':
        _lote_hold(request, pk)
    return redirect('supervisor_ordenes')


def supervisor_lote_liberar(request, pk):
    if request.method == 'POST':
        _lote_liberar(request, pk)
    return redirect('supervisor_lote_detalle', pk=pk)


def supervisor_lote_rechazar_liberando_orden(request, pk):
    """Misma acción que supervisor_orden_liberar_rechazando_lote, pero
    llamada desde la trazabilidad del propio lote — resuelve la orden a
    partir del lote en vez de recibirla en la URL."""
    ob = _get(f'/v1/detail/Oblea/{pk}/') or {}
    orden_pk = ob.get('orden')
    if request.method == 'POST' and orden_pk:
        _orden_liberar_rechazando_lote(request, orden_pk, pk)
    return redirect('supervisor_lote_detalle', pk=pk)


def supervisor_orden_liberar(request, pk):
    if request.method == 'POST':
        _orden_liberar(request, pk)
    return redirect('supervisor_orden_detalle', pk=pk)

def supervisor_orden_rechazar(request, pk):
    if request.method == 'POST':
        _orden_rechazar(request, pk)
    return redirect('supervisor_orden_detalle', pk=pk)

def supervisor_orden_liberar_rechazando_lote(request, pk, lote_pk):
    if request.method == 'POST':
        _orden_liberar_rechazando_lote(request, pk, lote_pk)
    return redirect('supervisor_orden_detalle', pk=pk)


def supervisor_orden_generar_reporte(request, pk):
    if request.method == 'POST':
        _generar_reporte_manual(request, pk, reportes_url_name='supervisor_reportes')
    return redirect('supervisor_orden_detalle', pk=pk)


def supervisor_lote_generar_reporte(request, pk):
    orden_pk = request.POST.get('orden_id', '') if request.method == 'POST' else None
    if request.method == 'POST':
        _generar_reporte_manual(request, orden_pk, oblea_num=pk, reportes_url_name='supervisor_reportes')
    return redirect('supervisor_lote_detalle', pk=pk)


def supervisor_lote_scrap(request, pk):
    if request.method == 'POST':
        _lote_scrap(request, pk)
    return redirect('supervisor_ordenes')


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — DETALLE DE ORDEN Y LOTE (vistas propias)
# ════════════════════════════════════════════════════════════════

def supervisor_orden_detalle(request, pk):
    (ordenes_bd, obleas_bd, procesos_bd, lineas_bd, tipos_oblea_bd,
     pasos_bd, pasos_catalogo, pasos_realizados_bd, _alertas_bd, empleados_bd) = _get_many(
        '/v1/list/Orden/',
        '/v1/list/Oblea/',
        '/v1/list/Proceso/',
        '/v1/list/Linea/',
        '/v1/list/TipoOblea/',
        '/v1/list/PasoProceso/',
        '/v1/list/pasos/',
        '/v1/list/PasoRealizado/',
        '/v1/list/alertas/',
        '/v1/list/empleados/',
    )
    # recent_notifications/unread_count del topbar los pone el context
    # processor home.context_processors.notificaciones para toda la app.
    ctx = {
        'user_role': 'Supervisor',
        'breadcrumbs': [],
        'backend_url': BACKEND_URL,
    }

    orden_data = next((o for o in ordenes_bd if str(o.get('numero')) == str(pk)), {})
    if not orden_data:
        # _get_many pudo haber fallado en ESTA lista puntual (timeout,
        # hipo de red) sin que las demás fallaran — antes de asumir que la
        # orden no existe y mandar al usuario a la lista (interrumpiendo un
        # simple refresh de la página), dar una segunda oportunidad con una
        # consulta directa al registro.
        orden_data = _get(f'/v1/detail/Orden/{pk}/') or {}
        if not orden_data:
            return redirect('supervisor_ordenes')

    num    = orden_data.get('numero')
    obs    = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
    total  = len(obs)
    en_proc = sum(1 for ob in obs if str(ob.get('estado', '')).lower() == 'proce')

    proceso_codigo = str(orden_data.get('proceso', ''))
    proceso_data   = next((p for p in procesos_bd if str(p.get('codigo')) == proceso_codigo), {})
    proceso_obj    = _FakeObj(pk=proceso_codigo, nombre=proceso_data.get('nombre', proceso_codigo))

    catalogo_map = {str(p.get('codigo', '')): p for p in pasos_catalogo}
    pasos_de_proceso = sorted(
        [p for p in pasos_bd if str(p.get('proceso')) == proceso_codigo],
        key=lambda x: x.get('orden', 0)
    )

    linea_pk = str(orden_data.get('linea', '')) if orden_data.get('linea') else ''
    linea_data = next((l for l in lineas_bd if str(l.get('codigo')) == linea_pk), {})
    tipo_pk = str(orden_data.get('tipoOblea', '')) if orden_data.get('tipoOblea') else ''
    tipo_data = next((t for t in tipos_oblea_bd if str(t.get('codigo')) == tipo_pk), {})

    edo_str, comp, _pct, terminados, rechazados = _estado_orden_display(orden_data.get('estado'), obs)

    creador = next((e for e in empleados_bd if str(e.get('numero')) == str(orden_data.get('empleado', ''))), {})
    creador_nombre = f"{creador.get('nombre', '')} {creador.get('primerApell', '')}".strip() or '—'

    orden = {
        'pk':               num,
        'numero':           f'ORD-{num:04d}' if isinstance(num, int) else str(num),
        'proceso':          proceso_obj,
        'linea_nombre':     linea_data.get('nombre', '—'),
        'tipo_oblea_nombre': tipo_data.get('descripcion', '—'),
        'creado_por':       creador_nombre,
        'fecha_creacion_display': _fecha_display(orden_data.get('fecha', '')),
        'total_lotes':      total,
        'lotes_completados': comp,
        'lotes_terminados': terminados,
        'lotes_rechazados': rechazados,
        'lotes_en_proceso': en_proc,
        'estado':           edo_str,
        'estado_pk':        str(orden_data.get('estado', '')),
    }

    lotes = []
    lotes_candidatos_liberar = []
    for ob in obs:
        ob_num = ob.get('numero')
        edo_ob = str(ob.get('estado', '')).lower()
        realizados_de_esta_oblea = {
            str(pr.get('paso', '')): pr
            for pr in pasos_realizados_bd
            if str(pr.get('oblea', '')) == str(ob_num)
        }
        etapas = _construir_etapas(pasos_de_proceso, catalogo_map, realizados_de_esta_oblea)
        etapa_en_curso = next((e for e in etapas if e['estado'] == 'en_curso'), None)
        etapa_nombre = etapa_en_curso['nombre'] if etapa_en_curso else ('Completado' if etapas else '—')
        dies_iniciales = tipo_data.get('cantidadDies') or ob.get('diesGenerados', 0)
        dies_activos, scrap_total, yield_pct = _calcular_yield(
            ob_num, pasos_realizados_bd, dies_iniciales, ob.get('diesGenerados', 0)
        )
        folio = f'LOT-{ob_num:04d}' if isinstance(ob_num, int) else str(ob_num)
        lotes.append({
            'pk':            ob_num,
            'folio':         folio,
            'numero_oblea':  ob_num,
            'dies_buenos':   dies_iniciales,
            'dies_activos':  dies_activos,
            'scrap':         scrap_total,
            'etapa_actual':  _FakeObj(nombre=etapa_nombre),
            'estado':        _FakeObj(nombre=ESTADOS_OBLEA_LABEL.get(edo_ob, edo_ob.capitalize())),
            'yield_pct':     yield_pct,
        })
        if edo_ob in ('proce', 'enhol') and yield_pct is not None and yield_pct < 95:
            lotes_candidatos_liberar.append({'pk': ob_num, 'folio': folio, 'yield_pct': yield_pct})

    ctx.update({
        'orden': orden,
        'lotes': lotes,
        'lotes_candidatos_liberar': lotes_candidatos_liberar if orden['estado_pk'] == 'enhol' else [],
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Órdenes',   'url': '/supervisor/ordenes/'},
            {'label': orden['numero'], 'url': ''},
        ],
    })
    return render(request, 'supervisor/orden_detalle.html', ctx)


def supervisor_lote_detalle(request, pk):
    (obleas_bd, ordenes_bd, pasos_bd, pasos_catalogo, pasos_realizados,
     defectos_bd, paso_defecto_bd, _alertas_bd, tipos_oblea_bd,
     procesos_bd, proceso_pieza_bd, piezas_bd, lineas_bd) = _get_many(
        '/v1/list/Oblea/',
        '/v1/list/Orden/',
        '/v1/list/PasoProceso/',
        '/v1/list/pasos/',
        '/v1/list/PasoRealizado/',
        '/v1/list/Defecto/',
        '/v1/list/PasoDefecto/',
        '/v1/list/alertas/',
        '/v1/list/TipoOblea/',
        '/v1/list/Proceso/',
        '/v1/list/ProcesoPieza/',
        '/v1/list/piezas/',
        '/v1/list/Linea/',
    )
    procesos_map = {str(p.get('codigo', '')): p for p in procesos_bd}
    piezas_por_proceso = _piezas_por_proceso_map(proceso_pieza_bd, piezas_bd)
    lineas_map = {str(l.get('codigo', '')): l for l in lineas_bd}
    operador_por_paso = _operador_por_paso()
    # recent_notifications/unread_count del topbar los pone el context
    # processor home.context_processors.notificaciones para toda la app.
    ctx = {
        'user_role': 'Supervisor',
        'breadcrumbs': [],
        'backend_url': BACKEND_URL,
    }

    ob = next((o for o in obleas_bd if str(o.get('numero')) == str(pk)), {})
    if not ob:
        # Mismo caso que supervisor_orden_detalle: dar una segunda
        # oportunidad con una consulta directa antes de mandar a la lista.
        ob = _get(f'/v1/detail/Oblea/{pk}/') or {}
        if not ob:
            return redirect('supervisor_ordenes')

    num       = ob.get('numero')
    orden_num = ob.get('orden')
    orden_data = next((o for o in ordenes_bd if str(o.get('numero')) == str(orden_num)), {})

    proceso_codigo   = str(orden_data.get('proceso', ''))
    pasos_de_proceso = sorted(
        [p for p in pasos_bd if str(p.get('proceso')) == proceso_codigo],
        key=lambda x: x.get('orden', 0)
    )

    # Mapa codigo_paso → tiempo estimado en segundos (del catálogo de pasos)
    catalogo_map = {str(p.get('codigo', '')): p for p in pasos_catalogo}

    # Mapa codigo_paso → paso_realizado de esta oblea
    realizados_map = {
        str(pr.get('paso', '')): pr
        for pr in pasos_realizados
        if str(pr.get('oblea', '')) == str(num)
    }

    etapas_raw = _construir_etapas(pasos_de_proceso, catalogo_map, realizados_map, _maquinas_por_paso())

    etapas = []
    etapa_activa = None
    for e in etapas_raw:
        etapa = _FakeObj(
            codigo=e['codigo'],
            nombre=e['nombre'],
            descripcion=e['descripcion'],
            completado=e['estado'] in ('aprobado', 'rechazado'),
            rechazado=e['estado'] == 'rechazado',
            activo=e['estado'] == 'en_curso',
            maquina=e['maquina_nombre'] or 'Sin máquina asignada',
            scrap=e['scrap'],
            notas=e['meta'] or '',
            tiempo_estimado_seg=e['tiempo_estimado_seg'],
            hora_inicio_iso=e['hora_inicio_iso'],
        )
        etapas.append(etapa)
        if etapa.activo:
            etapa_activa = etapa

    edo    = str(ob.get('estado', '')).lower()
    edo_str = ESTADOS_OBLEA_LABEL.get(edo, edo.capitalize())

    tipo_pk   = str(orden_data.get('tipoOblea', '')) if orden_data.get('tipoOblea') else ''
    tipo_data = next((t for t in tipos_oblea_bd if str(t.get('codigo')) == tipo_pk), {})
    dies_iniciales = tipo_data.get('cantidadDies') or ob.get('diesGenerados', 0)
    dies_activos, scrap_total, _yield_pct_py = _calcular_yield(
        num, pasos_realizados, dies_iniciales, ob.get('diesGenerados', 0)
    )
    yield_pct = _calcular_yield_sp(num)

    proceso_nombre = procesos_map.get(proceso_codigo, {}).get('nombre', proceso_codigo or '—')
    total_pasos_lote = len(etapas)
    pasos_completados_lote = sum(1 for e in etapas if e.completado)
    lote_linea_pk = str(orden_data.get('linea', '')) if orden_data.get('linea') else ''

    lote = {
        'pk':             num,
        'folio':          f'LOT-{num:04d}' if isinstance(num, int) else str(num),
        'orden':          _FakeObj(
                              pk=orden_num,
                              numero=f'ORD-{orden_num:04d}' if isinstance(orden_num, int) else str(orden_num)
                          ) if orden_data else None,
        'estado':         _FakeObj(nombre=edo_str),
        'orden_en_hold':  str(orden_data.get('estado', '')).lower() == 'enhol',
        'orden_rechazada': str(orden_data.get('estado', '')).lower() == 'recha',
        'proceso_nombre': proceso_nombre,
        'linea_nombre':   lineas_map.get(lote_linea_pk, {}).get('nombre', '—') if lote_linea_pk else '—',
        'operador_nombre': operador_por_paso.get(etapa_activa.codigo, '—') if etapa_activa else '—',
        'piezas':         piezas_por_proceso.get(proceso_codigo, []),
        'dies_iniciales': dies_iniciales,
        'dies_activos':   dies_activos,
        'scrap_total':    scrap_total,
        'yield_pct':      yield_pct,
        'etapas':         etapas,
        'etapa_activa':   etapa_activa,
        'total_pasos':         total_pasos_lote,
        'pasos_completados':   pasos_completados_lote,
        'pct_completados':     round(pasos_completados_lote / total_pasos_lote * 100) if total_pasos_lote else 0,
    }

    defectos_map = {str(d.get('codigo')): d for d in defectos_bd if d.get('activo', True)}
    codigos_defecto_paso = {
        str(rel.get('defecto'))
        for rel in paso_defecto_bd
        if etapa_activa and str(rel.get('paso')) == str(etapa_activa.codigo)
    }
    tipos_defecto = [
        {'codigo': cod, 'descripcion': d.get('descripcion', '')}
        for cod, d in defectos_map.items()
        if cod in codigos_defecto_paso
    ]

    ctx.update({
        'lote':          lote,
        'tipos_defecto': tipos_defecto,
        # Bandeja global de respaldo — si el paso activo no tiene defectos
        # propios ligados, se ofrece el catálogo completo en su lugar.
        'defectos_catalogo_json': json.dumps(
            [{'codigo': d.get('codigo'), 'descripcion': d.get('descripcion', '')} for d in defectos_map.values()]
        ),
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Órdenes',   'url': '/supervisor/ordenes/'},
            {'label': lote['folio'], 'url': ''},
        ],
    })
    return render(request, 'supervisor/lote_detalle.html', ctx)


def supervisor_etapa_completar(request, pk):
    """Permite al supervisor completar una etapa desde la vista web."""
    if request.method == 'POST':
        _etapa_completar(request, pk)
    return redirect('supervisor_lote_detalle', pk=pk)