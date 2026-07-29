import re
from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from home.views import _base_ctx, _get, _get_many, _post, _patch, _FakeObj, _build_semaforo
from django.core.paginator import Paginator

PAGE_SIZE_PERSONAL = 9

_RFC_RE = re.compile(r'^[A-Z0-9]{13}$')
_USERNAME_RE = re.compile(r'^[a-z0-9._-]+$')

def admin_dashboard(request):
    ctx = _base_ctx('Administrador')
    empleados, maquinas, kpis, obleas, ordenes_bd, alertas_bd = _get_many(
        '/v1/list/empleados/', '/v1/list/maquinaria/', '/v1/list/kpis/',
        '/v1/list/Oblea/', '/v1/list/Orden/', '/v1/list/alertas/',
    )
    lotes_hold = sum(1 for o in obleas if str(o.get('estado', '')).lower() == 'enhol')
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

ESTADO_MAP = {
    'act': 'Activo', 'ina': 'Inactivo',
    'activo': 'Activo', 'inactivo': 'Inactivo',
}

ESTADO_PK_MAP = {
    'activo': 'act', 'inactivo': 'ina',
    'act': 'act', 'ina': 'ina',
}

def _build_empleados(empleados_bd):
    """Construye la lista de empleados con todos los campos para la tabla unificada."""
    return [
        {
            'pk': e.get('numero'),
            'primer_nombre': e.get('nombre', ''),
            'apellido_paterno': e.get('primerApell', ''),
            'apellido_materno': e.get('seguApell', '') or '',
            'rfc':   e.get('rfc', ''),
            'username': e.get('username', '—'),
            'email':   e.get('email', ''),
            'rol':  _FakeObj(pk=e.get('rol', ''), nombre=e.get('rol', '—')),
            'estado':  _FakeObj(
                pk=ESTADO_PK_MAP.get(str(e.get('estado', '')).lower(), 'act'),
                nombre=ESTADO_MAP.get(str(e.get('estado', '')).lower(), e.get('estado', '—'))
            ),
            'fecha_contrato':   e.get('fechaReg', '—'),
        }
        for e in empleados_bd
    ]


def admin_personal(request):
    empleados_bd, alertas_bd = _get_many(
        '/v1/list/empleados/',
        '/v1/list/alertas/',
    )

    # pk = código corto — es lo que espera el API al crear/editar un
    # empleado (Empleado.rol es FK a Rol, cuya PK es el código corto).
    roles_list = [
        _FakeObj(pk='admin', nombre='Administrador'),
        _FakeObj(pk='super', nombre='Supervisor'),
        _FakeObj(pk='opera', nombre='Operador'),
    ]
    estados_empleado = [
        _FakeObj(pk='act', nombre='Activo'),
        _FakeObj(pk='ina', nombre='Inactivo'),
    ]
    roles_map = {r.pk: r.nombre for r in roles_list}

    empleados_lista = _build_empleados(empleados_bd)

    # Los filtros (texto, rol, estado) se aplican sobre la lista COMPLETA
    # antes de paginar — si se paginara primero, filtrar solo buscaría
    # dentro de la página actual en vez de en todos los empleados.
    q = request.GET.get('q', '').strip().lower()
    rol_filtro = request.GET.get('rol', '')
    estado_filtro = request.GET.get('estado', '')

    if q:
        empleados_lista = [
            e for e in empleados_lista
            if q in e['primer_nombre'].lower()
            or q in e['apellido_paterno'].lower()
            or q in e['username'].lower()
            or q in e['rfc'].lower()
        ]
    if rol_filtro:
        rol_nombre = roles_map.get(rol_filtro, '')
        empleados_lista = [e for e in empleados_lista if e['rol'].nombre == rol_nombre]
    if estado_filtro:
        empleados_lista = [
            e for e in empleados_lista if e['estado'].pk.lower() == estado_filtro.lower()
        ]

    paginator = Paginator(empleados_lista, PAGE_SIZE_PERSONAL)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    filtros_activos = {}
    if q:
        filtros_activos['q'] = q
    if rol_filtro:
        filtros_activos['rol'] = rol_filtro
    if estado_filtro:
        filtros_activos['estado'] = estado_filtro
    personal_extra_params = (urlencode(filtros_activos) + '&') if filtros_activos else ''

    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Administrador',
        'unread_count': unread,
        'recent_notifications': [],
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/admin-dash/'},
            {'label': 'Personal',  'url': '/admin/personal/'},
        ],
    }

    ctx.update({
        'empleados':            page_obj,
        'page_obj':             page_obj,
        'roles_list':           roles_list,
        'estados_empleado':     estados_empleado,
        'q':                    q,
        'rol_filtro':           rol_filtro,
        'estado_filtro':        estado_filtro,
        'personal_extra_params': personal_extra_params,
    })
    return render(request, 'admin/personal.html', ctx)


