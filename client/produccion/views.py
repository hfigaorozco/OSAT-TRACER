import json
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from home.views import _base_ctx, _get, _get_many, _post, _patch, _delete, _FakeObj

PAGE_SIZE_ORGANIZACION = 9


def _duracion_str(segundos):
    """Convierte segundos a un string que DurationField acepta (formato de str(timedelta))."""
    try:
        return str(timedelta(seconds=int(segundos or 0)))
    except (TypeError, ValueError):
        return '0:00:00'


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


def _get_linea_proceso(linea_pk):
    """Devuelve el código de proceso asignado a una línea, o None."""
    linea = _get(f'/v1/detail/Linea/{linea_pk}/')
    if not linea:
        return None
    return linea.get('proceso')


def _crear_lotes_para_orden(orden_pk, tipo_oblea_pk, cantidad):
    """Crea `cantidad` lotes/obleas para una orden. diesGenerados se hereda de TipoOblea.cantidadDies."""
    if cantidad <= 0:
        return 0, []
    tipo = _get(f'/v1/detail/TipoOblea/{tipo_oblea_pk}/')
    dies = (tipo or {}).get('cantidadDies', 0)
    errores = []
    creados = 0
    for _ in range(cantidad):
        ok, resp = _post('/v1/create/Oblea/', {
            'diesGenerados': dies,
            'orden':         orden_pk,
            'estado':        'proce',
        })
        if ok:
            creados += 1
        else:
            errores.append(str(resp))
    return creados, errores


def _crear_orden(request):
    linea_pk   = request.POST.get('linea', '').strip()
    tipo_oblea = request.POST.get('tipo_oblea', '').strip()
    empleado_pk = request.session.get('user_id')
    cantidad_lotes = int(request.POST.get('cantidad_lotes', 0) or 0)

    if not linea_pk or not tipo_oblea:
        messages.error(request, 'Selecciona línea y tipo de oblea.')
        return
    proceso_pk = _get_linea_proceso(linea_pk)
    if not proceso_pk:
        messages.error(request, 'La línea seleccionada no tiene un proceso asignado.')
        return

    ok, resp = _post('/v1/create/Orden/', {
        'horaIni':   request.POST.get('fecha_inicio', '') + ' 00:00:00',
        'horaFin':   request.POST.get('fecha_fin', '')    + ' 23:59:00',
        'proceso':   proceso_pk,
        'linea':     linea_pk,
        'tipoOblea': tipo_oblea,
        'estado':    'abier',
        'empleado':  empleado_pk,
    })
    if not ok:
        messages.error(request, f'Error: {resp}')
        return

    orden_pk = resp.get('numero') if isinstance(resp, dict) else None
    if cantidad_lotes > 0 and orden_pk:
        creados, errores = _crear_lotes_para_orden(orden_pk, tipo_oblea, cantidad_lotes)
        if errores:
            messages.error(request, f'Orden creada, pero solo {creados} de {cantidad_lotes} lotes se registraron.')
        else:
            messages.success(request, f'Orden creada con {creados} lote(s).')
    else:
        messages.success(request, 'Orden creada.')


def _editar_orden(request, pk):
    linea_pk = request.POST.get('linea', '').strip()
    tipo_oblea = request.POST.get('tipo_oblea', '')
    cantidad_lotes_extra = int(request.POST.get('cantidad_lotes_extra', 0) or 0)
    payload = {
        'horaIni':   request.POST.get('fecha_inicio', '') + ' 00:00:00',
        'horaFin':   request.POST.get('fecha_fin', '')    + ' 23:59:00',
        'tipoOblea': tipo_oblea,
        'estado':    request.POST.get('estado', ''),
    }
    if linea_pk:
        proceso_pk = _get_linea_proceso(linea_pk)
        if not proceso_pk:
            messages.error(request, 'La línea seleccionada no tiene un proceso asignado.')
            return
        payload['linea']   = linea_pk
        payload['proceso'] = proceso_pk

    ok, resp = _patch(f'/v1/update/Orden/{pk}/', payload)
    if not ok:
        messages.error(request, f'Error: {resp}')
        return

    if cantidad_lotes_extra > 0 and tipo_oblea:
        creados, errores = _crear_lotes_para_orden(pk, tipo_oblea, cantidad_lotes_extra)
        if errores:
            messages.error(request, f'Orden actualizada, pero solo se agregaron {creados} de {cantidad_lotes_extra} lotes nuevos.')
        else:
            messages.success(request, f'Orden actualizada y se agregaron {creados} lote(s) nuevo(s).')
    else:
        messages.success(request, 'Orden actualizada.')


