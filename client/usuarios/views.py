import re
from datetime import date
from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from home.views import _base_ctx, _get, _get_many, _post, _patch, _FakeObj, _build_semaforo
from produccion.views import _estado_orden_display
from django.core.paginator import Paginator

PAGE_SIZE_PERSONAL = 9

_RFC_RE = re.compile(r'^[A-Z0-9]{13}$')
_USERNAME_RE = re.compile(r'^[a-z0-9._-]+$')


def _ordenes_activas_reales(ordenes_bd, obleas_bd, procesos_map, limit=5):
    """Órdenes activas reales para el widget de dashboard (admin y
    supervisor comparten este criterio para no divergir de lo que se ve
    al entrar a Producción/Órdenes). Reusa _estado_orden_display —el mismo
    cálculo de estado/progreso que ya usa esa página— en vez de tener una
    segunda fórmula que se pueda desalinear con el tiempo.
    'Activa' = la orden todavía no quedó cerrada (aprobada o rechazada).
    """
    activas = []
    for o in ordenes_bd:
        num = o.get('numero')
        obs = [ob for ob in obleas_bd if str(ob.get('orden')) == str(num)]
        edo_str, comp, pct = _estado_orden_display(o.get('estado'), obs)
        if edo_str in ('aprobado', 'rechazado'):
            continue
        proceso_codigo = str(o.get('proceso', ''))
        activas.append({
            'pk': num,
            'numero': f'ORD-{num:04d}' if isinstance(num, int) else str(num),
            'proceso': procesos_map.get(proceso_codigo, {}).get('nombre') or proceso_codigo or '—',
            'completados': comp,
            'total': len(obs),
            'pct': pct,
            'estado': edo_str,
        })
    activas.sort(key=lambda x: x['pk'] if isinstance(x['pk'], int) else 0, reverse=True)
    return activas[:limit]


def _kpi_produccion_reales(obleas_bd, ordenes_bd, tipos_oblea_bd, pasos_realizados_bd):
    """Yield/Throughput/OEE reales para las tarjetas de producción del
    dashboard (hoy solo las usa supervisor, pero quedan disponibles para
    admin también si se necesitan más adelante).

    OEE es una aproximación: Calidad (yield global) x Disponibilidad
    (fracción de lotes que NO cayeron en Hold). Este proyecto no rastrea
    tiempos de paro de máquina en ningún modelo, así que el factor de
    Rendimiento/Performance de la fórmula OEE clásica no se puede calcular
    con datos reales — se omite en vez de inventar un número.
    """
    tipos_map = {str(t.get('codigo')): t for t in tipos_oblea_bd}
    ordenes_map = {str(o.get('numero')): o for o in ordenes_bd}

    dies_iniciales_total = 0
    dies_activos_total = 0
    lotes_hold_count = 0
    for ob in obleas_bd:
        orden = ordenes_map.get(str(ob.get('orden')))
        tipo_pk = str(orden.get('tipoOblea')) if orden else None
        cantidad_dies = tipos_map.get(tipo_pk, {}).get('cantidadDies') or ob.get('diesGenerados', 0)
        dies_iniciales_total += cantidad_dies
        dies_activos_total += ob.get('diesGenerados', 0)
        if str(ob.get('estado', '')).lower() == 'enhol':
            lotes_hold_count += 1

    yield_pct = round(dies_activos_total / dies_iniciales_total * 100, 1) if dies_iniciales_total > 0 else 0
    disponibilidad = 1 - (lotes_hold_count / len(obleas_bd)) if obleas_bd else 1
    oee_pct = round(yield_pct * disponibilidad, 1)

    hoy = date.today().isoformat()
    throughput = sum(
        1 for pr in pasos_realizados_bd
        if str(pr.get('estado', '')).lower() == 'compl' and str(pr.get('fecha', ''))[:10] == hoy
    )

    return {'yield_pct': yield_pct, 'throughput': throughput, 'oee_pct': oee_pct}


