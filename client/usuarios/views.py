from django.shortcuts import render, redirect
from django.contrib import messages
from home.views import _base_ctx, _get, _get_many, _post, _patch, _FakeObj, _build_semaforo
from django.core.paginator import Paginator

def admin_dashboard(request):
    ctx = _base_ctx('Administrador')
    empleados, maquinas, kpis, obleas, ordenes_bd, alertas_bd = _get_many(
        '/v1/list/empleados/', '/v1/list/maquinaria/', '/v1/list/kpis/',
        '/v1/list/Oblea/', '/v1/list/Orden/', '/v1/list/alertas/',
    )
    lotes_hold = sum(1 for o in obleas if str(o.get('estado', '')).lower() in ('hold', 'ho001'))
    ordenes_activas = [{'numero': f"ORD-{o['numero']:04d}" if isinstance(o.get('numero'), int) else str(o.get('numero', '')),
        'proceso': str(o.get('proceso', '—')), 'completados': 0, 'total': 1, 'pct': 0, 'estado': 'en_proceso'}
        for o in ordenes_bd[:5]]
    alertas_activas = [{'tipo': 'advertencia', 'descripcion': a.get('descripcion', ''),
        'referencia': f"#{a.get('numero', '—')}", 'tiempo': '—'}
        for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre')][:5]
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {'user_role': 'Administrador', 'unread_count': unread,
        'recent_notifications': [{'titulo': a.get('descripcion', ''), 'tipo': 'alerta',
            'leida': str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre')} for a in alertas_bd[:5]],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}]}
    ctx.update({'kpi': {'cuentas': len(empleados), 'empleados': len(empleados), 'maquinas': len(maquinas),
        'lotes_hold': lotes_hold, 'lotes_hold_delta': ''},
        'semaforo_kpi': _build_semaforo(kpis), 'ordenes_activas': ordenes_activas,
        'alertas_activas': alertas_activas})
    return render(request, 'admin/dashboard.html', ctx)


# ════════════════════════════════════════════════════════════════
# ADMIN — PERSONAL (tabla unificada)
# ════════════════════════════════════════════════════════════════

def _build_empleados(empleados_bd):
    """Construye la lista de empleados con todos los campos para la tabla unificada."""
    return [
        {
            'pk':               e.get('numero'),
            'primer_nombre':    e.get('nombre', ''),
            'apellido_paterno': e.get('primerApell', ''),
            'apellido_materno': e.get('seguApell', '') or '',
            'rfc':              e.get('rfc', ''),
            'username':         e.get('username', '—'),
            'email':            e.get('email', ''),
            'rol':              _FakeObj(pk=e.get('rol', ''), nombre=e.get('rol', '—')),
            'estado':           _FakeObj(pk=e.get('estado', ''), nombre=e.get('estado', '—')),
            'fecha_contrato':   e.get('fechaReg', '—'),
        }
        for e in empleados_bd
    ]


def admin_personal(request):
    empleados_bd, alertas_bd = _get_many(
        '/v1/list/empleados/',
        '/v1/list/alertas/',
    )

    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role':    'Administrador',
        'unread_count': unread,
        'recent_notifications': [],
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/admin-dash/'},
            {'label': 'Personal',  'url': '/admin/personal/'},
        ],
    }

    roles_list = [
        _FakeObj(pk='admin', nombre='Administrador'),
        _FakeObj(pk='super', nombre='Supervisor'),
        _FakeObj(pk='opera', nombre='Operador'),
    ]
    estados_empleado = [
        _FakeObj(pk='act', nombre='Activo'),
        _FakeObj(pk='ina', nombre='Inactivo'),
    ]

    empleados_lista = _build_empleados(empleados_bd)
    paginator = Paginator(empleados_lista, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    ctx.update({
        'empleados':        page_obj,
        'page_obj':         page_obj,
        'roles_list':       roles_list,
        'estados_empleado': estados_empleado,
    })
    return render(request, 'admin/personal.html', ctx)

def admin_personal_crear(request):
    if request.method == 'POST':
        seguApell = request.POST.get('apellido_materno', '').strip()
        payload = {
            'nombre':      request.POST.get('primer_nombre', '').strip(),
            'primerApell': request.POST.get('apellido_paterno', '').strip(),
            'seguApell':   seguApell if seguApell else '',
            'rfc':         request.POST.get('rfc', '').strip().upper(),
            'estado':      request.POST.get('estado', ''),
            'rol':         request.POST.get('rol', ''),
            'username':    request.POST.get('username', '').strip().lower(),
            'password':    request.POST.get('password', ''),
            'email':       request.POST.get('email', '').strip(),
        }
        ok, resp = _post('/v1/create/empleado/', payload)
        if ok:
            messages.success(request, f"Empleado {payload['nombre']} {payload['primerApell']} creado correctamente.")
        else:
            messages.error(request, f'Error al crear empleado: {resp}')
    return redirect('admin_personal')


def admin_personal_editar(request, pk):
    if request.method == 'POST':
        seguApell = request.POST.get('apellido_materno', '').strip()
        payload = {
            'nombre':      request.POST.get('primer_nombre', '').strip(),
            'primerApell': request.POST.get('apellido_paterno', '').strip(),
            'seguApell':   seguApell if seguApell else '',
            'estado':      request.POST.get('estado', ''),
            'rol':         request.POST.get('rol', ''),
            'username':    request.POST.get('username', '').strip().lower(),
            'email':       request.POST.get('email', '').strip(),
        }
        pw = request.POST.get('password', '').strip()
        if pw:
            payload['password'] = pw
        ok, resp = _patch(f'/v1/update/empleado/{pk}/', payload)
        if ok:
            messages.success(request, 'Empleado actualizado correctamente.')
        else:
            messages.error(request, f'Error al actualizar: {resp}')
    return redirect('admin_personal')


def admin_personal_toggle_estado(request, pk):
    if request.method == 'POST':
        empleados = _get('/v1/list/empleados/', [])
        emp = next((e for e in empleados if str(e.get('numero')) == str(pk)), None)
        if emp:
            estado_actual = str(emp.get('estado', '')).lower()
            nuevo_estado = 'ina' if 'activ' in estado_actual else 'act'
            ok, resp = _patch(f'/v1/update/empleado/{pk}/', {
                'nombre':      emp.get('nombre', ''),
                'primerApell': emp.get('primerApell', ''),
                'seguApell':   emp.get('seguApell', ''),
                'estado':      nuevo_estado,
            })
            if ok:
                accion = 'desactivado' if nuevo_estado == 'ina' else 'activado'
                messages.success(request, f'Empleado {accion} correctamente.')
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
        '/v1/list/kpis/', '/v1/list/Oblea/', '/v1/list/alertas/',
    )
    lotes_hold = sum(1 for o in obleas if str(o.get('estado', '')).lower() in ('hold', 'ho001'))
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Supervisor', 'unread_count': unread,
        'recent_notifications': [],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/supervisor/'}],
        'kpi': {'yield_pct': 94.2, 'yield_delta': '+2.5%', 'throughput': 498,
                'throughput_delta': '-1.2%', 'oee_pct': 87.1, 'oee_delta': '+11%',
                'lotes_hold': lotes_hold, 'lotes_hold_delta': ''},
        'semaforo_kpi': _build_semaforo(kpis),
        'ordenes_activas': [], 'alertas_activas': [],
    }
    return render(request, 'supervisor/dashboard.html', ctx)


def supervisor_configuracion(request):
    return redirect('admin_configuracion')
