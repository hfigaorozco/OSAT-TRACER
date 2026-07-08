import time
from django.shortcuts import render, redirect
from django.contrib import messages
from home.views import _base_ctx, _get, _get_many, _post, _patch, _FakeObj, _build_semaforo


# ════════════════════════════════════════════════════════════════
# ADMIN — DASHBOARD
# ════════════════════════════════════════════════════════════════

def admin_dashboard(request):
    t0 = time.time()

    empleados, maquinas, kpis, obleas, ordenes_bd, alertas_bd = _get_many(
        '/v1/list/empleados/',
        '/v1/list/maquinaria/',
        '/v1/list/kpis/',
        '/v1/list/Oblea/',
        '/v1/list/Orden/',
        '/v1/list/alertas/',
    )
    t1 = time.time()
    print(f"_get_many tardó: {t1-t0:.3f}s")

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
    t2 = time.time()
    print(f"ctx.update tardó: {t2-t1:.3f}s")

    result = render(request, 'admin/dashboard.html', ctx)
    t3 = time.time()
    print(f"render tardó: {t3-t2:.3f}s")
    print(f"TOTAL: {t3-t0:.3f}s")
    return result


# ════════════════════════════════════════════════════════════════
# ADMIN — PERSONAL Y CUENTAS
# ════════════════════════════════════════════════════════════════

def admin_personal(request):
    empleados_bd, alertas_bd = _get_many(
        '/v1/list/empleados/',
        '/v1/list/alertas/',
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


def admin_cuentas(request):
    return redirect('admin_personal')


def admin_cuentas_crear(request):
    return admin_personal_crear(request)


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — DASHBOARD
# ════════════════════════════════════════════════════════════════

def supervisor_dashboard(request):
    kpis, obleas, alertas_bd = _get_many(
        '/v1/list/kpis/',
        '/v1/list/Oblea/',
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


def supervisor_configuracion(request):
    return redirect('admin_configuracion')