def _agregar_lotes(request):
    orden_pk = request.POST.get('orden_id', '').strip()
    cantidad = int(request.POST.get('cantidad_lotes', 0) or 0)
    if not orden_pk or cantidad <= 0:
        messages.error(request, 'Indica cuántos lotes quieres agregar.')
        return
    orden = _get(f'/v1/detail/Orden/{orden_pk}/')
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
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'enhol', 'hold_motivo': motivo})
    if ok:
        messages.success(request, 'Lote puesto en hold.')
    else:
        messages.error(request, f'Error: {resp}')


def _lote_liberar(request, pk):
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'proce'})
    if ok:
        messages.success(request, 'Lote liberado del hold.')
    else:
        messages.error(request, f'Error: {resp}')


def _lote_scrap(request, pk):
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'recha'})
    if ok:
        messages.success(request, 'Lote marcado como rechazado (scrap).')
    else:
        messages.error(request, f'Error: {resp}')


def _etapa_completar(request, pk):
    paso          = request.POST.get('paso', '')
    resultado     = request.POST.get('resultado', 'aprobado')
    observaciones = request.POST.get('observaciones', '')
    unidades_defecto = int(request.POST.get('unidades_defecto', 0) or 0)
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

    messages.success(request, 'Etapa completada correctamente.')
    _avanzar_estado_lote_y_orden(pk)


def _avanzar_estado_lote_y_orden(oblea_pk):
    """
    Tras registrar un Paso_Realizado: si el lote ya tiene TODAS sus etapas
    registradas, avanza su estado real (termi si todo fue aprobado, recha
    si alguna etapa fue rechazada). Y, según cómo queden los lotes de la
    orden, avanza el estado de la orden (abier -> proce -> cerra), siguiendo
    el catálogo real: Estado_Orden abier/proce/cerra, Estado_Oblea proce/termi/recha/enhol.
    No toca lotes en Hold (enhol) — esos requieren resolverse aparte.
    """
    ob = _get(f'/v1/detail/Oblea/{oblea_pk}/')
    if not ob:
        return
    orden_num = ob.get('orden')
    orden = _get(f'/v1/detail/Orden/{orden_num}/')
    if not orden:
        return
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

    edo_orden_actual = str(orden.get('estado', '')).lower()
    if edo_orden_actual == 'abier':
        _patch(f'/v1/update/Orden/{orden_num}/', {'estado': 'proce'})
        edo_orden_actual = 'proce'

    if edo_orden_actual == 'proce' and nuevo_estado_lote:
        obleas_de_orden = [o for o in obleas_bd if str(o.get('orden')) == str(orden_num)]
        for o in obleas_de_orden:
            if str(o.get('numero')) == str(oblea_pk):
                o['estado'] = nuevo_estado_lote
        if obleas_de_orden and all(str(o.get('estado', '')).lower() in ('termi', 'recha') for o in obleas_de_orden):
            _patch(f'/v1/update/Orden/{orden_num}/', {'estado': 'cerra'})


# ── Cálculo de etapas de un lote (mismo criterio que usa la app móvil) ───────

def _construir_etapas(pasos_de_proceso, catalogo_map, pasos_realizados_de_oblea):
    """
    pasos_de_proceso: lista de PasoProceso (dicts) ya ordenados por 'orden'.
    pasos_realizados_de_oblea: dict {codigo_paso: paso_realizado} SOLO de esta oblea.
    Marca completado cada paso con Paso_Realizado propio; el primer paso pendiente
    queda en_curso. No avanza si el paso fue rechazado ('nocom'): se queda visible
    como completado igual (el registro ya existe), consistente con el criterio
    que ya usa el endpoint de la app móvil.
    """
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
            'estado':              estado,
            'meta':                realizado.get('observaciones') if realizado else None,
            'detalle':             None,
            'tiempo_estimado_seg': cat.get('tiempoEstimado', 0),
            'hora_inicio_iso':     str(realizado.get('hora', '') or '') if realizado else '',
        })

    # La primera etapa pendiente pasa a "en_curso"
    for e in etapas:
        if e['estado'] == 'pendiente':
            e['estado'] = 'en_curso'
            break

    return etapas


def _calcular_yield(oblea_num, pasos_realizados_bd, dies_iniciales):
    """Dies activos = dies iniciales - scrap acumulado de cada etapa completada de este lote."""
    scrap_total = sum(
        int(pr.get('scrap', 0) or 0)
        for pr in pasos_realizados_bd
        if str(pr.get('oblea', '')) == str(oblea_num)
    )
    dies_activos = max(0, dies_iniciales - scrap_total)
    yield_pct = round(dies_activos / dies_iniciales * 100, 1) if dies_iniciales > 0 else 0
    return dies_activos, scrap_total, yield_pct


# ── Helper compartido para construir ordenes y lotes ─────────────────────────

