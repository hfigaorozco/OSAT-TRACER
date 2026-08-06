from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from django.views import View
from home.views import _get, _get_many, _post, BACKEND_URL
from produccion.views import _generar_reporte_manual

PAGE_SIZE_REPORTES = 9

MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}


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


def _tipo_label(tipo_generacion):
    return 'Manual' if tipo_generacion == 'manual' else 'Automático'


def _rango_str(fecha_inicio, fecha_fin):
    if not fecha_fin:
        return f"Desde {fecha_inicio}"
    return f"{fecha_inicio} a {fecha_fin}"


class BaseReportesView(View):
    """Página de Reportes: 3 pestañas (Producción/Inventario/KPI), cada una
    con la lista PAGINADA de reportes ya generados (ya no se recalcula nada
    en vivo aquí — cada reporte es una foto fija de cuando se generó)."""
    role = None
    template_name = None
    dashboard_url = None

    def get(self, request):
        anio_anterior, mes_anterior = _mes_anterior()
        _generar_mensual_si_no_existe(anio_anterior, mes_anterior, 'auto', None)

        (empleados_bd, alertas_bd, reportes_prod, reportes_inv, reportes_kpi,
         ordenes_bd, obleas_bd) = _get_many(
            '/v1/list/empleados/', '/v1/list/alertas/',
            '/v1/list/reportes/', '/v1/list/reportes_inventario/', '/v1/list/reportes_kpi/',
            '/v1/list/Orden/', '/v1/list/Oblea/',
        )
        empleados_map = _empleados_map(empleados_bd)

        # Para el picker del modal "Generar reporte" de la pestaña
        # Producción — deja elegir cualquier orden o lote sin tener que
        # ir primero a Producción a abrirlo.
        ordenes_picker = sorted(
            [{'numero': o.get('numero'), 'folio': f"ORD-{o.get('numero', 0):04d}"} for o in ordenes_bd],
            key=lambda x: x['numero'], reverse=True,
        )
        lotes_picker = sorted(
            [{
                'numero': l.get('numero'),
                'folio': f"LOT-{l.get('numero', 0):04d}",
                'orden_numero': l.get('orden'),
                'orden_folio': f"ORD-{l.get('orden', 0):04d}",
            } for l in obleas_bd],
            key=lambda x: x['numero'], reverse=True,
        )

        reportes_prod = sorted(reportes_prod, key=lambda r: (r.get('fecha', ''), r.get('hora', '')), reverse=True)
        reportes_inv = sorted(reportes_inv, key=lambda r: r.get('fecha_generado', ''), reverse=True)
        reportes_kpi = sorted(reportes_kpi, key=lambda r: r.get('fecha_generado', ''), reverse=True)

        # Reporte de orden más reciente por cada orden (para vincular el
        # reporte de un lote de esa orden con su reporte "padre", si existe).
        # Se usa "numero" (autoincremental) y no "fecha" porque los reportes
        # "auto" antiguos pueden traer una fecha sembrada que no refleja
        # cuándo se generaron de verdad.
        reporte_padre_de_orden = {}
        for r in sorted(reportes_prod, key=lambda r: r.get('numero', 0), reverse=True):
            if not r.get('oblea') and r.get('orden') not in reporte_padre_de_orden:
                reporte_padre_de_orden[r.get('orden')] = r.get('numero')

        # Reportes de orden y de lote van en sub-pestañas separadas dentro de
        # Producción — antes era una sola lista mezclada con un <select> para
        # filtrar; ahora son dos listas/paginadores independientes desde el
        # origen, así nunca se mezclan.
        prod_rows_orden = []
        prod_rows_lote = []
        for r in reportes_prod:
            es_lote = bool(r.get('oblea'))
            padre_numero = reporte_padre_de_orden.get(r.get('orden')) if es_lote else None
            if padre_numero == r.get('numero'):
                padre_numero = None
            fila = {
                'numero': r.get('numero'),
                'alcance': f"Lote LOT-{r['oblea']:04d}" if es_lote else f"Orden ORD-{r.get('orden', 0):04d}",
                'orden_ref': f"ORD-{r.get('orden', 0):04d}",
                'padre_numero': padre_numero,
                'fecha': r.get('fecha', ''),
                'tipo': _tipo_label(r.get('tipo_generacion')),
                'generado_por': empleados_map.get(str(r.get('generado_por')), '—') if r.get('generado_por') else 'Sistema',
                'dies_finales': r.get('unidades_apro'),
                'scrap': r.get('unidaes_defect'),
            }
            (prod_rows_lote if es_lote else prod_rows_orden).append(fila)

        inv_rows = [{
            'numero': r.get('numero'),
            'rango': _rango_str(r.get('fecha_inicio', ''), r.get('fecha_fin')),
            'fecha_generado': str(r.get('fecha_generado', ''))[:16].replace('T', ' '),
            'tipo': _tipo_label(r.get('tipo_generacion')),
            'generado_por': empleados_map.get(str(r.get('generado_por')), '—') if r.get('generado_por') else 'Sistema',
            'materiales': (r.get('snapshot') or {}).get('materiales', 0),
            'bajo_minimo': (r.get('snapshot') or {}).get('bajo_minimo', 0),
        } for r in reportes_inv]

        kpi_rows = [{
            'numero': r.get('numero'),
            'rango': _rango_str(r.get('fecha_inicio', ''), r.get('fecha_fin')),
            'fecha_generado': str(r.get('fecha_generado', ''))[:16].replace('T', ' '),
            'tipo': _tipo_label(r.get('tipo_generacion')),
            'generado_por': empleados_map.get(str(r.get('generado_por')), '—') if r.get('generado_por') else 'Sistema',
            'kpis_evaluados': len((r.get('snapshot') or {}).get('filas', [])),
        } for r in reportes_kpi]

        page_prod_orden = Paginator(prod_rows_orden, PAGE_SIZE_REPORTES).get_page(request.GET.get('page_prod_orden', 1))
        page_prod_lote = Paginator(prod_rows_lote, PAGE_SIZE_REPORTES).get_page(request.GET.get('page_prod_lote', 1))
        page_inv = Paginator(inv_rows, PAGE_SIZE_REPORTES).get_page(request.GET.get('page_inv', 1))
        page_kpi = Paginator(kpi_rows, PAGE_SIZE_REPORTES).get_page(request.GET.get('page_kpi', 1))

        ctx = _base_ctx_from_alertas(self.role, alertas_bd)
        ctx.update({
            'backend_url': BACKEND_URL,
            'reportes_produccion_orden_page': page_prod_orden,
            'reportes_produccion_lote_page': page_prod_lote,
            'reportes_inventario_page': page_inv,
            'reportes_kpi_page': page_kpi,
            'extra_params_prod_orden': "tab=produccion&subtab_prod=orden&",
            'extra_params_prod_lote': "tab=produccion&subtab_prod=lote&",
            'ordenes_picker': ordenes_picker,
            'lotes_picker': lotes_picker,
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


class BaseReportesGenerarView(View):
    """POST para generar un reporte de inventario o KPI (fecha_inicio/fecha_fin
    en el body) desde el modal de Reportes. El de producción no pasa por
    aquí — se genera directo desde la orden/lote (ver produccion/views.py).
    No redirige a la página de Reportes: se queda donde el usuario estaba
    (HTTP_REFERER) y avisa con una notificación que trae un botón "Ver"."""
    redirect_url_name = None

    def post(self, request):
        tipo = request.POST.get('tipo', '')
        fecha_inicio = request.POST.get('fecha_inicio', '').strip()
        fecha_fin = request.POST.get('fecha_fin', '').strip()
        generado_por = request.session.get('user_id')
        volver = request.META.get('HTTP_REFERER') or reverse(self.redirect_url_name)

        if not fecha_inicio:
            messages.error(request, 'Indica la fecha de inicio.')
            return redirect(volver)
        # El reporte de KPI puede quedar sin fecha_fin ("hasta ahora") — igual
        # que el semáforo en vivo del dashboard — porque exigir una fecha_fin
        # concreta puede dejar fuera lecturas de Registro_Kpi más recientes.
        if tipo == 'inventario' and not fecha_fin:
            messages.error(request, 'Indica el rango de fechas.')
            return redirect(volver)

        endpoint = {
            'inventario': '/v1/create/reporte_inventario/',
            'kpi': '/v1/create/reporte_kpi/',
        }.get(tipo)
        if not endpoint:
            messages.error(request, 'Tipo de reporte no válido.')
            return redirect(volver)

        ok, resp = _post(endpoint, {
            'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin or None,
            'tipo_generacion': 'manual', 'generado_por': generado_por,
        })
        if ok:
            ver_url = f"{reverse(self.redirect_url_name)}?tab={tipo}"
            messages.success(request, 'Reporte generado correctamente.', extra_tags=ver_url)
        else:
            messages.error(request, f'Error: {resp}')
        return redirect(volver)


class AdminReportesGenerarView(BaseReportesGenerarView):
    redirect_url_name = 'admin_reportes'


class SupervisorReportesGenerarView(BaseReportesGenerarView):
    redirect_url_name = 'supervisor_reportes'


class BaseReportesGenerarProduccionView(View):
    """POST para generar un reporte de producción (de una orden completa o
    de un lote específico, elegido en el picker de la pestaña Producción
    de Reportes) sin tener que ir primero a Producción a abrirlo. Reusa
    el mismo cálculo que el botón "Generar reporte" de la orden/lote."""
    redirect_url_name = None

    def post(self, request):
        orden_id = request.POST.get('orden_id', '').strip()
        oblea_id = request.POST.get('oblea_id', '').strip()
        if not orden_id:
            messages.error(request, 'Selecciona una orden o un lote.')
        else:
            _generar_reporte_manual(
                request, orden_id, oblea_num=oblea_id or None,
                reportes_url_name=self.redirect_url_name,
            )
        return redirect(f"{reverse(self.redirect_url_name)}?tab=produccion")


class AdminReportesGenerarProduccionView(BaseReportesGenerarProduccionView):
    redirect_url_name = 'admin_reportes'


class SupervisorReportesGenerarProduccionView(BaseReportesGenerarProduccionView):
    redirect_url_name = 'supervisor_reportes'


def _mes_anterior():
    hoy = date.today()
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    return ultimo_dia_mes_anterior.year, ultimo_dia_mes_anterior.month


def _generar_mensual_si_no_existe(anio, mes, tipo_generacion, generado_por):
    """Idempotente gracias al UniqueConstraint(anio, mes) del backend — si ya
    existe, no hace nada. Esta es la 'generación diferida': no hay ningún
    cron corriendo, se revisa cada vez que alguien visita la página."""
    existentes = _get('/v1/list/reportes_mensuales/', [])
    if any(r.get('anio') == anio and r.get('mes') == mes for r in existentes):
        return
    _post('/v1/create/reporte_mensual/', {
        'anio': anio, 'mes': mes,
        'tipo_generacion': tipo_generacion, 'generado_por': generado_por,
    })


class BaseReportesMensualesView(View):
    role = None
    template_name = None
    dashboard_url = None
    redirect_url_name = None

    def get(self, request):
        anio_anterior, mes_anterior = _mes_anterior()
        _generar_mensual_si_no_existe(anio_anterior, mes_anterior, 'auto', None)

        empleados_bd, alertas_bd, reportes = _get_many(
            '/v1/list/empleados/', '/v1/list/alertas/', '/v1/list/reportes_mensuales/',
        )
        empleados_map = _empleados_map(empleados_bd)
        reportes = sorted(reportes, key=lambda r: (r.get('anio', 0), r.get('mes', 0)), reverse=True)

        rows = []
        for r in reportes:
            snap_prod = r.get('snapshot_produccion') or {}
            snap_inv = r.get('snapshot_inventario') or {}
            rows.append({
                'numero': r.get('numero'),
                'periodo': f"{MESES.get(r.get('mes'), r.get('mes'))} {r.get('anio')}",
                'fecha_generado': str(r.get('fecha_generado', ''))[:16].replace('T', ' '),
                'tipo': _tipo_label(r.get('tipo_generacion')),
                'generado_por': empleados_map.get(str(r.get('generado_por')), '—') if r.get('generado_por') else 'Sistema',
                'ordenes_count': snap_prod.get('ordenes_count', 0),
                'yield_pct': snap_prod.get('yield_pct', 0),
                'bajo_minimo': snap_inv.get('bajo_minimo', 0),
            })

        page = Paginator(rows, PAGE_SIZE_REPORTES).get_page(request.GET.get('page', 1))

        ctx = _base_ctx_from_alertas(self.role, alertas_bd)
        ctx.update({
            'backend_url': BACKEND_URL,
            'reportes_mensuales_page': page,
            'anio_actual': date.today().year,
            'mes_actual': date.today().month,
            'meses': MESES,
            'breadcrumbs': [
                {'label': 'Dashboard', 'url': self.dashboard_url},
                {'label': 'Reportes', 'url': ''},
                {'label': 'Mensual', 'url': ''},
            ],
        })
        return render(request, self.template_name, ctx)

    def post(self, request):
        anio = int(request.POST.get('anio') or date.today().year)
        mes = int(request.POST.get('mes') or date.today().month)
        existentes = _get('/v1/list/reportes_mensuales/', [])
        if any(r.get('anio') == anio and r.get('mes') == mes for r in existentes):
            messages.error(request, f'Ya existe el reporte de {MESES.get(mes, mes)} {anio}.')
        else:
            ok, resp = _post('/v1/create/reporte_mensual/', {
                'anio': anio, 'mes': mes,
                'tipo_generacion': 'manual', 'generado_por': request.session.get('user_id'),
            })
            if ok:
                messages.success(request, f'Reporte de {MESES.get(mes, mes)} {anio} generado.')
            else:
                messages.error(request, f'Error: {resp}')
        return redirect(self.redirect_url_name)


class AdminReportesMensualesView(BaseReportesMensualesView):
    role = 'Administrador'
    template_name = 'admin/reportes_mensual.html'
    dashboard_url = '/admin-dash/'
    redirect_url_name = 'admin_reportes_mensual'


class SupervisorReportesMensualesView(BaseReportesMensualesView):
    role = 'Supervisor'
    template_name = 'supervisor/reportes_mensual.html'
    dashboard_url = '/supervisor/'
    redirect_url_name = 'supervisor_reportes_mensual'
