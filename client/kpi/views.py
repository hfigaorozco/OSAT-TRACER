from django.shortcuts import render, redirect
from django.contrib import messages
from home.views import _base_ctx, _get, _get_many, _patch, _FakeObj


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
    defectos, alertas_bd = _get_many(
        '/v1/list/Defecto/',
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


def admin_config_turno_crear(request):
    return redirect('admin_configuracion')


def admin_config_defecto_crear(request):
    return redirect('admin_configuracion')


def admin_config_change_password(request):
    return redirect('admin_configuracion')
