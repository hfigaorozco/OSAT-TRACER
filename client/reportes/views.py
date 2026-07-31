from django.shortcuts import render
from django.views import View
from home.views import _get, _get_many


def _base_ctx_from_alertas(role, alertas_bd):
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    return {
        'user_role': role,
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


def _empleados_map(empleados_bd):
    return {
        str(e.get('numero', '')): f"{e.get('nombre', '')} {e.get('primerApell', '')}".strip()
        for e in empleados_bd
    }


def _ordenes_cerradas(ordenes_bd, procesos_map, desde, hasta):
    resultado = []
    for o in ordenes_bd:
        if str(o.get('estado', '')).lower() != 'cerra':
            continue
        fecha = str(o.get('horaIni', ''))[:10]
        if desde and fecha < desde:
            continue
        if hasta and fecha > hasta:
            continue
        num = o.get('numero')
        proceso_pk = str(o.get('proceso', ''))
        resultado.append({
            'pk': num,
            'numero': f'ORD-{num:04d}' if isinstance(num, int) else str(num),
            'proceso_nombre': procesos_map.get(proceso_pk, {}).get('nombre', proceso_pk),
        })
    return resultado


def _hora_corta(hora_str):
    s = str(hora_str or '')
    return s[:5] if len(s) >= 5 else s


def _reporte_de_orden(orden_id, ordenes_bd, reportes_bd, empleados_map, procesos_map,obleas_bd,pasos_bd,):
    orden_data = next((o for o in ordenes_bd if str(o.get('numero')) == str(orden_id)), None)
    if not orden_data:
        return None, 'La orden no existe.'
    if str(orden_data.get('estado', '')).lower() != 'cerra':
        return None, 'Solo se puede generar el reporte de una orden ya cerrada.'

    reporte = next((r for r in reportes_bd if str(r.get('orden')) == str(orden_id)), None)
    if not reporte:
        return None, 'Esta orden aún no tiene un reporte generado.'

    obleas = [o for o in obleas_bd if str(o.get("orden")) == str(orden_id)]
    
    dies_finales = sum(int(o.get("diesGenerados", 0) or 0)for o in obleas)
    scrap = 0
    for oblea in obleas:
        scrap += sum(int(p.get("scrap", 0) or 0)for p in pasos_bd if str(p.get("oblea")) == str(oblea.get("numero")))
    
    dies_iniciales = dies_finales + scrap
    
    yield_pct = round(dies_finales / dies_iniciales * 100,1) if dies_iniciales else 0
    
    
    num = orden_data.get('numero')
    empleado_pk = str(orden_data.get('empleado', ''))
    proceso_pk = str(orden_data.get('proceso', ''))

    return {
        'pk': num,
        'numero': f'ORD-{num:04d}' if isinstance(num, int) else str(num),
        'proceso_nombre': procesos_map.get(proceso_pk, {}).get('nombre', proceso_pk),
        'operador': empleados_map.get(empleado_pk, 'Sin asignar'),
        'dies_iniciales': dies_iniciales,
        'dies_finales': dies_finales,
        'scrap': scrap,
        'yield_pct': yield_pct,
        'comentarios': reporte.get('comentarios', ''),
        'fecha': reporte.get('fecha', ''),
        'hora': _hora_corta(reporte.get('hora', '')),
        'numero_reporte': reporte.get('numero', ''),
    }, None


def _reporte_inventario(piezas_bd):
    resultado = []
    for p in piezas_bd:
        actual = p.get('stockActual', 0)
        minimo = p.get('stockMinimo', 0)
        if actual == 0:
            estado = 'Crítico'
        elif actual < minimo:
            estado = 'Bajo'
        else:
            estado = 'OK'
        resultado.append({
            'codigo': p.get('codigo'),
            'nombre': p.get('nombre'),
            'stock_minimo': minimo,
            'stock_actual': actual,
            'estado': estado,
        })
    return resultado


def _reporte_kpi(registros_bd, kpis_bd, semaforos_bd, desde, hasta, kpi_filtro):
    kpi_map = {str(k.get('clave', '')): k for k in kpis_bd}
    sem_map = {str(s.get('codigo', '')): s for s in semaforos_bd}
    resultado = []
    for r in registros_bd:
        fecha = str(r.get('fecha', ''))
        if desde and fecha < desde:
            continue
        if hasta and fecha > hasta:
            continue
        kpi_pk = str(r.get('kpi', ''))
        if kpi_filtro and kpi_pk != kpi_filtro:
            continue
        kpi_data = kpi_map.get(kpi_pk, {})
        valor = r.get('valor', 0) or 0
        verde = kpi_data.get('umbralVerde', 0) or 0
        semaforo_pk = str(r.get('semaforo', ''))
        resultado.append({
            'fecha': fecha,
            'hora': r.get('hora', ''),
            'kpi_nombre': kpi_data.get('nombre', kpi_pk),
            'valor': valor,
            'umbral_verde': verde,
            'umbral_amarillo': kpi_data.get('umbralAmarillo', 0) or 0,
            'umbral_rojo': kpi_data.get('umbralRojo', 0) or 0,
            'semaforo': sem_map.get(semaforo_pk, {}).get('descripcion', '—'),
            'cumple': valor >= verde,
        })
    return resultado


class BaseReportesView(View):
    role = None
    template_name = None
    dashboard_url = None

    def get(self, request):
        (ordenes_bd, reportes_bd, empleados_bd, procesos_bd,
         piezas_bd, registros_kpi_bd, kpis_bd, semaforos_bd, alertas_bd,obleas_bd, pasos_bd,) = _get_many(
            '/v1/list/Orden/',
            '/v1/list/reportes/',
            '/v1/list/empleados/',
            '/v1/list/Proceso/',
            '/v1/list/piezas/',
            '/v1/list/registros_kpi/',
            '/v1/list/kpis/',
            '/v1/list/semaforos/',
            '/v1/list/alertas/',
            '/v1/list/Oblea/',
            '/v1/list/PasoRealizado/',
        )

        empleados_map = _empleados_map(empleados_bd)
        procesos_map = {str(p.get('codigo', '')): p for p in procesos_bd}

        desde = request.GET.get('desde', '')
        hasta = request.GET.get('hasta', '')
        orden_id = request.GET.get('orden_id', '')

        reporte_orden = None
        error_orden = None
        if orden_id:
            reporte_orden, error_orden = _reporte_de_orden(
                orden_id, ordenes_bd, reportes_bd, empleados_map, procesos_map, obleas_bd,pasos_bd,
            )

        kpi_tipo = request.GET.get('kpi_tipo', '')

        ctx = _base_ctx_from_alertas(self.role, alertas_bd)
        ctx.update({
            'ordenes': _ordenes_cerradas(ordenes_bd, procesos_map, desde, hasta),
            'orden_id_actual': orden_id,
            'reporte_orden': reporte_orden,
            'error_orden': error_orden,
            'reporte_inventario': _reporte_inventario(piezas_bd),
            'reporte_kpi': _reporte_kpi(registros_kpi_bd, kpis_bd, semaforos_bd, desde, hasta, kpi_tipo),
            'kpis_catalogo': [{'pk': k.get('clave'), 'nombre': k.get('nombre', '')} for k in kpis_bd],
            'breadcrumbs': [
                {'label': 'Dashboard', 'url': self.dashboard_url},
                {'label': 'Reportes', 'url': ''},
            ],
        })
        return render(request, self.template_name, ctx)


class AdminReportesView(BaseReportesView):
    role = 'Administrador'
    template_name = 'admin/reportes.html'
    dashboard_url = '/admin-dash/'


class SupervisorReportesView(BaseReportesView):
    role = 'Supervisor'
    template_name = 'supervisor/reportes.html'
    dashboard_url = '/supervisor/'