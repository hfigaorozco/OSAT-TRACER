import json
from django.shortcuts import render, redirect
from django.contrib import messages
from home.views import _base_ctx, _get, _post, _patch, _FakeObj


# ── Helper compartido para construir ordenes y lotes ─────────────────────────

def _build_ordenes_lotes():
    ordenes_bd     = _get('/v1/list/Orden/', [])
    obleas_bd      = _get('/v1/list/Oblea/', [])
    procesos_bd    = _get('/v1/list/Proceso/', [])
    pasos_bd       = _get('/v1/list/PasoProceso/', [])
    pasos_catalogo = _get('/v1/list/pasos/', [])
    catalogo_map   = {str(p.get('codigo', '')): p for p in pasos_catalogo}

    ordenes = []
    for o in ordenes_bd:
        num   = o.get('numero')
        obs   = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
        total = len(obs)
        comp  = sum(
            1 for ob in obs
            if str(ob.get('estado', '')).lower() in ('completado', 'aprobado', 'co001')
        )
        pct = round(comp / total * 100) if total > 0 else 0
        edo = str(o.get('estado', '')).lower()
        if 'aprobado' in edo or 'complet' in edo:
            edo_str = 'aprobado'
        elif 'rechaz' in edo:
            edo_str = 'rechazado'
        elif 'activo' in edo or 'proceso' in edo:
            edo_str = 'en_proceso'
        else:
            edo_str = 'pendiente'

        ordenes.append({
            'pk':           num,
            'numero':       f'ORD-{num:04d}' if isinstance(num, int) else str(num),
            'proceso':      str(o.get('proceso', '—')),
            'fecha_inicio': str(o.get('horaIni', '—'))[:10],
            'fecha_fin':    str(o.get('horaFin', '—'))[:10],
            'total_lotes':  total,
            'completados':  comp,
            'pct':          pct,
            'estado':       edo_str,
        })

    lotes = []
    for ob in obleas_bd:
        num       = ob.get('numero')
        orden_num = ob.get('orden')
        edo       = str(ob.get('estado', '')).lower()

        if 'complet' in edo or 'aprobado' in edo:
            edo_str = 'aprobado'
        elif 'rechaz' in edo:
            edo_str = 'rechazado'
        elif 'activo' in edo or 'proceso' in edo:
            edo_str = 'en_proceso'
        else:
            edo_str = 'pendiente'

        orden_data       = next((o for o in ordenes_bd if str(o.get('numero')) == str(orden_num)), {})
        proceso_codigo   = str(orden_data.get('proceso', ''))
        pasos_de_proceso = sorted(
            [p for p in pasos_bd if str(p.get('proceso')) == proceso_codigo],
            key=lambda x: x.get('orden', 0)
        )
        etapas = []
        for p in pasos_de_proceso:
            codigo = str(p.get('paso', ''))
            cat    = catalogo_map.get(codigo, {})
            etapas.append({
                'nombre':             cat.get('nombre', codigo),
                'estado':             'pendiente',
                'meta':               None,
                'detalle':            None,
                'tiempo_estimado_seg': cat.get('tiempoEstimado', 0),
                'hora_inicio_iso':    '',
            })
        if etapas:
            etapas[0]['estado'] = 'en_curso'

        lotes.append({
            'pk':                num,
            'folio':             f'LOT-{num:04d}' if isinstance(num, int) else str(num),
            'orden_pk':          orden_num,
            'proceso':           str(orden_data.get('proceso', '—')),
            'fecha_inicio':      str(orden_data.get('horaIni', '—'))[:10],
            'fecha_fin':         str(orden_data.get('horaFin', '—'))[:10],
            'total_pasos':       len(etapas),
            'pasos_completados': 0,
            'estado':            edo_str,
            'dies_iniciales':    ob.get('diesGenerados', 0),
            'dies_activos':      ob.get('diesGenerados', 0),
            'scrap':             0,
            'yield_pct':         98.0,
            'etapas':            etapas,
        })

    plantillas = [
        _FakeObj(pk=p.get('codigo'), nombre=p.get('nombre', ''))
        for p in procesos_bd
    ]

    return ordenes, lotes, plantillas


# ════════════════════════════════════════════════════════════════
# ADMIN — PRODUCCIÓN
# ════════════════════════════════════════════════════════════════

