import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.urls import reverse
from home.views import _base_ctx, _get, _get_many, _post, _patch, _delete, _FakeObj

# Importaciones para los horarios del sistema
from core.models import HorarioSistema, ConfiguracionMovil
from django.core.cache import cache
from datetime import datetime

# ── Catálogo de colores/íconos/etiquetas por tipo de alerta ──────────────────
# 'hold' usa el mismo naranja/gold que .badge-hold en osat.css — es el color
# que ya representa "Hold" en toda la app (órdenes, lotes), para no inventar
# un código de color nuevo que el usuario tenga que aprender aparte.

_COLOR_MAP = {
    'stock': {
        'bg': '#FFF8E1', 'borde': '#F5A623', 'icon': '#F5A623',
    },
    'produccion': {
        'bg': '#FFEBEE', 'borde': '#EF5350', 'icon': '#EF5350',
    },
    'kpi': {
        'bg': '#F3E8FD', 'borde': '#8E44AD', 'icon': '#8E44AD',
    },
    'hold': {
        'bg': '#FEF3E2', 'borde': '#F5A623', 'icon': '#F5A623',
    },
}

_TIPO_LABEL = {
    'stock': 'Stock', 'produccion': 'Producción', 'kpi': 'KPI', 'hold': 'Hold',
}

# Códigos fijos del catálogo Estado_Alerta (ver models.EstadoAlerta)
_CODIGO_SIN_RESOLVER = 'sinre'
_CODIGO_RESUELTO = 'resue'


# ── Helpers de estado ──────────────────────────────────────────────────────────

def _estados_alerta_info():
    """
    Regresa:
      - estados_map:      {codigo: descripcion} de todo el catálogo Estado_Alerta
      - codigo_resuelto:   'resue' si existe en el catálogo, si no None
                            (se usa para marcar una alerta como leída/resuelta)
    """
    estados_bd = _get('/v1/list/estados_alerta/', [])
    estados_map = {str(e.get('codigo')): e.get('descripcion', '') for e in estados_bd}
    codigo_resuelto = _CODIGO_RESUELTO if _CODIGO_RESUELTO in estados_map else None
    return estados_map, codigo_resuelto


def _detalle_url(role, tipo, oblea_id, orden_numero):
    """Deep-link real al lote/orden que originó la alerta — antes esto
    siempre mandaba a la lista genérica del tipo (ver historial), sin
    importar qué lote/orden específico estuviera involucrado."""
    try:
        if role == 'Administrador':
            if oblea_id or orden_numero:
                url = reverse('admin_produccion')
                params = []
                if orden_numero:
                    params.append(f'orden={orden_numero}')
                if oblea_id:
                    params.append(f'lote={oblea_id}')
                return url + '?' + '&'.join(params)
            return reverse('admin_inventario') if tipo == 'stock' else reverse('admin_reportes')
        else:
            if oblea_id:
                return reverse('supervisor_lote_detalle', args=[oblea_id])
            if orden_numero:
                return reverse('supervisor_orden_detalle', args=[orden_numero])
            return reverse('supervisor_inventario') if tipo == 'stock' else reverse('supervisor_reportes')
    except Exception:
        return '#'


def _marcar_leida_url(role, pk):
    nombre = 'admin_alerta_marcar_leida' if role == 'Administrador' else 'supervisor_alerta_marcar_leida'
    try:
        return reverse(nombre, args=[pk])
    except Exception:
        return '#'


# ── Construcción de la lista de alertas (usada por admin y supervisor) ───────