def _build_ordenes_lotes():
    (ordenes_bd, obleas_bd, procesos_bd, lineas_bd, tipos_oblea_bd,
     pasos_bd, pasos_catalogo, pasos_realizados_bd, alertas_bd) = _get_many(
        '/v1/list/Orden/',
        '/v1/list/Oblea/',
        '/v1/list/Proceso/',
        '/v1/list/Linea/',
        '/v1/list/TipoOblea/',
        '/v1/list/PasoProceso/',
        '/v1/list/pasos/',
        '/v1/list/PasoRealizado/',
        '/v1/list/alertas/',
    )
    catalogo_map = {str(p.get('codigo', '')): p for p in pasos_catalogo}
    procesos_map = {str(p.get('codigo', '')): p for p in procesos_bd}
    lineas_map   = {str(l.get('codigo', '')): l for l in lineas_bd}
    tipos_map    = {str(t.get('codigo', '')): t for t in tipos_oblea_bd}

    ordenes = []
    for o in ordenes_bd:
        num   = o.get('numero')
        obs   = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
        total = len(obs)
        comp  = sum(1 for ob in obs if str(ob.get('estado', '')).lower() == 'termi')
        pct = round(comp / total * 100) if total > 0 else 0
        edo = str(o.get('estado', '')).lower()
        if edo == 'cerra':
            edo_str = 'aprobado'
        else:
            edo_str = 'en_proceso' if edo == 'proce' else 'pendiente'

        linea_pk = str(o.get('linea', '')) if o.get('linea') else ''
        tipo_pk  = str(o.get('tipoOblea', '')) if o.get('tipoOblea') else ''

        ordenes.append({
            'pk':              num,
            'numero':          f'ORD-{num:04d}' if isinstance(num, int) else str(num),
            'proceso':         str(o.get('proceso', '—')),
            'proceso_nombre':  procesos_map.get(str(o.get('proceso', '')), {}).get('nombre', o.get('proceso', '—')),
            'linea_pk':        linea_pk,
            'linea_nombre':    lineas_map.get(linea_pk, {}).get('nombre', '—') if linea_pk else '—',
            'tipo_oblea_pk':   tipo_pk,
            'tipo_oblea_nombre': tipos_map.get(tipo_pk, {}).get('descripcion', '—') if tipo_pk else '—',
            'fecha_inicio':    str(o.get('horaIni', '—'))[:10],
            'fecha_fin':       str(o.get('horaFin', '—'))[:10],
            'fecha_inicio_display': _fecha_display(o.get('horaIni', '')),
            'fecha_fin_display':    _fecha_display(o.get('horaFin', '')),
            'total_lotes':     total,
            'completados':     comp,
            'pct':             pct,
            'estado':          edo_str,
            'estado_pk':       str(o.get('estado', '')),
            'tiene_hold':      any(str(ob.get('estado', '')).lower() == 'enhol' for ob in obs),
        })

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
        etapas = _construir_etapas(pasos_de_proceso, catalogo_map, realizados_de_esta_oblea)
        pasos_completados = sum(1 for e in etapas if e['estado'] in ('aprobado', 'rechazado'))

        dies_iniciales = ob.get('diesGenerados', 0)
        dies_activos, scrap_total, yield_pct = _calcular_yield(num, pasos_realizados_bd, dies_iniciales)

        lotes.append({
            'pk':                num,
            'folio':             f'LOT-{num:04d}' if isinstance(num, int) else str(num),
            'orden_pk':          orden_num,
            'proceso':           str(orden_data.get('proceso', '—')),
            'fecha_inicio':      str(orden_data.get('horaIni', '—'))[:10],
            'fecha_fin':         str(orden_data.get('horaFin', '—'))[:10],
            'total_pasos':       len(etapas),
            'pasos_completados': pasos_completados,
            'estado':            edo_str,
            'dies_iniciales':    dies_iniciales,
            'dies_activos':      dies_activos,
            'scrap':             scrap_total,
            'yield_pct':         yield_pct,
            'etapas':            etapas,
        })

    plantillas = [
        _FakeObj(pk=p.get('codigo'), nombre=p.get('nombre', ''))
        for p in procesos_bd
    ]
    lineas_activas = [
        {'pk': l.get('codigo'), 'nombre': l.get('nombre', ''), 'proceso_pk': l.get('proceso'),
         'proceso_nombre': procesos_map.get(str(l.get('proceso', '')), {}).get('nombre', '')}
        for l in lineas_bd
        if l.get('activo', True) and l.get('proceso')
    ]
    tipos_oblea_activos = [
        {'pk': t.get('codigo'), 'nombre': t.get('descripcion', '')}
        for t in tipos_oblea_bd
        if t.get('activo', True)
    ]

    return ordenes, lotes, plantillas, lineas_activas, tipos_oblea_activos, alertas_bd


# ════════════════════════════════════════════════════════════════
# ADMIN — PRODUCCIÓN
# ════════════════════════════════════════════════════════════════