def admin_produccion(request):
    ctx = _base_ctx('Administrador')
    ordenes, lotes, plantillas = _build_ordenes_lotes()
    ctx.update({
        'ordenes':              ordenes,
        'lotes':                lotes,
        'plantillas':           plantillas,
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


# ════════════════════════════════════════════════════════════════
# ADMIN — ORGANIZACIÓN (plantillas, obleas, líneas) — SOLO ADMIN
# ════════════════════════════════════════════════════════════════

def admin_organizacion(request):
    ctx = _base_ctx('Administrador')

    procesos_bd = _get('/v1/list/Proceso/', [])
    tipos_oblea = _get('/v1/list/TipoOblea/', [])
    lineas_bd   = _get('/v1/list/Linea/', [])
    kpis        = _get('/v1/list/kpis/', [])

    plantillas = [
        {
            'pk':          p.get('codigo'),
            'nombre':      p.get('nombre', '—'),
            'descripcion': p.get('descripcion', ''),
            'activo':      True,
            'pasos_count': 0,
        }
        for p in procesos_bd
    ]
    tipos_oblea_front = [
        {
            'pk':           t.get('codigo'),
            'codigo':       t.get('codigo'),
            'nombre':       t.get('descripcion', ''),
            'dies_maximos': t.get('cantidadDies', 0),
            'activo':       True,
        }
        for t in tipos_oblea
    ]
    lineas = [
        {
            'pk':               l.get('codigo'),
            'nombre':           l.get('nombre', ''),
            'planta':           '—',
            'activo':           True,
            'proceso_asignado': None,
        }
        for l in lineas_bd
    ]
    kpi_cards = [
        {
            'nombre':         k.get('nombre', ''),
            'key':            k.get('nombre', '').lower(),
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

    ctx.update({
        'plantillas':  plantillas,
        'tipos_oblea': tipos_oblea_front,
        'lineas':      lineas,
        'kpi_cards':   kpi_cards,
        'breadcrumbs': [
            {'label': 'Dashboard',    'url': '/admin-dash/'},
            {'label': 'Organización', 'url': '/admin/organizacion/'},
        ],
    })
    return render(request, 'admin/organizacion.html', ctx)


def admin_organizacion_plantilla_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/Proceso/', {
            'codigo':      request.POST.get('codigo', ''),
            'nombre':      request.POST.get('nombre', ''),
            'descripcion': request.POST.get('descripcion', ''),
        })
        if ok:
            messages.success(request, 'Plantilla creada.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_organizacion')


def admin_organizacion_plantilla_editar(request, pk):
    if request.method == 'POST':
        ok, resp = _patch(f'/v1/update/Proceso/{pk}/', {
            'descripcion': request.POST.get('descripcion', ''),
        })
        if ok:
            messages.success(request, 'Plantilla actualizada.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_organizacion')


def admin_organizacion_oblea_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/TipoOblea/', {
            'codigo':       request.POST.get('codigo', ''),
            'descripcion':  request.POST.get('nombre', ''),
            'cantidadDies': int(request.POST.get('dies_maximos', 0)),
        })
        if ok:
            messages.success(request, 'Tipo de oblea creado.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_organizacion')


def admin_organizacion_linea_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/Linea/', {
            'codigo': request.POST.get('codigo', ''),
            'nombre': request.POST.get('nombre', ''),
        })
        if ok:
            messages.success(request, 'Línea creada.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_organizacion')


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — PRODUCCIÓN (órdenes, lotes, hold, scrap)
# ════════════════════════════════════════════════════════════════

def supervisor_ordenes(request):
    ctx = _base_ctx('Supervisor')
    ordenes_bd  = _get('/v1/list/Orden/', [])
    obleas_bd   = _get('/v1/list/Oblea/', [])
    procesos_bd = _get('/v1/list/Proceso/', [])

    # Construir lista de órdenes con los campos que espera supervisor/ordenes.html
    ordenes = []
    for o in ordenes_bd:
        num   = o.get('numero')
        obs   = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
        total = len(obs)
        comp  = sum(
            1 for ob in obs
            if str(ob.get('estado', '')).lower() in ('completado', 'aprobado')
        )
        en_proc = sum(
            1 for ob in obs
            if str(ob.get('estado', '')).lower() in ('activo', 'en_proceso', 'proceso')
        )
        pct = round(comp / total * 100) if total > 0 else 0
        edo = str(o.get('estado', '')).lower()
        if 'aprobado' in edo or 'complet' in edo or 'cerra' in edo:
            edo_str = 'completada'
        elif 'rechaz' in edo or 'cancel' in edo:
            edo_str = 'cancelada'
        else:
            edo_str = 'activa'

        # proceso como FakeObj para que template acceda a orden.proceso.nombre
        proceso_codigo = str(o.get('proceso', ''))
        proceso_data   = next((p for p in procesos_bd if str(p.get('codigo')) == proceso_codigo), {})
        proceso_obj    = _FakeObj(pk=proceso_codigo, nombre=proceso_data.get('nombre', proceso_codigo))

        ordenes.append({
            'pk':               num,
            'numero':           f'ORD-{num:04d}' if isinstance(num, int) else str(num),
            'proceso':          proceso_obj,
            'fecha_inicio':     str(o.get('horaIni', '—'))[:10],
            'fecha_fin':        str(o.get('horaFin', '—'))[:10],
            'total_lotes':      total,
            'lotes_completados': comp,
            'lotes_en_proceso': en_proc,
            'pct_completados':  pct,
            'estado':           edo_str,
            'prioridad':        'media',
        })

    procesos = [
        _FakeObj(pk=p.get('codigo'), nombre=p.get('nombre', ''))
        for p in procesos_bd
    ]

    ctx.update({
        'ordenes':  ordenes,
        'procesos': procesos,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Órdenes',   'url': '/supervisor/ordenes/'},
        ],
    })
    return render(request, 'supervisor/ordenes.html', ctx)


