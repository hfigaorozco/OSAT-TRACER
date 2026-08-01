import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from home.views import _base_ctx, _get, _get_many, _post, _patch, _delete, _FakeObj

_CODIGO_RE = re.compile(r'^[a-z0-9-]+$')


def _build_alertas(historiales):
    _color_map = {
        'activo':   {'bg': '#FFF8E1', 'borde': '#F5A623', 'icon': '#F5A623',
                     'badge': 'Activa',   'badge_color': '#856404'},
        'resuelto': {'bg': '#E8F5EE', 'borde': '#16A85E', 'icon': '#16A85E',
                     'badge': 'Resuelta', 'badge_color': '#155724'},
    }
    alertas = []
    for i, h in enumerate(historiales, 1):
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
            'pk':           i,
            'tipo':         'hold' if edo_key == 'activo' else 'liberado',
            'leida':        edo_key != 'activo',
            'titulo':       desc,
            'cuerpo':       desc,
            'tiempo':       f"{h.get('fecha', '—')} {str(h.get('hora', ''))[:5]}",
            'color_bg':     c['bg'],
            'color_borde':  c['borde'],
            'color_icon':   c['icon'],
            'badge_label':  c['badge'],
            'badge_color':  c['badge_color'],
            'ref_label':    'Alerta',
            'ref_valor':    str(num),
            'accion_label': 'Ver detalle',
            'accion_url':   '/admin/reportes/',
        })
    return alertas


# ════════════════════════════════════════════════════════════════
# ADMIN — ALERTAS
# ════════════════════════════════════════════════════════════════

def admin_notificaciones(request):
    historiales, alertas_bd = _get_many(
        '/v1/list/historiales_alertas/',
        '/v1/list/alertas/',
    )
    unread_bd = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Administrador',
        'unread_count': unread_bd,
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
    alertas = _build_alertas(historiales)
    unread  = sum(1 for a in alertas if not a['leida'])
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
# SUPERVISOR — ALERTAS
# ════════════════════════════════════════════════════════════════

def supervisor_notificaciones(request):
    historiales, alertas_bd = _get_many(
        '/v1/list/historiales_alertas/',
        '/v1/list/alertas/',
    )
    unread_bd = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Supervisor',
        'unread_count': unread_bd,
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
    alertas = _build_alertas(historiales)
    unread  = sum(1 for a in alertas if not a['leida'])
    ctx.update({
        'alertas':      alertas,
        'total_count':  len(alertas),
        'unread_count': unread,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Alertas',   'url': '/supervisor/notificaciones/'},
        ],
    })
    return render(request, 'supervisor/alertas.html', ctx)


# ════════════════════════════════════════════════════════════════
# ADMIN — CONFIGURACIÓN (KPI y catálogos) — SOLO ADMIN
# ════════════════════════════════════════════════════════════════

def admin_configuracion(request):
    defectos, paso_defecto_bd, pasos_bd, kpis_bd, empleados_bd, alertas_bd = _get_many(
        '/v1/list/Defecto/',
        '/v1/list/PasoDefecto/',
        '/v1/list/pasos/',
        '/v1/list/kpis/',
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
        for k in kpis_bd
    ]

    mi_empleado = next((e for e in empleados_bd if str(e.get('numero')) == str(request.session.get('user_id'))), {})

    def _parse_fecha(raw):
        if not raw:
            return None
        try:
            return parse_datetime(raw)
        except (TypeError, ValueError):
            return None

    mi_cuenta = {
        'nombre':      f"{mi_empleado.get('nombre', '')} {mi_empleado.get('primerApell', '')}".strip(),
        'username':    mi_empleado.get('username', request.session.get('user_name', '')),
        'email':       mi_empleado.get('email', ''),
        'rol':         mi_empleado.get('rol', ''),
        'last_login':  _parse_fecha(mi_empleado.get('last_login')),
        'date_joined': _parse_fecha(mi_empleado.get('date_joined')),
    }

    pasos_map = {str(p.get('codigo', '')): p for p in pasos_bd}
    pasos_por_defecto = {}
    for rel in paso_defecto_bd:
        pasos_por_defecto.setdefault(str(rel.get('defecto')), []).append(str(rel.get('paso')))

    ctx.update({
        'kpi_cards':     kpi_cards,
        'tipos_defecto': [
            _FakeObj(
                pk=d.get('codigo'), codigo=d.get('codigo', ''),
                nombre=d.get('descripcion', ''), activo=d.get('activo', True),
                pasos=pasos_por_defecto.get(str(d.get('codigo')), []),
                pasos_nombres=', '.join(
                    pasos_map.get(cod, {}).get('nombre', cod)
                    for cod in pasos_por_defecto.get(str(d.get('codigo')), [])
                ),
            )
            for d in defectos
        ],
        'pasos_catalogo': [{'pk': p.get('codigo'), 'nombre': p.get('nombre', '')} for p in pasos_bd],
        'mi_cuenta': mi_cuenta,
        'breadcrumbs': [
            {'label': 'Dashboard',     'url': '/admin-dash/'},
            {'label': 'Configuración', 'url': '/admin/configuracion/'},
        ],
    })
    return render(request, 'admin/configuracion.html', ctx)