def admin_produccion(request):
    ordenes, lotes, plantillas, lineas, tipos_oblea, alertas_bd = _build_ordenes_lotes()
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Administrador',
        'unread_count': unread,
        'recent_notifications': [
            {
                'titulo': a.get('descripcion', ''),
                'tipo': 'alerta',
                'leida': str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre'),
            }
            for a in alertas_bd[:5]
        ],
        'breadcrumbs': [],
    }
    ctx.update({
        'ordenes':              ordenes,
        'lotes':                lotes,
        'plantillas':           plantillas,
        'lineas':               lineas,
        'tipos_oblea':          tipos_oblea,
        'ordenes_json':         json.dumps(ordenes),
        'lotes_json':           json.dumps(lotes),
        'maquinas_disponibles': [],
        'empleados':            [],
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


def admin_etapa_completar(request, pk):
    orden_pk = request.POST.get('orden_id', '') if request.method == 'POST' else None
    if request.method == 'POST':
        _etapa_completar(request, pk)
    return _admin_produccion_redirect(orden_pk=orden_pk, lote_pk=pk)


# ════════════════════════════════════════════════════════════════
# ADMIN — ORGANIZACIÓN (plantillas, obleas, líneas) — SOLO ADMIN
# ════════════════════════════════════════════════════════════════

def admin_organizacion(request):
    (procesos_bd, tipos_oblea, lineas_bd, kpis, alertas_bd,
     pasos_bd, pasos_proceso_bd, proceso_pieza_bd, piezas_bd) = _get_many(
        '/v1/list/Proceso/',
        '/v1/list/TipoOblea/',
        '/v1/list/Linea/',
        '/v1/list/kpis/',
        '/v1/list/alertas/',
        '/v1/list/pasos/',
        '/v1/list/PasoProceso/',
        '/v1/list/ProcesoPieza/',
        '/v1/list/piezas/',
    )
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Administrador',
        'unread_count': unread,
        'recent_notifications': [
            {
                'titulo': a.get('descripcion', ''),
                'tipo': 'alerta',
                'leida': str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre'),
            }
            for a in alertas_bd[:5]
        ],
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
            'activo':      p.get('activo', True),
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
            'activo':       t.get('activo', True),
        }
        for t in tipos_oblea
    ]

    lineas = [
        {
            'pk':               l.get('codigo'),
            'nombre':           l.get('nombre', ''),
            'activo':           l.get('activo', True),
            'proceso_pk':       l.get('proceso'),
            'proceso_asignado': procesos_map.get(str(l.get('proceso', '')), {}).get('nombre') if l.get('proceso') else None,
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
            'activo':              p.get('activo', True),
        }
        for p in pasos_bd
    ]

    kpi_cards = [
        {
            'nombre':         k.get('nombre', ''),
            'key':            k.get('clave', ''),
            'unidad':         '%',
            'verde':          k.get('umbralVerde', 0),
            'amarillo':       k.get('umbralAmarillo', 0),
            'rojo':           k.get('umbralRojo', 0),
            'label_verde':    f"≥ {k.get('umbralVerde', 0)}",
            'label_amarillo': f"{k.get('umbralAmarillo', 0)} – {k.get('umbralVerde', 0)}",
            'label_rojo':     f"< {k.get('umbralRojo', 0)}",
        }
        for k in kpis
    ]

    # Filtros de estado (activo/inactivo) para cada listado de la pestaña correspondiente
    estado_plantillas = request.GET.get('estado_plantillas', 'todos')
    if estado_plantillas == 'activo':
        plantillas_filtradas = [p for p in plantillas if p['activo']]
    elif estado_plantillas == 'inactivo':
        plantillas_filtradas = [p for p in plantillas if not p['activo']]
    else:
        plantillas_filtradas = plantillas

    estado_lineas = request.GET.get('estado_lineas', 'todos')
    if estado_lineas == 'activo':
        lineas_filtradas = [l for l in lineas if l['activo']]
    elif estado_lineas == 'inactivo':
        lineas_filtradas = [l for l in lineas if not l['activo']]
    else:
        lineas_filtradas = lineas

    estado_obleas = request.GET.get('estado_obleas', 'todos')
    if estado_obleas == 'activo':
        obleas_filtradas = [o for o in tipos_oblea_front if o['activo']]
    elif estado_obleas == 'inactivo':
        obleas_filtradas = [o for o in tipos_oblea_front if not o['activo']]
    else:
        obleas_filtradas = tipos_oblea_front

    estado_pasos = request.GET.get('estado_pasos', 'todos')
    if estado_pasos == 'activo':
        pasos_filtrados = [p for p in pasos if p['activo']]
    elif estado_pasos == 'inactivo':
        pasos_filtrados = [p for p in pasos if not p['activo']]
    else:
        pasos_filtrados = pasos

    plantillas_page = Paginator(plantillas_filtradas, PAGE_SIZE_ORGANIZACION).get_page(request.GET.get('page', 1))
    lineas_page     = Paginator(lineas_filtradas, PAGE_SIZE_ORGANIZACION).get_page(request.GET.get('page_lineas', 1))
    obleas_page     = Paginator(obleas_filtradas, PAGE_SIZE_ORGANIZACION).get_page(request.GET.get('page_obleas', 1))
    pasos_page      = Paginator(pasos_filtrados, PAGE_SIZE_ORGANIZACION).get_page(request.GET.get('page_pasos', 1))

    ctx.update({
        'plantillas':       plantillas,
        'plantillas_page':  plantillas_page,
        'estado_plantillas': estado_plantillas,
        'plantillas_extra_params': f'tab=plantillas&estado_plantillas={estado_plantillas}&',
        'tipos_oblea':      obleas_page,
        'estado_obleas':    estado_obleas,
        'obleas_extra_params': f'tab=obleas&estado_obleas={estado_obleas}&',
        'lineas':           lineas,
        'lineas_page':      lineas_page,
        'estado_lineas':    estado_lineas,
        'lineas_extra_params': f'tab=lineas&estado_lineas={estado_lineas}&',
        'pasos':            pasos_page,
        'estado_pasos':     estado_pasos,
        'pasos_extra_params': f'tab=pasos&estado_pasos={estado_pasos}&',
        'kpi_cards':        kpi_cards,
        'procesos_activos': [p for p in plantillas if p['activo']],
        'pasos_activos':    [p for p in pasos if p['activo']],
        'piezas_catalogo':  [{'pk': z.get('codigo'), 'nombre': z.get('nombre', '')} for z in piezas_bd],
        'breadcrumbs': [
            {'label': 'Dashboard',    'url': '/admin-dash/'},
            {'label': 'Organización', 'url': '/admin/organizacion/'},
        ],
    })
    return render(request, 'admin/organizacion.html', ctx)