def supervisor_ordenes_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/Orden/', {
            'horaIni': request.POST.get('fecha_inicio', '') + ' 00:00:00',
            'horaFin': request.POST.get('fecha_fin', '')    + ' 23:59:00',
            'proceso': request.POST.get('proceso', ''),
            'estado':  '01',
            'empleado': 1,
        })
        if ok:
            messages.success(request, 'Orden creada.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('supervisor_ordenes')


def supervisor_lotes(request):
    return redirect('supervisor_ordenes')


def supervisor_lote_detalle(request, pk):
    return redirect('supervisor_ordenes')


def supervisor_orden_detalle(request, pk=1):
    return redirect('supervisor_ordenes')


def supervisor_lote_registrar(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/Oblea/', {
            'diesGenerados': int(request.POST.get('dies_buenos', 0)),
            'orden':  request.POST.get('orden_id', ''),
            'estado': '01',
            'tipo':   '01',
        })
        if ok:
            messages.success(request, 'Lote registrado.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('supervisor_ordenes')


def supervisor_lote_hold(request, pk):
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'HO001'})
    if not ok:
        messages.error(request, f'Error: {resp}')
    return redirect('supervisor_ordenes')


def supervisor_lote_scrap(request, pk):
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'RE001'})
    if not ok:
        messages.error(request, f'Error: {resp}')
    return redirect('supervisor_ordenes')


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — DETALLE DE ORDEN Y LOTE (vistas propias)
# ════════════════════════════════════════════════════════════════