def _build_alertas(role):
    # La clasificación (tipo/lote/orden/línea/kpi/paso/defectos/operador) ya
    # viene resuelta desde el backend (osat_tracer/api_kpi/views.py::
    # _construir_alertas_base) — misma fuente que usa la app móvil, así que
    # ambas coinciden siempre. El backend ya la entrega ordenada por más
    # reciente primero (numero descendente).
    alertas_bd = _get('/v1/list/alertas/', [])

    alertas = []
    for a in alertas_bd:
        num = a.get('numero')
        tipo = a.get('tipo', 'stock')
        leida = bool(a.get('leida'))
        oblea_id = a.get('oblea_id')
        orden_numero = a.get('orden_numero')

        colores = _COLOR_MAP.get(tipo, _COLOR_MAP['stock'])
        alertas.append({
            'pk': num,
            'tipo': tipo,
            'tipo_label': _TIPO_LABEL.get(tipo, tipo.capitalize()),
            'leida': leida,
            'titulo': a.get('descripcion', ''),
            'tiempo': f"{a.get('fecha', '—')} {str(a.get('hora', ''))[:5]}",
            'color_bg': colores['bg'],
            'color_borde': colores['borde'],
            'color_icon': colores['icon'],
            'badge_label': 'Resuelta' if leida else 'Sin resolver',
            'badge_color': '#155724' if leida else '#B71C1C',
            'folio_lote': a.get('folio_lote'),
            'folio_orden': a.get('folio_orden'),
            'linea_nombre': a.get('linea_nombre'),
            'empleado_nombre': a.get('empleado_nombre'),
            'kpi_nombre': a.get('kpi_nombre'),
            'kpi_valor': a.get('kpi_valor'),
            'kpi_umbral_verde': a.get('kpi_umbral_verde'),
            'kpi_umbral_amarillo': a.get('kpi_umbral_amarillo'),
            'kpi_umbral_rojo': a.get('kpi_umbral_rojo'),
            'kpi_semaforo': a.get('kpi_semaforo'),
            'paso_nombre': a.get('paso_nombre'),
            'paso_scrap': a.get('paso_scrap'),
            'defectos': a.get('defectos') or [],
            'tiene_detalle': bool(oblea_id or orden_numero),
            'detalle_url': _detalle_url(role, tipo, oblea_id, orden_numero),
            'marcar_url': _marcar_leida_url(role, num),
        })

    return alertas


# ════════════════════════════════════════════════════════════════
# ADMIN — ALERTAS
# ════════════════════════════════════════════════════════════════

def admin_notificaciones(request):
    ctx = _base_ctx('Administrador')
    alertas = _build_alertas('Administrador')
    unread  = sum(1 for a in alertas if not a['leida'])
    ctx.update({
        'alertas': alertas,
        'total_count':  len(alertas),
        'unread_count': unread,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/admin-dash/'},
            {'label': 'Alertas',   'url': '/admin/notificaciones/'},
        ],
    })
    return render(request, 'admin/alertas.html', ctx)


def admin_alerta_marcar_leida(request, pk):
    if request.method == 'POST':
        _estados_map, codigo_resuelto = _estados_alerta_info()
        if not codigo_resuelto:
            messages.error(request, 'No hay un estado "resuelto" configurado en el catálogo Estado_Alerta.')
        else:
            ok, resp = _patch(f'/v1/update/alerta/{pk}/', {'estadoAlerta': codigo_resuelto})
            if ok:
                messages.success(request, 'Alerta marcada como resuelta.')
            else:
                messages.error(request, f'Error: {resp}')
    return redirect('admin_notificaciones')


def admin_alertas_marcar_todas_leidas(request):
    if request.method == 'POST':
        _estados_map, codigo_resuelto = _estados_alerta_info()
        if not codigo_resuelto:
            messages.error(request, 'No hay un estado "resuelto" configurado en el catálogo Estado_Alerta.')
        else:
            alertas_bd = _get('/v1/list/alertas/', [])
            marcadas, errores = 0, []
            for a in alertas_bd:
                edo_codigo = str(a.get('estadoAlerta', ''))
                if edo_codigo == _CODIGO_SIN_RESOLVER:
                    ok, resp = _patch(f"/v1/update/alerta/{a.get('numero')}/", {'estadoAlerta': codigo_resuelto})
                    if ok:
                        marcadas += 1
                    else:
                        errores.append(str(resp))
            if errores:
                messages.error(request, f'Se marcaron {marcadas}, pero hubo errores en algunas.')
            else:
                messages.success(request, f'{marcadas} alerta(s) marcada(s) como resueltas.')
    return redirect('admin_notificaciones')


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — ALERTAS (sin tocar la UI todavía, pero ya clasifica bien)
# ════════════════════════════════════════════════════════════════

def supervisor_notificaciones(request):
    ctx = _base_ctx('Supervisor')
    alertas = _build_alertas('Supervisor')
    unread = sum(1 for a in alertas if not a['leida'])
    ctx.update({
        'alertas': alertas,
        'total_count': len(alertas),
        'unread_count': unread,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Alertas', 'url': '/supervisor/notificaciones/'},
        ],
    })
    return render(request, 'supervisor/alertas.html', ctx)


def supervisor_alerta_marcar_leida(request, pk):
    if request.method == 'POST':
        _estados_map, codigo_resuelto = _estados_alerta_info()
        if not codigo_resuelto:
            messages.error(request, 'No hay un estado "resuelto" configurado en el catálogo Estado_Alerta.')
        else:
            ok, resp = _patch(f'/v1/update/alerta/{pk}/', {'estadoAlerta': codigo_resuelto})
            if ok:
                messages.success(request, 'Alerta marcada como resuelta.')
            else:
                messages.error(request, f'Error: {resp}')
    return redirect('supervisor_notificaciones')