def admin_dashboard(request):
    ctx = _base_ctx('Administrador')
    empleados, maquinas, obleas, ordenes_bd, alertas_bd, procesos_bd = _get_many(
        '/v1/list/empleados/', '/v1/list/maquinaria/',
        '/v1/list/Oblea/', '/v1/list/Orden/', '/v1/list/alertas/', '/v1/list/Proceso/',
    )
    procesos_map = {str(p.get('codigo')): p for p in procesos_bd}
    lotes_hold = sum(1 for o in obleas if str(o.get('estado', '')).lower() == 'enhol')
    ordenes_activas = _ordenes_activas_reales(ordenes_bd, obleas, procesos_map)
    alertas_activas = [{'tipo': 'advertencia', 'descripcion': a.get('descripcion', ''),
        'referencia': f"#{a.get('numero', '—')}", 'tiempo': '—'}
        for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre')][:5]
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {'user_role': 'Administrador', 'unread_count': unread,
        'recent_notifications': [{'titulo': a.get('descripcion', ''), 'tipo': 'alerta',
            'leida': str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre')} for a in alertas_bd[:5]],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/admin-dash/'}]}
    semaforo_kpi, semaforo_columnas = _build_semaforo()
    ctx.update({'kpi': {'cuentas': len(empleados), 'empleados': len(empleados), 'maquinas': len(maquinas),
        'lotes_hold': lotes_hold, 'lotes_hold_delta': ''},
        'semaforo_kpi': semaforo_kpi, 'semaforo_columnas': semaforo_columnas,
        'ordenes_activas': ordenes_activas,
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
            nuevo_estado = 'ina' if estado_actual == 'activo' else 'act'
            if nuevo_estado == 'ina' and str(pk) == str(request.session.get('user_id')):
                messages.error(request, 'No puedes desactivar tu propia cuenta.')
                return redirect('admin_personal')
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
    obleas, ordenes_bd, tipos_oblea_bd, pasos_realizados_bd, alertas_bd, procesos_bd = _get_many(
        '/v1/list/Oblea/', '/v1/list/Orden/', '/v1/list/TipoOblea/',
        '/v1/list/PasoRealizado/', '/v1/list/alertas/', '/v1/list/Proceso/',
    )
    procesos_map = {str(p.get('codigo')): p for p in procesos_bd}
    lotes_hold = sum(1 for o in obleas if str(o.get('estado', '')).lower() == 'enhol')
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    kpi_prod = _kpi_produccion_reales(obleas, ordenes_bd, tipos_oblea_bd, pasos_realizados_bd)
    # Mismo criterio que admin_dashboard para que ambos tengan la misma
    # función real (antes estas dos listas venían hardcodeadas vacías aquí).
    ordenes_activas = _ordenes_activas_reales(ordenes_bd, obleas, procesos_map)
    alertas_activas = [{'tipo': 'advertencia', 'descripcion': a.get('descripcion', ''),
        'referencia': f"#{a.get('numero', '—')}", 'tiempo': '—'}
        for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre')][:5]
    semaforo_kpi, semaforo_columnas = _build_semaforo()
    ctx = {
        'user_role': 'Supervisor', 'unread_count': unread,
        'recent_notifications': [{'titulo': a.get('descripcion', ''), 'tipo': 'alerta',
            'leida': str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre')} for a in alertas_bd[:5]],
        'breadcrumbs': [{'label': 'Dashboard', 'url': '/supervisor/'}],
        'kpi': {'yield_pct': kpi_prod['yield_pct'], 'yield_delta': '',
                'throughput': kpi_prod['throughput'], 'throughput_delta': '',
                'oee_pct': kpi_prod['oee_pct'], 'oee_delta': '',
                'lotes_hold': lotes_hold, 'lotes_hold_delta': ''},
        'semaforo_kpi': semaforo_kpi, 'semaforo_columnas': semaforo_columnas,
        'ordenes_activas': ordenes_activas, 'alertas_activas': alertas_activas,
    }
    return render(request, 'supervisor/dashboard.html', ctx)


def supervisor_configuracion(request):
    return redirect('admin_configuracion')