def supervisor_orden_detalle(request, pk):
    ctx = _base_ctx('Supervisor')
    ordenes_bd = _get('/v1/list/Orden/', [])
    obleas_bd  = _get('/v1/list/Oblea/', [])
    procesos_bd = _get('/v1/list/Proceso/', [])

    orden_data = next((o for o in ordenes_bd if str(o.get('numero')) == str(pk)), {})
    if not orden_data:
        return redirect('supervisor_ordenes')

    num    = orden_data.get('numero')
    obs    = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
    total  = len(obs)
    comp   = sum(1 for ob in obs if str(ob.get('estado', '')).lower() in ('completado', 'aprobado'))
    en_proc = sum(1 for ob in obs if str(ob.get('estado', '')).lower() in ('activo', 'en_proceso', 'proceso'))

    proceso_codigo = str(orden_data.get('proceso', ''))
    proceso_data   = next((p for p in procesos_bd if str(p.get('codigo')) == proceso_codigo), {})
    proceso_obj    = _FakeObj(pk=proceso_codigo, nombre=proceso_data.get('nombre', proceso_codigo))

    edo = str(orden_data.get('estado', '')).lower()
    if 'aprobado' in edo or 'complet' in edo or 'cerra' in edo:
        edo_str = 'completada'
    elif 'rechaz' in edo or 'cancel' in edo:
        edo_str = 'cancelada'
    else:
        edo_str = 'activa'

    orden = {
        'pk':               num,
        'numero':           f'ORD-{num:04d}' if isinstance(num, int) else str(num),
        'proceso':          proceso_obj,
        'total_lotes':      total,
        'lotes_completados': comp,
        'lotes_en_proceso': en_proc,
        'estado':           edo_str,
    }

    lotes = []
    for ob in obs:
        ob_num = ob.get('numero')
        edo_ob = str(ob.get('estado', '')).lower()
        lotes.append({
            'pk':            ob_num,
            'folio':         f'LOT-{ob_num:04d}' if isinstance(ob_num, int) else str(ob_num),
            'numero_oblea':  ob_num,
            'dies_buenos':   ob.get('diesGenerados', 0),
            'etapa_actual':  _FakeObj(nombre='—'),
            'estado':        _FakeObj(nombre=edo_ob.capitalize()),
            'yield_pct':     98.0,
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


def _parse_tiempo_estimado_segundos(tiempo_val):
    """
    Acepta int (segundos directos) o string HH:MM:SS del DurationField.
    """
    if not tiempo_val:
        return 0
    # Si ya es un número (el serializer devuelve total_seconds())
    if isinstance(tiempo_val, (int, float)):
        return int(tiempo_val)
    # Si es string HH:MM:SS o D days, HH:MM:SS
    try:
        s = str(tiempo_val).strip()
        if 'day' in s:
            parts = s.split(', ')
            days = int(parts[0].split(' ')[0])
            time_part = parts[1]
        else:
            days = 0
            time_part = s
        h, m, sec = time_part.split(':')
        return days * 86400 + int(h) * 3600 + int(m) * 60 + int(float(sec))
    except Exception:
        return 0


def supervisor_lote_detalle(request, pk):
    ctx = _base_ctx('Supervisor')
    obleas_bd        = _get('/v1/list/Oblea/', [])
    ordenes_bd       = _get('/v1/list/Orden/', [])
    pasos_bd         = _get('/v1/list/PasoProceso/', [])
    pasos_catalogo   = _get('/v1/list/pasos/', [])   # catálogo con tiempoEstimado
    pasos_realizados = _get('/v1/list/PasoRealizado/', [])

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

    etapas = []
    etapa_activa = None

    for i, pp in enumerate(pasos_de_proceso):
        codigo_paso = str(pp.get('paso', ''))
        catalogo    = catalogo_map.get(codigo_paso, {})
        realizado   = realizados_map.get(codigo_paso)

        tiempo_estimado_seg = _parse_tiempo_estimado_segundos(
            catalogo.get('tiempoEstimado', '')
        )

        if realizado:
            edo_pr = str(realizado.get('estado', '')).lower()
            completado = 'aprob' in edo_pr or 'complet' in edo_pr or 'compl' in edo_pr
            activo     = 'curso' in edo_pr or 'activo' in edo_pr or 'proceso' in edo_pr
            hora_inicio_str = str(realizado.get('hora', '') or '')
        else:
            completado = False
            # Primera etapa sin completar = activa
            activo = not any(
                'aprob' in str(realizados_map.get(str(p.get('paso','')), {}).get('estado','')).lower() or
                'complet' in str(realizados_map.get(str(p.get('paso','')), {}).get('estado','')).lower()
                for p in pasos_de_proceso[:i]
                if realizados_map.get(str(p.get('paso','')))
            ) and i == len([
                x for x in pasos_de_proceso
                if realizados_map.get(str(x.get('paso',''))) and (
                    'aprob' in str(realizados_map[str(x.get('paso',''))].get('estado','')).lower() or
                    'complet' in str(realizados_map[str(x.get('paso',''))].get('estado','')).lower()
                )
            ])
            hora_inicio_str = ''

        etapa = _FakeObj(
            codigo=codigo_paso,
            nombre=catalogo.get('nombre', codigo_paso),
            descripcion=catalogo.get('descripcion', ''),
            completado=completado,
            activo=activo,
            operador_nombre='—',
            maquina='—',
            iniciado_en=None,
            completado_en=None,
            scrap=0,
            yield_pct=0,
            notas='',
            tipo_maquina='—',
            tiempo_estimado_seg=tiempo_estimado_seg,
            hora_inicio_iso=hora_inicio_str,
        )
        etapas.append(etapa)
        if activo and not completado and etapa_activa is None:
            etapa_activa = etapa

    if etapa_activa is None and etapas:
        # Ninguna marcada como activa — usar primera no completada
        for e in etapas:
            if not e.completado:
                e.activo = True
                etapa_activa = e
                break

    edo    = str(ob.get('estado', '')).lower()
    edo_str = 'En proceso' if 'activo' in edo or 'proce' in edo else edo.capitalize()

    lote = {
        'pk':             num,
        'folio':          f'LOT-{num:04d}' if isinstance(num, int) else str(num),
        'orden':          _FakeObj(
                              pk=orden_num,
                              numero=f'ORD-{orden_num:04d}' if isinstance(orden_num, int) else str(orden_num)
                          ) if orden_data else None,
        'estado':         _FakeObj(nombre=edo_str),
        'dies_iniciales': ob.get('diesGenerados', 0),
        'dies_activos':   ob.get('diesGenerados', 0),
        'scrap_total':    0,
        'yield_pct':      98.0,
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
        paso       = request.POST.get('paso', '')
        resultado  = request.POST.get('resultado', 'aprobado')
        observaciones = request.POST.get('observaciones', '')

        # Mapear resultado a código de estado del backend
        estado_map = {
            'aprobado':  'compl',
            'rechazado': 'nocom',
        }
        estado = estado_map.get(resultado, 'compl')

        ok, resp = _post('/v1/create/PasoRealizado/', {
            'paso':          paso,
            'oblea':         pk,
            'estado':        estado,
            'observaciones': observaciones,
        })
        if ok:
            messages.success(request, 'Etapa completada correctamente.')
        else:
            messages.error(request, f'Error al completar: {resp}')
    return redirect('supervisor_lote_detalle', pk=pk)