def supervisor_alertas_marcar_todas_leidas(request):
    if request.method == 'POST':
        _estados_map, codigo_resuelto = _estados_alerta_info()
        if not codigo_resuelto:
            messages.error(request, 'No hay un estado "resuelto" configurado en el catálogo Estado_Alerta.')
        else:
            alertas_bd = _get('/v1/list/alertas/', [])
            marcadas, errores = 0, []
            for a in alertas_bd:
                edo_codigo = str(a.get('estadoAlerta', ''))
                if edo_codigo == _CODIGO_SIN_RESOLVER:
                    ok, resp = _patch(f"/v1/update/alerta/{a.get('numero')}/", {'estadoAlerta': codigo_resuelto})
                    if ok:
                        marcadas += 1
                    else:
                        errores.append(str(resp))
            if errores:
                messages.error(request, f'Se marcaron {marcadas}, pero hubo errores en algunas.')
            else:
                messages.success(request, f'{marcadas} alerta(s) marcada(s) como resueltas.')
    return redirect('supervisor_notificaciones')

# ════════════════════════════════════════════════════════════════
# ADMIN — CONFIGURACIÓN (KPI y catálogos) — SOLO ADMIN
# ════════════════════════════════════════════════════════════════

def admin_configuracion(request):
    defectos, paso_defecto_bd, pasos_bd, kpis_bd, empleados_bd = _get_many(
        '/v1/list/Defecto/',
        '/v1/list/PasoDefecto/',
        '/v1/list/pasos/',
        '/v1/list/kpis/',
        '/v1/list/empleados/',
    )
    # unread_count/recent_notifications los pone home.context_processors.
    # notificaciones() para toda la app — no armarlos aquí a mano, porque
    # el contexto explícito de esta vista gana sobre el del context
    # processor y tapaba el valor correcto (icono/color/tipo reales) con
    # una forma vieja que dejaba la campana rota en esta página.
    ctx = {
        'user_role': 'Administrador',
        'breadcrumbs': [],
    }

    kpi_cards = [
        {
            'nombre':         k.get('nombre', ''),
            'key':            k.get('clave', ''),
            'unidad':         k.get('unidad', '%'),
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
        'horario_sistema': HorarioSistema.obtener(),
        'configuracion_movil': ConfiguracionMovil.obtener(),
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
        kpi_actual = next((k for k in kpis_bd if str(k.get('clave')) == clave), None)
        if kpi_actual and kpi_actual.get('unidad') == '%' and max(verde, amarillo, rojo) > 100:
            messages.error(request, 'Un umbral en porcentaje no puede ser mayor a 100%.')
            return redirect('admin_configuracion')

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
        new_password = request.POST.get('new_password', '')
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


def admin_config_horario_save(request):
    if request.method == 'POST':
        inicio_raw = request.POST.get('hora_inicio', '').strip()
        fin_raw = request.POST.get('hora_fin', '').strip()

        try:
            hora_inicio = datetime.strptime(inicio_raw, '%H:%M').time()
            hora_fin = datetime.strptime(fin_raw, '%H:%M').time()
        except ValueError:
            messages.error(request, 'Formato de hora inválido.')
            return redirect('admin_configuracion')

        if hora_inicio >= hora_fin:
            messages.error(request, 'La hora de inicio debe ser menor a la hora de fin.')
            return redirect('admin_configuracion')

        horario = HorarioSistema.obtener()
        horario.hora_inicio = hora_inicio
        horario.hora_fin = hora_fin
        horario.save()

        messages.success(request, 'Horario del sistema actualizado.')
    return redirect('admin_configuracion')


# Guardado de la app móvil — independiente del horario laboral (modelo,
# form y vista propios; ConfiguracionMovil no toca HorarioSistema).
def admin_config_movil_save(request):
    if request.method == 'POST':
        inactividad_raw = request.POST.get('inactividad_minutos', '').strip()

        if not inactividad_raw.isdigit() or not (1 <= int(inactividad_raw) <= 480):
            messages.error(request, 'La inactividad debe ser un número entre 1 y 480 minutos.')
            return redirect('admin_configuracion')

        config = ConfiguracionMovil.obtener()
        config.inactividad_minutos = int(inactividad_raw)
        config.save()

        messages.success(request, 'Configuración de la app móvil actualizada.')
    return redirect('admin_configuracion')