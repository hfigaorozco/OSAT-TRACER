import json
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

BACKEND_URL = 'http://localhost:8001/api'


# ── Helpers HTTP ─────────────────────────────────────────────────────────────

def _get(endpoint, default=None):
    try:
        r = requests.get(f'{BACKEND_URL}{endpoint}', timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default if default is not None else []


def _post(endpoint, data):
    try:
        r = requests.post(f'{BACKEND_URL}{endpoint}', json=data, timeout=5)
        r.raise_for_status()
        return True, r.json()
    except requests.HTTPError as e:
        try:
            return False, str(e.response.json())
        except Exception:
            return False, str(e)
    except Exception as e:
        return False, str(e)


def _patch(endpoint, data):
    try:
        r = requests.patch(f'{BACKEND_URL}{endpoint}', json=data, timeout=5)
        r.raise_for_status()
        return True, r.json()
    except Exception as e:
        return False, str(e)


# ── Objeto falso para templates que esperan atributos de modelo ──────────────

class _FakeObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __str__(self):
        return str(getattr(self, 'nombre', getattr(self, 'descripcion', '')))


# ── Contexto base ─────────────────────────────────────────────────────────────

def _base_ctx(role='Administrador'):
    alertas = _get('/v1/list/alertas/', [])
    unread  = sum(1 for a in alertas if str(a.get('estadoAlerta', '')).lower() == 'activo')
    return {
        'user_role':            role,
        'unread_count':         unread,
        'recent_notifications': [
            {
                'titulo': a.get('descripcion', ''),
                'tipo':   'alerta',
                'leida':  str(a.get('estadoAlerta', '')).lower() != 'activo',
            }
            for a in alertas[:5]
        ],
        'breadcrumbs': [],
    }


# ── Semáforo KPI reutilizable ─────────────────────────────────────────────────

def _semaforo_color(valor, kpi_dict, unidad='%'):
    """
    kpi_dict: dict con claves umbralVerde, umbralAmarillo, umbralRojo
    Devuelve dict listo para el template.
    """
    val_str = f'{valor:.1f}' if isinstance(valor, float) else str(valor)
    if not kpi_dict:
        return {'bg': '#E9ECEF', 'color': '#495057', 'valor': val_str, 'unidad': unidad}
    if valor >= kpi_dict.get('umbralVerde', 0):
        bg, color = '#D4EDDA', '#155724'
    elif valor >= kpi_dict.get('umbralAmarillo', 0):
        bg, color = '#FFF3CD', '#856404'
    else:
        bg, color = '#F8D7DA', '#721C24'
    return {'bg': bg, 'color': color, 'valor': val_str, 'unidad': unidad}


def _build_semaforo(kpi_list):
    """Construye las 3 filas del semáforo con los umbrales reales del backend."""
    kpi_map = {k.get('nombre', '').lower(): k for k in kpi_list}
    ky = kpi_map.get('yield')
    kt = kpi_map.get('throughput')
    ko = kpi_map.get('oee')
    return [
        {'nombre': 'Yield',
         'celdas': [_semaforo_color(94.2, ky), _semaforo_color(91.5, ky),
                    _semaforo_color(88.3, ky), _semaforo_color(91.3, ky)]},
        {'nombre': 'Throughput',
         'celdas': [_semaforo_color(210, kt, ''), _semaforo_color(185, kt, ''),
                    _semaforo_color(95,  kt, ''), _semaforo_color(163, kt, '')]},
        {'nombre': 'OEE',
         'celdas': [_semaforo_color(88.1, ko), _semaforo_color(82.4, ko),
                    _semaforo_color(71.2, ko), _semaforo_color(80.6, ko)]},
    ]


# ════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════

def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user:
            login(request, user)
            empleados = _get('/v1/list/empleados/', [])
            rol = 'administrador'
            for e in empleados:
                if e.get('username') == user.username:
                    rol = (e.get('rol') or '').lower()
                    break
            if 'supervisor' in rol:
                return redirect('supervisor_dashboard')
            return redirect('admin_dashboard')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'base/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ════════════════════════════════════════════════════════════════
# ADMIN — DASHBOARD
# ════════════════════════════════════════════════════════════════

def admin_dashboard(request):
    ctx = _base_ctx('Administrador')

    empleados  = _get('/v1/list/empleados/', [])
    maquinas   = _get('/v1/list/maquinaria/', [])
    kpis       = _get('/v1/list/kpis/', [])
    obleas     = _get('/v1/list/Oblea/', [])
    ordenes_bd = _get('/v1/list/Orden/', [])
    alertas_bd = _get('/v1/list/alertas/', [])

    lotes_hold = sum(
        1 for o in obleas
        if str(o.get('estado', '')).lower() in ('hold', 'ho001')
    )

    ordenes_activas = [
        {
            'numero':      f"ORD-{o['numero']:04d}" if isinstance(o.get('numero'), int) else str(o.get('numero', '')),
            'proceso':     str(o.get('proceso', '—')),
            'completados': 0,
            'total':       1,
            'pct':         0,
            'estado':      'en_proceso',
        }
        for o in ordenes_bd[:5]
    ]

    alertas_activas = [
        {
            'tipo':        'advertencia',
            'descripcion': a.get('descripcion', ''),
            'referencia':  f"#{a.get('numero', '—')}",
            'tiempo':      '—',
        }
        for a in alertas_bd
        if str(a.get('estadoAlerta', '')).lower() == 'activo'
    ][:5]

    ctx.update({
        'kpi': {
            'cuentas':          len(empleados),
            'empleados':        len(empleados),
            'maquinas':         len(maquinas),
            'lotes_hold':       lotes_hold,
            'lotes_hold_delta': '',
        },
        'throughput_labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'throughput_data':   [7200, 8100, 8900, 7800, 9200, 8500,
                              9800, 10200, 9500, 10800, 11200, 11800],
        'semaforo_kpi':    _build_semaforo(kpis),
        'ordenes_activas': ordenes_activas,
        'alertas_activas': alertas_activas,
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}],
    })
    return render(request, 'admin/dashboard.html', ctx)