def admin_config_kpi_save(request):
    if request.method == 'POST':
        clave = request.POST.get('kpi', '').strip()
        verde_raw    = request.POST.get('verde', '').strip()
        amarillo_raw = request.POST.get('amarillo', '').strip()
        rojo_raw     = request.POST.get('rojo', '').strip()

        errores = []
        if not clave:
            errores.append('No se indicó el KPI a configurar.')
        for etiqueta, raw in (('verde', verde_raw), ('amarillo', amarillo_raw), ('rojo', rojo_raw)):
            if not raw.lstrip('-').isdigit():
                errores.append(f'El umbral {etiqueta} debe ser un número entero.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_configuracion')

        verde, amarillo, rojo = int(verde_raw), int(amarillo_raw), int(rojo_raw)
        if not (verde >= amarillo >= rojo):
            messages.error(request, 'Los umbrales deben cumplir verde ≥ amarillo ≥ rojo.')
            return redirect('admin_configuracion')

        kpis_bd = _get('/v1/list/kpis/', [])
        otros_kpis = [k for k in kpis_bd if str(k.get('clave')) != clave]
        if any(k.get('umbralVerde') == verde for k in otros_kpis):
            errores.append(f'Ya existe otro KPI con umbral verde {verde}.')
        if any(k.get('umbralAmarillo') == amarillo for k in otros_kpis):
            errores.append(f'Ya existe otro KPI con umbral amarillo {amarillo}.')
        if any(k.get('umbralRojo') == rojo for k in otros_kpis):
            errores.append(f'Ya existe otro KPI con umbral rojo {rojo}.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_configuracion')

        ok, resp = _patch(f'/v1/update/kpi/{clave}/', {
            'umbralVerde':    verde,
            'umbralAmarillo': amarillo,
            'umbralRojo':     rojo,
        })
        if ok:
            messages.success(request, 'Umbrales actualizados.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_configuracion')


