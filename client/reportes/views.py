from django.shortcuts import render
from home.views import _base_ctx, _get, _get_many


def _build_reporte_data(ctx_role, dash_url):
    reportes_bd, ordenes_bd, alertas_bd = _get_many(
        '/v1/list/reportes/',
        '/v1/list/Orden/',
        '/v1/list/alertas/',
    )

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

    return {
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
            {'label': 'Dashboard', 'url': dash_url},
            {'label': 'Reportes',  'url': ''},
        ],
    }, alertas_bd


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


def admin_reportes(request):
    reporte_data, alertas_bd = _build_reporte_data('Administrador', '/admin-dash/')
    ctx = _base_ctx_from_alertas('Administrador', alertas_bd)
    ctx.update(reporte_data)
    return render(request, 'admin/reportes.html', ctx)


def supervisor_reportes(request):
    reporte_data, alertas_bd = _build_reporte_data('Supervisor', '/supervisor/')
    ctx = _base_ctx_from_alertas('Supervisor', alertas_bd)
    ctx.update(reporte_data)
    return render(request, 'supervisor/reportes.html', ctx)