def admin_organizacion_plantilla_crear(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        ok, resp = _post('/v1/create/Proceso/', {
            'codigo':      codigo,
            'nombre':      request.POST.get('nombre', ''),
            'descripcion': request.POST.get('descripcion', ''),
        })
        if not ok:
            messages.error(request, f'Error al crear la plantilla: {resp}')
            return _organizacion_redirect('plantillas')

        errores = []

        # 1. Crear los pasos nuevos definidos inline (modal apilado, plantilla nueva)
        nuevos_codigo = request.POST.getlist('paso_nuevo_codigo')
        nuevos_nombre = request.POST.getlist('paso_nuevo_nombre')
        nuevos_desc   = request.POST.getlist('paso_nuevo_descripcion')
        nuevos_tiempo = request.POST.getlist('paso_nuevo_tiempo')
        for i, pcod in enumerate(nuevos_codigo):
            pcod = pcod.strip()
            if not pcod:
                continue
            ok_p, resp_p = _post('/v1/create/Paso/', {
                'codigo':         pcod,
                'nombre':         nuevos_nombre[i] if i < len(nuevos_nombre) else pcod,
                'descripcion':    nuevos_desc[i] if i < len(nuevos_desc) else '',
                'tiempoEstimado': _duracion_str(int(nuevos_tiempo[i] or 0) * 60 if i < len(nuevos_tiempo) and nuevos_tiempo[i] else 0),
            })
            if not ok_p:
                errores.append(f'Paso {pcod}: {resp_p}')

        # 2. Enlazar pasos (existentes + recién creados) en el orden en que se agregaron
        orden_codigos = [c.strip() for c in request.POST.getlist('paso_orden_codigo') if c.strip()]
        for idx, pcod in enumerate(orden_codigos):
            ok_pp, resp_pp = _post('/v1/create/PasoProceso/', {
                'paso':    pcod,
                'proceso': codigo,
                'orden':   idx + 1,
            })
            if not ok_pp:
                errores.append(f'Vincular paso {pcod}: {resp_pp}')

        # 3. Piezas requeridas
        piezas_codigo   = request.POST.getlist('pieza_codigo')
        piezas_cantidad = request.POST.getlist('pieza_cantidad')
        for i, zcod in enumerate(piezas_codigo):
            zcod = zcod.strip()
            if not zcod:
                continue
            cant = piezas_cantidad[i] if i < len(piezas_cantidad) else 0
            ok_z, resp_z = _post('/v1/create/ProcesoPieza/', {
                'proceso':    codigo,
                'pieza':      zcod,
                'cantPiezas': int(cant or 0),
            })
            if not ok_z:
                errores.append(f'Pieza {zcod}: {resp_z}')

        if errores:
            messages.error(request, 'Plantilla creada con errores: ' + '; '.join(errores))
        else:
            messages.success(request, 'Plantilla creada.')
    return _organizacion_redirect('plantillas')


def admin_organizacion_plantilla_editar(request, pk):
    if request.method == 'POST':
        ok, resp = _patch(f'/v1/update/Proceso/{pk}/', {
            'nombre':      request.POST.get('nombre', ''),
            'descripcion': request.POST.get('descripcion', ''),
            'activo':      request.POST.get('activo') == 'true',
        })
        if ok:
            messages.success(request, 'Plantilla actualizada.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('plantillas', pk)


def admin_organizacion_plantilla_paso_asignar(request, pk):
    if request.method == 'POST':
        paso_codigo = request.POST.get('paso', '').strip()

        nuevo_codigo = request.POST.get('paso_nuevo_codigo', '').strip()
        if nuevo_codigo:
            minutos = request.POST.get('paso_nuevo_tiempo', 0)
            ok_p, resp_p = _post('/v1/create/Paso/', {
                'codigo':         nuevo_codigo,
                'nombre':         request.POST.get('paso_nuevo_nombre', nuevo_codigo),
                'descripcion':    request.POST.get('paso_nuevo_descripcion', ''),
                'tiempoEstimado': _duracion_str(int(minutos or 0) * 60),
            })
            if not ok_p:
                messages.error(request, f'Error al crear el paso: {resp_p}')
                return _organizacion_redirect('plantillas', pk)
            paso_codigo = nuevo_codigo

        if paso_codigo:
            pasos_proceso = _get('/v1/list/PasoProceso/', [])
            orden = sum(1 for pp in pasos_proceso if str(pp.get('proceso')) == str(pk)) + 1
            ok, resp = _post('/v1/create/PasoProceso/', {
                'paso':    paso_codigo,
                'proceso': pk,
                'orden':   orden,
            })
            if ok:
                messages.success(request, 'Paso agregado a la plantilla.')
            else:
                messages.error(request, f'Error: {resp}')
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
        cantidad = request.POST.get('cantidad', 0)
        if pieza_codigo:
            ok, resp = _post('/v1/create/ProcesoPieza/', {
                'proceso':    pk,
                'pieza':      pieza_codigo,
                'cantPiezas': int(cantidad or 0),
            })
            if ok:
                messages.success(request, 'Pieza asignada a la plantilla.')
            else:
                messages.error(request, f'Error: {resp}')
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
        ok, resp = _post('/v1/create/TipoOblea/', {
            'codigo':       request.POST.get('codigo', ''),
            'descripcion':  request.POST.get('nombre', ''),
            'cantidadDies': int(request.POST.get('dies_maximos', 0) or 0),
            'activo':       request.POST.get('activo', 'true') == 'true',
        })
        if ok:
            messages.success(request, 'Tipo de oblea creado.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('obleas')


def admin_organizacion_oblea_editar(request, pk):
    if request.method == 'POST':
        ok, resp = _patch(f'/v1/update/TipoOblea/{pk}/', {
            'descripcion':  request.POST.get('nombre', ''),
            'cantidadDies': int(request.POST.get('dies_maximos', 0) or 0),
            'activo':       request.POST.get('activo') == 'true',
        })
        if ok:
            messages.success(request, 'Tipo de oblea actualizado.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('obleas')


def admin_organizacion_linea_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/Linea/', {
            'codigo':  request.POST.get('codigo', ''),
            'nombre':  request.POST.get('nombre', ''),
            'proceso': request.POST.get('proceso') or None,
            'activo':  request.POST.get('activo', 'true') == 'true',
        })
        if ok:
            messages.success(request, 'Línea creada.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('lineas')


def admin_organizacion_linea_editar(request, pk):
    if request.method == 'POST':
        ok, resp = _patch(f'/v1/update/Linea/{pk}/', {
            'nombre':  request.POST.get('nombre', ''),
            'proceso': request.POST.get('proceso') or None,
            'activo':  request.POST.get('activo') == 'true',
        })
        if ok:
            messages.success(request, 'Línea actualizada.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('lineas')


def admin_organizacion_paso_crear(request):
    if request.method == 'POST':
        minutos = request.POST.get('tiempo_estimado', 0)
        ok, resp = _post('/v1/create/Paso/', {
            'codigo':         request.POST.get('codigo', ''),
            'nombre':         request.POST.get('nombre', ''),
            'descripcion':    request.POST.get('descripcion', ''),
            'tiempoEstimado': _duracion_str(int(minutos or 0) * 60),
            'activo':         request.POST.get('activo', 'true') == 'true',
        })
        if ok:
            messages.success(request, 'Paso creado.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('pasos')


def admin_organizacion_paso_editar(request, pk):
    if request.method == 'POST':
        minutos = request.POST.get('tiempo_estimado', 0)
        ok, resp = _patch(f'/v1/update/Paso/{pk}/', {
            'nombre':         request.POST.get('nombre', ''),
            'descripcion':    request.POST.get('descripcion', ''),
            'tiempoEstimado': _duracion_str(int(minutos or 0) * 60),
            'activo':         request.POST.get('activo') == 'true',
        })
        if ok:
            messages.success(request, 'Paso actualizado.')
        else:
            messages.error(request, f'Error: {resp}')
    return _organizacion_redirect('pasos')


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — PRODUCCIÓN (órdenes, lotes, hold, scrap)
# ════════════════════════════════════════════════════════════════

def supervisor_ordenes(request):
    ordenes_bd, obleas_bd, procesos_bd, lineas_bd, tipos_oblea_bd, alertas_bd = _get_many(
        '/v1/list/Orden/',
        '/v1/list/Oblea/',
        '/v1/list/Proceso/',
        '/v1/list/Linea/',
        '/v1/list/TipoOblea/',
        '/v1/list/alertas/',
    )
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Supervisor',
        'unread_count': unread,
        'recent_notifications': [
            {
                'titulo': a.get('descripcion', ''),
                'tipo': 'alerta',
                'leida': str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre'),
            }
            for a in alertas_bd[:5]
        ],
        'breadcrumbs': [],
    }

    procesos_map = {str(p.get('codigo', '')): p for p in procesos_bd}
    lineas_map   = {str(l.get('codigo', '')): l for l in lineas_bd}
    tipos_map    = {str(t.get('codigo', '')): t for t in tipos_oblea_bd}

    # Construir lista de órdenes con los campos que espera supervisor/ordenes.html
    ordenes = []
    for o in ordenes_bd:
        num   = o.get('numero')
        obs   = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
        total = len(obs)
        comp  = sum(1 for ob in obs if str(ob.get('estado', '')).lower() == 'termi')
        en_proc = sum(1 for ob in obs if str(ob.get('estado', '')).lower() == 'proce')
        pct = round(comp / total * 100) if total > 0 else 0
        edo = str(o.get('estado', '')).lower()
        if 'cerra' in edo:
            edo_str = 'completada'
        elif 'rechaz' in edo or 'cancel' in edo:
            edo_str = 'cancelada'
        else:
            edo_str = 'activa'

        # proceso como FakeObj para que template acceda a orden.proceso.nombre
        proceso_codigo = str(o.get('proceso', ''))
        proceso_data   = procesos_map.get(proceso_codigo, {})
        proceso_obj    = _FakeObj(pk=proceso_codigo, nombre=proceso_data.get('nombre', proceso_codigo))

        linea_pk = str(o.get('linea', '')) if o.get('linea') else ''
        tipo_pk  = str(o.get('tipoOblea', '')) if o.get('tipoOblea') else ''

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
            'total_lotes':      total,
            'lotes_completados': comp,
            'lotes_en_proceso': en_proc,
            'pct_completados':  pct,
            'estado':           edo_str,
            'estado_pk':        str(o.get('estado', '')),
            'tiene_hold':       any(str(ob.get('estado', '')).lower() == 'enhol' for ob in obs),
        })

    lineas_activas = [
        {'pk': l.get('codigo'), 'nombre': l.get('nombre', ''), 'proceso_pk': l.get('proceso'),
         'proceso_nombre': procesos_map.get(str(l.get('proceso', '')), {}).get('nombre', '')}
        for l in lineas_bd
        if l.get('activo', True) and l.get('proceso')
    ]
    tipos_oblea_activos = [
        {'pk': t.get('codigo'), 'nombre': t.get('descripcion', '')}
        for t in tipos_oblea_bd
        if t.get('activo', True)
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

    ctx.update({
        'ordenes':           ordenes,
        'ordenes_json_data': ordenes_json_data,
        'lineas':            lineas_activas,
        'tipos_oblea':       tipos_oblea_activos,
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


def supervisor_lote_scrap(request, pk):
    if request.method == 'POST':
        _lote_scrap(request, pk)
    return redirect('supervisor_ordenes')


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — DETALLE DE ORDEN Y LOTE (vistas propias)
# ════════════════════════════════════════════════════════════════

def supervisor_orden_detalle(request, pk):
    (ordenes_bd, obleas_bd, procesos_bd, lineas_bd, tipos_oblea_bd,
     pasos_bd, pasos_catalogo, pasos_realizados_bd, alertas_bd) = _get_many(
        '/v1/list/Orden/',
        '/v1/list/Oblea/',
        '/v1/list/Proceso/',
        '/v1/list/Linea/',
        '/v1/list/TipoOblea/',
        '/v1/list/PasoProceso/',
        '/v1/list/pasos/',
        '/v1/list/PasoRealizado/',
        '/v1/list/alertas/',
    )
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Supervisor',
        'unread_count': unread,
        'recent_notifications': [
            {
                'titulo': a.get('descripcion', ''),
                'tipo': 'alerta',
                'leida': str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre'),
            }
            for a in alertas_bd[:5]
        ],
        'breadcrumbs': [],
    }

    orden_data = next((o for o in ordenes_bd if str(o.get('numero')) == str(pk)), {})
    if not orden_data:
        return redirect('supervisor_ordenes')

    num    = orden_data.get('numero')
    obs    = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
    total  = len(obs)
    comp   = sum(1 for ob in obs if str(ob.get('estado', '')).lower() == 'termi')
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

    edo = str(orden_data.get('estado', '')).lower()
    if 'cerra' in edo:
        edo_str = 'completada'
    elif 'rechaz' in edo or 'cancel' in edo:
        edo_str = 'cancelada'
    else:
        edo_str = 'activa'

    orden = {
        'pk':               num,
        'numero':           f'ORD-{num:04d}' if isinstance(num, int) else str(num),
        'proceso':          proceso_obj,
        'linea_nombre':     linea_data.get('nombre', '—'),
        'tipo_oblea_nombre': tipo_data.get('descripcion', '—'),
        'total_lotes':      total,
        'lotes_completados': comp,
        'lotes_en_proceso': en_proc,
        'estado':           edo_str,
        'estado_pk':        str(orden_data.get('estado', '')),
    }

    lotes = []
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
        dies_iniciales = ob.get('diesGenerados', 0)
        dies_activos, scrap_total, yield_pct = _calcular_yield(ob_num, pasos_realizados_bd, dies_iniciales)
        lotes.append({
            'pk':            ob_num,
            'folio':         f'LOT-{ob_num:04d}' if isinstance(ob_num, int) else str(ob_num),
            'numero_oblea':  ob_num,
            'dies_buenos':   dies_iniciales,
            'dies_activos':  dies_activos,
            'scrap':         scrap_total,
            'etapa_actual':  _FakeObj(nombre=etapa_nombre),
            'estado':        _FakeObj(nombre=ESTADOS_OBLEA_LABEL.get(edo_ob, edo_ob.capitalize())),
            'yield_pct':     yield_pct,
        })

    ctx.update({
        'orden': orden,
        'lotes': lotes,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Órdenes',   'url': '/supervisor/ordenes/'},
            {'label': orden['numero'], 'url': ''},
        ],
    })
    return render(request, 'supervisor/orden_detalle.html', ctx)


def supervisor_lote_detalle(request, pk):
    obleas_bd, ordenes_bd, pasos_bd, pasos_catalogo, pasos_realizados, alertas_bd = _get_many(
        '/v1/list/Oblea/',
        '/v1/list/Orden/',
        '/v1/list/PasoProceso/',
        '/v1/list/pasos/',
        '/v1/list/PasoRealizado/',
        '/v1/list/alertas/',
    )
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Supervisor',
        'unread_count': unread,
        'recent_notifications': [
            {
                'titulo': a.get('descripcion', ''),
                'tipo': 'alerta',
                'leida': str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre'),
            }
            for a in alertas_bd[:5]
        ],
        'breadcrumbs': [],
    }

    ob = next((o for o in obleas_bd if str(o.get('numero')) == str(pk)), {})
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

    etapas_raw = _construir_etapas(pasos_de_proceso, catalogo_map, realizados_map)

    etapas = []
    etapa_activa = None
    for e in etapas_raw:
        catalogo = catalogo_map.get(e['codigo'], {})
        etapa = _FakeObj(
            codigo=e['codigo'],
            nombre=e['nombre'],
            descripcion=catalogo.get('descripcion', ''),
            completado=e['estado'] in ('aprobado', 'rechazado'),
            rechazado=e['estado'] == 'rechazado',
            activo=e['estado'] == 'en_curso',
            operador_nombre='—',
            maquina='—',
            iniciado_en=None,
            completado_en=None,
            scrap=int((realizados_map.get(e['codigo'], {}) or {}).get('scrap', 0) or 0),
            yield_pct=0,
            notas=e['meta'] or '',
            tipo_maquina='—',
            tiempo_estimado_seg=e['tiempo_estimado_seg'],
            hora_inicio_iso=e['hora_inicio_iso'],
        )
        etapas.append(etapa)
        if etapa.activo:
            etapa_activa = etapa

    edo    = str(ob.get('estado', '')).lower()
    edo_str = ESTADOS_OBLEA_LABEL.get(edo, edo.capitalize())

    dies_iniciales = ob.get('diesGenerados', 0)
    dies_activos, scrap_total, yield_pct = _calcular_yield(num, pasos_realizados, dies_iniciales)

    lote = {
        'pk':             num,
        'folio':          f'LOT-{num:04d}' if isinstance(num, int) else str(num),
        'orden':          _FakeObj(
                              pk=orden_num,
                              numero=f'ORD-{orden_num:04d}' if isinstance(orden_num, int) else str(orden_num)
                          ) if orden_data else None,
        'estado':         _FakeObj(nombre=edo_str),
        'dies_iniciales': dies_iniciales,
        'dies_activos':   dies_activos,
        'scrap_total':    scrap_total,
        'yield_pct':      yield_pct,
        'etapas':         etapas,
        'etapa_activa':   etapa_activa,
    }

    ctx.update({
        'lote':          lote,
        'tipos_defecto': [],
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