def admin_personal_crear(request):
    if request.method == 'POST':
        seguApell = request.POST.get('apellido_materno', '').strip()
        nombre = request.POST.get('primer_nombre', '').strip()
        primer_apell = request.POST.get('apellido_paterno', '').strip()
        rfc = request.POST.get('rfc', '').strip().upper()
        rol = request.POST.get('rol', '')
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        email = request.POST.get('email', '').strip()

        errores = []
        if not nombre:
            errores.append('El primer nombre es obligatorio.')
        if not primer_apell:
            errores.append('El apellido paterno es obligatorio.')
        if not rfc:
            errores.append('El RFC es obligatorio.')
        elif not _RFC_RE.match(rfc):
            errores.append('El RFC debe tener exactamente 13 caracteres, solo letras y números.')
        if not rol:
            errores.append('Selecciona un rol.')
        if not username:
            errores.append('El usuario es obligatorio.')
        elif not _USERNAME_RE.match(username):
            errores.append('El usuario solo puede tener letras minúsculas, números, puntos y guiones.')
        if not email:
            errores.append('El correo es obligatorio.')
        else:
            try:
                validate_email(email)
            except DjangoValidationError:
                errores.append('Ingresa un correo válido.')
        if not password or len(password) < 8:
            errores.append('La contraseña debe tener al menos 8 caracteres.')

        if not errores:
            empleados_bd = _get('/v1/list/empleados/', [])
            if any(str(e.get('rfc', '')).upper() == rfc for e in empleados_bd):
                errores.append(f'Ya existe un empleado con el RFC "{rfc}".')
            if any(str(e.get('username', '')).lower() == username for e in empleados_bd):
                errores.append(f'Ya existe un empleado con el usuario "{username}".')
            if any(str(e.get('email', '')).lower() == email.lower() for e in empleados_bd):
                errores.append(f'Ya existe un empleado con el correo "{email}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_personal')

        payload = {
            'nombre': nombre,
            'primerApell': primer_apell,
            'seguApell': seguApell if seguApell else '',
            'rfc': rfc,
            'rol': rol,
            'username': username,
            'password': password,
            'email': email,
        }
        ok, resp = _post('/v1/create/empleado/', payload)
        if ok:
            messages.success(request, f"Empleado {nombre} {primer_apell} creado correctamente.")
        else:
            messages.error(request, f'Error al crear empleado: {resp}')
    return redirect('admin_personal')


def admin_personal_editar(request, pk):
    if request.method == 'POST':
        seguApell = request.POST.get('apellido_materno', '').strip()
        nombre = request.POST.get('primer_nombre', '').strip()
        primer_apell = request.POST.get('apellido_paterno', '').strip()
        estado = request.POST.get('estado', '')
        rol = request.POST.get('rol', '')
        username = request.POST.get('username', '').strip().lower()
        email = request.POST.get('email', '').strip()
        pw = request.POST.get('password', '').strip()

        errores = []
        if not nombre:
            errores.append('El primer nombre es obligatorio.')
        if not primer_apell:
            errores.append('El apellido paterno es obligatorio.')
        if not username:
            errores.append('El usuario es obligatorio.')
        elif not _USERNAME_RE.match(username):
            errores.append('El usuario solo puede tener letras minúsculas, números, puntos y guiones.')
        if not email:
            errores.append('El correo es obligatorio.')
        else:
            try:
                validate_email(email)
            except DjangoValidationError:
                errores.append('Ingresa un correo válido.')
        if pw and len(pw) < 8:
            errores.append('La contraseña debe tener al menos 8 caracteres.')

        if not errores:
            empleados_bd = _get('/v1/list/empleados/', [])
            if any(
                str(e.get('username', '')).lower() == username and str(e.get('numero')) != str(pk)
                for e in empleados_bd
            ):
                errores.append(f'Ya existe otro empleado con el usuario "{username}".')
            if any(
                str(e.get('email', '')).lower() == email.lower() and str(e.get('numero')) != str(pk)
                for e in empleados_bd
            ):
                errores.append(f'Ya existe otro empleado con el correo "{email}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_personal')

        payload = {
            'nombre':      nombre,
            'primerApell': primer_apell,
            'seguApell':   seguApell if seguApell else '',
            'estado':      estado,
            'rol':         rol,
            'username':    username,
            'email':       email,
        }
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
    lotes_hold = sum(1 for o in obleas if str(o.get('estado', '')).lower() == 'enhol')
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