def admin_config_defecto_crear(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().lower()
        nombre = request.POST.get('nombre', '').strip()
        pasos  = [p.strip() for p in request.POST.getlist('pasos') if p.strip()]

        errores = []
        if not codigo:
            errores.append('El código es obligatorio.')
        elif len(codigo) > 5:
            errores.append('El código no puede tener más de 5 caracteres.')
        elif not _CODIGO_RE.match(codigo):
            errores.append('El código solo puede tener letras minúsculas, números y guiones.')

        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 50:
            errores.append('El nombre no puede tener más de 50 caracteres.')

        if not errores:
            defectos_bd = _get('/v1/list/Defecto/', [])
            if any(str(d.get('codigo', '')).lower() == codigo for d in defectos_bd):
                errores.append(f'Ya existe un tipo de defecto con el código "{codigo}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_configuracion')

        ok, resp = _post('/v1/create/Defecto/', {
            'codigo':      codigo,
            'descripcion': nombre,
        })
        if not ok:
            messages.error(request, f'Error: {resp}')
            return redirect('admin_configuracion')

        errores_pasos = []
        for paso_codigo in pasos:
            ok_rel, resp_rel = _post('/v1/create/PasoDefecto/', {'paso': paso_codigo, 'defecto': codigo})
            if not ok_rel:
                errores_pasos.append(f'{paso_codigo}: {resp_rel}')

        if errores_pasos:
            messages.error(request, 'Tipo de defecto creado, pero no se pudieron ligar todos los pasos: ' + '; '.join(errores_pasos))
        else:
            messages.success(request, 'Tipo de defecto creado.')
    return redirect('admin_configuracion')


def admin_config_defecto_editar(request, pk):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        pasos  = {p.strip() for p in request.POST.getlist('pasos') if p.strip()}

        errores = []
        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 50:
            errores.append('El nombre no puede tener más de 50 caracteres.')

        if not errores:
            defectos_bd = _get('/v1/list/Defecto/', [])
            if any(str(d.get('descripcion', '')).strip().lower() == nombre.lower()
                   and str(d.get('codigo')) != str(pk) for d in defectos_bd):
                errores.append(f'Ya existe un tipo de defecto con el nombre "{nombre}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_configuracion')

        ok, resp = _patch(f'/v1/update/Defecto/{pk}/', {'descripcion': nombre})
        if not ok:
            messages.error(request, f'Error: {resp}')
            return redirect('admin_configuracion')

        # Sincronizar relaciones paso-defecto: agregar las nuevas, quitar las que ya no aplican.
        relaciones_bd = _get('/v1/list/PasoDefecto/', [])
        relaciones_actuales = [r for r in relaciones_bd if str(r.get('defecto')) == str(pk)]
        pasos_actuales = {str(r.get('paso')) for r in relaciones_actuales}

        errores_pasos = []
        for paso_codigo in pasos - pasos_actuales:
            ok_rel, resp_rel = _post('/v1/create/PasoDefecto/', {'paso': paso_codigo, 'defecto': pk})
            if not ok_rel:
                errores_pasos.append(f'{paso_codigo}: {resp_rel}')

        for rel in relaciones_actuales:
            if str(rel.get('paso')) not in pasos:
                _delete(f"/v1/delete/PasoDefecto/{rel.get('id')}/")

        if errores_pasos:
            messages.error(request, 'Tipo de defecto actualizado, pero no se pudieron ligar todos los pasos: ' + '; '.join(errores_pasos))
        else:
            messages.success(request, 'Tipo de defecto actualizado.')
    return redirect('admin_configuracion')


def admin_config_defecto_toggle_estado(request, pk):
    if request.method == 'POST':
        defectos_bd = _get('/v1/list/Defecto/', [])
        d = next((x for x in defectos_bd if str(x.get('codigo')) == str(pk)), None)
        if d:
            nuevo_activo = not d.get('activo', True)
            ok, resp = _patch(f'/v1/update/Defecto/{pk}/', {'activo': nuevo_activo})
            if ok:
                accion = 'activado' if nuevo_activo else 'desactivado'
                messages.success(request, f'Tipo de defecto {accion} correctamente.')
            else:
                messages.error(request, f'Error: {resp}')
    return redirect('admin_configuracion')


def admin_config_change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password     = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errores = []
        if not current_password:
            errores.append('Ingresa tu contraseña actual.')
        if not new_password or len(new_password) < 8:
            errores.append('La nueva contraseña debe tener al menos 8 caracteres.')
        if new_password != confirm_password:
            errores.append('La confirmación no coincide con la nueva contraseña.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_configuracion')

        username = request.session.get('user_name', '')
        ok, _resp = _post('/v1/auth/login/web', {
            'username': username,
            'password': current_password,
        })
        if not ok:
            messages.error(request, 'La contraseña actual no es correcta.')
            return redirect('admin_configuracion')

        pk = request.session.get('user_id')
        ok, resp = _patch(f'/v1/update/empleado/{pk}/', {'password': new_password})
        if ok:
            messages.success(request, 'Contraseña actualizada correctamente.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_configuracion')