# ════════════════════════════════════════════════════════════════
# ADMIN — INVENTARIO
# ════════════════════════════════════════════════════════════════

def admin_inventario(request):
    ctx = _base_ctx('Administrador')
    piezas_bd = _get('/v1/list/piezas/', [])
    piezas = [
        {
            'pk':             p.get('codigo', ''),
            'codigo':         p.get('codigo', '—'),
            'nombre':         p.get('nombre', '—'),
            'descripcion':    p.get('descripcion', ''),
            'stock':          p.get('stockActual', 0),
            'stock_minimo':   p.get('stockMinimo', 0),
            'linea':          '—',
            'operador':       '—',
            'fecha_registro': '—',
        }
        for p in piezas_bd
    ]
    ctx.update({
        'piezas':     piezas,
        'categorias': [],
        'breadcrumbs': [
            {'label': 'Dashboard',  'url': '/admin-dash/'},
            {'label': 'Inventario', 'url': '/admin/inventario/'},
        ],
    })
    return render(request, 'admin/inventario.html', ctx)


def admin_inventario_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/pieza/', {
            'codigo':      request.POST.get('codigo', ''),
            'nombre':      request.POST.get('nombre', ''),
            'descripcion': request.POST.get('descripcion', ''),
            'stockActual': int(request.POST.get('stock', 0)),
            'stockMinimo': int(request.POST.get('stock_minimo', 0)),
        })
        if ok:
            messages.success(request, 'Pieza creada correctamente.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_inventario')


def admin_inventario_movimiento(request):
    if request.method == 'POST':
        pieza_id = request.POST.get('pieza_id', '')
        tipo     = request.POST.get('tipo_mov', '')
        cantidad = int(request.POST.get('cantidad', 0))

        pieza        = _get(f'/v1/detail/pieza/{pieza_id}/', {})
        stock_actual = pieza.get('stockActual', 0)

        if tipo == 'entrada':
            nuevo_stock = stock_actual + cantidad
        elif tipo == 'salida':
            nuevo_stock = max(0, stock_actual - cantidad)
        else:
            nuevo_stock = cantidad

        ok, resp = _patch(f'/v1/update/pieza/{pieza_id}/', {'stockActual': nuevo_stock})
        if ok:
            messages.success(request, 'Movimiento registrado.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_inventario')


# ════════════════════════════════════════════════════════════════
# ADMIN — PERSONAL
# ════════════════════════════════════════════════════════════════

def admin_personal(request):
    ctx = _base_ctx('Administrador')
    empleados_bd = _get('/v1/list/empleados/', [])

    empleados = [
        {
            'pk':               e.get('numero'),
            'primer_nombre':    e.get('nombre', ''),
            'apellido_paterno': e.get('primerApell', ''),
            'apellido_materno': e.get('seguApell', ''),
            'rfc':              e.get('rfc', ''),
            'rol':              _FakeObj(nombre=e.get('rol', '—')),
            'estado':           _FakeObj(nombre=e.get('estado', '—')),
            'fecha_contrato':   e.get('fechaReg', '—'),
        }
        for e in empleados_bd
    ]
    cuentas = [
        {
            'pk':             e.get('numero'),
            'user':           _FakeObj(username=e.get('username', ''),
                                       email=e.get('email', '')),
            'rol':            (e.get('rol') or '').lower(),
            'activo':         True,
            'fecha_contrato': e.get('fechaReg', '—'),
        }
        for e in empleados_bd
    ]

    ctx.update({
        'empleados':        empleados,
        'cuentas':          cuentas,
        'roles_list':       [_FakeObj(pk='AD', nombre='Administrador'),
                             _FakeObj(pk='SU', nombre='Supervisor'),
                             _FakeObj(pk='OP', nombre='Operador')],
        'estados_empleado': [_FakeObj(pk='AC', nombre='Activo'),
                             _FakeObj(pk='IN', nombre='Inactivo')],
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/admin-dash/'},
            {'label': 'Personal',  'url': '/admin/personal/'},
        ],
    })
    return render(request, 'admin/personal.html', ctx)


def admin_personal_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/empleado/', {
            'nombre':      request.POST.get('primer_nombre', ''),
            'primerApell': request.POST.get('apellido_paterno', ''),
            'seguApell':   request.POST.get('apellido_materno', ''),
            'rfc':         request.POST.get('rfc', ''),
            'estado':      request.POST.get('estado', ''),
            'rol':         request.POST.get('rol', ''),
            'username':    request.POST.get('username', request.POST.get('rfc', '')),
            'password':    request.POST.get('password', 'Osat2026!'),
            'email':       request.POST.get('email', ''),
        })
        if ok:
            messages.success(request, 'Empleado creado correctamente.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_personal')


def admin_cuentas_crear(request):
    return admin_personal_crear(request)

def admin_cuentas(request):
    return redirect('admin_personal')


# ════════════════════════════════════════════════════════════════
# ADMIN — MAQUINARIA
# ════════════════════════════════════════════════════════════════

def admin_maquinaria(request):
    ctx = _base_ctx('Administrador')
    maquinas_bd     = _get('/v1/list/maquinaria/', [])
    tipos_maquina   = _get('/v1/list/tipo_maquinaria/', [])
    estados_maquina = _get('/v1/list/estado_maquinaria/', [])
    lineas_bd       = _get('/v1/list/Linea/', [])

    maquinas = [
        {
            'pk':              m.get('numSerie'),
            'id_maquina':      m.get('numSerie'),
            'tipo':            _FakeObj(nombre=str(m.get('tipoMaquina', '—'))),
            'linea':           _FakeObj(nombre=str(m.get('linea', '—'))),
            'estado':          _FakeObj(nombre=str(m.get('estado', '—'))),
            'operador_actual': _FakeObj(primer_nombre=str(m.get('empleado', '—')),
                                        apellido_paterno=''),
            'created_at':      '—',
        }
        for m in maquinas_bd
    ]
    ctx.update({
        'maquinas':        maquinas,
        'tipos_maquina':   [_FakeObj(pk=t.get('clave'), nombre=t.get('descripcion', ''))
                            for t in tipos_maquina],
        'estados_maquina': [_FakeObj(pk=e.get('clave'), nombre=e.get('descripcion', ''))
                            for e in estados_maquina],
        'lineas':          [_FakeObj(pk=l.get('codigo'), nombre=l.get('nombre', ''))
                            for l in lineas_bd],
        'breadcrumbs': [
            {'label': 'Dashboard',  'url': '/admin-dash/'},
            {'label': 'Maquinaria', 'url': '/admin/maquinaria/'},
        ],
    })
    return render(request, 'admin/maquinaria.html', ctx)


def admin_maquinaria_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/maquinaria/', {
            'numSerie':    request.POST.get('num_serie', ''),
            'nombre':      request.POST.get('nombre', ''),
            'tipoMaquina': request.POST.get('tipo', ''),
            'estado':      request.POST.get('estado', ''),
            'empleado':    request.POST.get('empleado', ''),
            'linea':       request.POST.get('linea', ''),
        })
        if ok:
            messages.success(request, 'Máquina registrada.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_maquinaria')


# ════════════════════════════════════════════════════════════════
# ADMIN — PRODUCCIÓN
# ════════════════════════════════════════════════════════════════

def admin_produccion(request):
    ctx = _base_ctx('Administrador')

    ordenes_bd  = _get('/v1/list/Orden/', [])
    obleas_bd   = _get('/v1/list/Oblea/', [])
    procesos_bd = _get('/v1/list/Proceso/', [])
    pasos_bd    = _get('/v1/list/PasoProceso/', [])

    ordenes = []
    for o in ordenes_bd:
        num  = o.get('numero')
        obs  = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
        total = len(obs)
        comp  = sum(
            1 for ob in obs
            if str(ob.get('estado', '')).lower() in ('completado', 'aprobado', 'co001')
        )
        pct   = round(comp / total * 100) if total > 0 else 0
        edo   = str(o.get('estado', '')).lower()
        if 'aprobado' in edo or 'complet' in edo:
            edo_str = 'aprobado'
        elif 'rechaz' in edo:
            edo_str = 'rechazado'
        elif 'activo' in edo or 'proceso' in edo:
            edo_str = 'en_proceso'
        else:
            edo_str = 'pendiente'

        ordenes.append({
            'pk':          num,
            'numero':      f'ORD-{num:04d}' if isinstance(num, int) else str(num),
            'proceso':     str(o.get('proceso', '—')),
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

        orden_data      = next((o for o in ordenes_bd if str(o.get('numero')) == str(orden_num)), {})
        proceso_codigo  = str(orden_data.get('proceso', ''))
        pasos_de_proceso = sorted(
            [p for p in pasos_bd if str(p.get('proceso')) == proceso_codigo],
            key=lambda x: x.get('orden', 0)
        )
        etapas = [
            {
                'nombre':  str(p.get('paso', 'Paso')),
                'estado':  'pendiente',
                'meta':    None,
                'detalle': None,
            }
            for p in pasos_de_proceso
        ]
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

    ctx.update({
        'ordenes':             ordenes,
        'lotes':               lotes,
        'plantillas':          plantillas,
        'ordenes_json':        json.dumps(ordenes),
        'lotes_json':          json.dumps(lotes),
        'maquinas_disponibles': [],
        'empleados':           [],
        'breadcrumbs': [
            {'label': 'Dashboard',  'url': '/admin-dash/'},
            {'label': 'Producción', 'url': '/admin/produccion/'},
        ],
    })
    return render(request, 'admin/produccion.html', ctx)


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
    return redirect('admin_produccion')


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
    return redirect('admin_produccion')


def supervisor_lote_hold(request, pk):
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'HO001'})
    if not ok:
        messages.error(request, f'Error: {resp}')
    return redirect('admin_produccion')


def supervisor_lote_scrap(request, pk):
    ok, resp = _patch(f'/v1/update/Oblea/{pk}/', {'estado': 'RE001'})
    if not ok:
        messages.error(request, f'Error: {resp}')
    return redirect('admin_produccion')


# ════════════════════════════════════════════════════════════════
# ADMIN — ORGANIZACIÓN
# ════════════════════════════════════════════════════════════════

def admin_organizacion(request):
    ctx = _base_ctx('Administrador')

    procesos_bd  = _get('/v1/list/Proceso/', [])
    tipos_oblea  = _get('/v1/list/TipoOblea/', [])
    lineas_bd    = _get('/v1/list/Linea/', [])
    kpis         = _get('/v1/list/kpis/', [])

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
            'pk':          t.get('codigo'),
            'codigo':      t.get('codigo'),
            'nombre':      t.get('descripcion', ''),
            'dies_maximos': t.get('cantidadDies', 0),
            'activo':      True,
        }
        for t in tipos_oblea
    ]
    lineas = [
        {
            'pk':              l.get('codigo'),
            'nombre':          l.get('nombre', ''),
            'planta':          '—',
            'activo':          True,
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


def admin_config_kpi_save(request):
    if request.method == 'POST':
        clave = request.POST.get('kpi', '')
        ok, resp = _patch(f'/v1/update/kpi/{clave}/', {
            'umbralVerde':    int(request.POST.get('verde', 0)),
            'umbralAmarillo': int(request.POST.get('amarillo', 0)),
            'umbralRojo':     int(request.POST.get('rojo', 0)),
        })
        if ok:
            messages.success(request, 'Umbrales actualizados.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_organizacion')


# ════════════════════════════════════════════════════════════════
# ADMIN — REPORTES
# ════════════════════════════════════════════════════════════════

def admin_reportes(request):
    ctx = _base_ctx('Administrador')

    reportes_bd = _get('/v1/list/reportes/', [])
    ordenes_bd  = _get('/v1/list/Orden/', [])

    ordenes = [
        {
            'pk':     o.get('numero'),
            'numero': f"ORD-{o['numero']:04d}" if isinstance(o.get('numero'), int)
                      else str(o.get('numero', '')),
        }
        for o in ordenes_bd
    ]

    reporte_produccion = []
    for r in reportes_bd:
        apro   = r.get('unidades_apro', 0) or 0
        defect = r.get('unidaes_defect', 0) or 0
        ini    = apro + defect
        yld    = round(apro / ini * 100, 1) if ini > 0 else 0
        num    = r.get('numero', '')
        reporte_produccion.append({
            'folio':          f'REP-{num:04d}' if isinstance(num, int) else str(num),
            'orden':          str(r.get('orden', '—')),
            'operador':       '—',
            'dies_iniciales': ini,
            'dies_finales':   apro,
            'scrap':          defect,
            'yield_pct':      yld,
            'estado':         'Completado',
        })

    total_ini    = sum(f['dies_iniciales'] for f in reporte_produccion)
    total_fin    = sum(f['dies_finales']   for f in reporte_produccion)
    total_scrap  = sum(f['scrap']          for f in reporte_produccion)
    yield_global = round(total_fin / total_ini * 100, 1) if total_ini > 0 else 0

    ctx.update({
        'ordenes':            ordenes,
        'reporte_produccion': reporte_produccion,
        'total_dies_ini':     total_ini,
        'total_dies_fin':     total_fin,
        'total_scrap':        total_scrap,
        'yield_global':       yield_global,
        'reporte_inventario': [],
        'reporte_kpi':        [],
        'todas_alertas':      [],
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/admin-dash/'},
            {'label': 'Reportes',  'url': '/admin/reportes/'},
        ],
    })
    return render(request, 'admin/reportes.html', ctx)


# ════════════════════════════════════════════════════════════════
# ADMIN — ALERTAS
# ════════════════════════════════════════════════════════════════

def admin_notificaciones(request):
    ctx = _base_ctx('Administrador')

    historiales = _get('/v1/list/historiales_alertas/', [])

    _color_map = {
        'activo':   {'bg': '#FFF8E1', 'borde': '#F5A623', 'icon': '#F5A623',
                     'badge': 'Activa',   'badge_color': '#856404'},
        'resuelto': {'bg': '#E8F5EE', 'borde': '#16A85E', 'icon': '#16A85E',
                     'badge': 'Resuelta', 'badge_color': '#155724'},
    }

    alertas = []
    for i, h in enumerate(historiales, 1):
        # El backend devuelve alerta como int (PK) o dict según el serializer
        alerta = h.get('alerta', {})
        if isinstance(alerta, dict):
            desc = alerta.get('descripcion', '')
            num  = alerta.get('numero', '—')
        else:
            desc = str(alerta)
            num  = str(alerta)

        edo_raw = str(h.get('estadoAlerta', 'activo')).lower()
        edo_key = 'activo' if 'activ' in edo_raw else 'resuelto'
        c       = _color_map[edo_key]

        alertas.append({
            'pk':          i,
            'tipo':        'hold' if edo_key == 'activo' else 'liberado',
            'leida':       edo_key != 'activo',
            'titulo':      desc,
            'cuerpo':      desc,
            'tiempo':      f"{h.get('fecha', '—')} {str(h.get('hora', ''))[:5]}",
            'color_bg':    c['bg'],
            'color_borde': c['borde'],
            'color_icon':  c['icon'],
            'badge_label': c['badge'],
            'badge_color': c['badge_color'],
            'ref_label':   'Alerta',
            'ref_valor':   str(num),
            'accion_label': 'Ver detalle',
            'accion_url':  '/admin/reportes/',
        })

    unread = sum(1 for a in alertas if not a['leida'])
    ctx.update({
        'alertas':      alertas,
        'total_count':  len(alertas),
        'unread_count': unread,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/admin-dash/'},
            {'label': 'Alertas',   'url': '/admin/notificaciones/'},
        ],
    })
    return render(request, 'admin/alertas.html', ctx)


# ════════════════════════════════════════════════════════════════
# ADMIN — CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════

def admin_configuracion(request):
    ctx = _base_ctx('Administrador')
    defectos = _get('/v1/list/Defecto/', [])
    ctx.update({
        'kpi_configs':   [],
        'tipos_defecto': [
            _FakeObj(pk=d.get('codigo'), codigo=d.get('codigo', ''),
                     nombre=d.get('descripcion', ''), categoria='—', activo=True)
            for d in defectos
        ],
        'turnos':        [],
        'notif_configs': [],
        'breadcrumbs': [
            {'label': 'Dashboard',     'url': '/admin-dash/'},
            {'label': 'Configuración', 'url': '/admin/configuracion/'},
        ],
    })
    return render(request, 'admin/configuracion.html', ctx)


def admin_config_turno_crear(request):
    return redirect('admin_configuracion')


def admin_config_defecto_crear(request):
    return redirect('admin_configuracion')


def admin_config_change_password(request):
    return redirect('admin_configuracion')


def admin_produccion_plantilla_crear(request):
    return admin_organizacion_plantilla_crear(request)


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — DASHBOARD
# ════════════════════════════════════════════════════════════════

def supervisor_dashboard(request):
    ctx = _base_ctx('Supervisor')

    kpis   = _get('/v1/list/kpis/', [])
    obleas = _get('/v1/list/Oblea/', [])

    lotes_hold = sum(
        1 for o in obleas
        if str(o.get('estado', '')).lower() in ('hold', 'ho001')
    )

    ctx.update({
        'kpi': {
            'yield_pct':        94.2,
            'yield_delta':      '+2.5%',
            'throughput':       498,
            'throughput_delta': '-1.2%',
            'oee_pct':          87.1,
            'oee_delta':        '+11%',
            'lotes_hold':       lotes_hold,
            'lotes_hold_delta': '',
        },
        'throughput_labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'throughput_data':   [7200, 8100, 8900, 7800, 9200, 8500,
                              9800, 10200, 9500, 10800, 11200, 11800],
        'semaforo_kpi':    _build_semaforo(kpis),
        'ordenes_activas': [],
        'alertas_activas': [],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/supervisor/'}],
    })
    return render(request, 'supervisor/dashboard.html', ctx)


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — reutiliza views del admin
# ════════════════════════════════════════════════════════════════

def supervisor_ordenes(request):
    return admin_produccion(request)


def supervisor_lotes(request):
    return redirect('supervisor_ordenes')


def supervisor_lote_detalle(request, pk):
    return redirect('supervisor_ordenes')


def supervisor_inventario(request):
    return admin_inventario(request)


def supervisor_inventario_entrada(request):
    return admin_inventario_movimiento(request)


def supervisor_reportes(request):
    return admin_reportes(request)


def supervisor_notificaciones(request):
    return admin_notificaciones(request)


def supervisor_configuracion(request):
    return redirect('admin_configuracion')


def supervisor_orden_detalle(request, pk=1):
    return redirect('supervisor_ordenes')
