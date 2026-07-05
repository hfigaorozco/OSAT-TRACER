from django.shortcuts import render
from home.views import _base_ctx, _get


def _build_reporte_data(ctx_role, dash_url):
    reportes_bd = _get('/v1/list/reportes/', [])
    ordenes_bd  = _get('/v1/list/Orden/', [])

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
    }


def admin_reportes(request):
    ctx = _base_ctx('Administrador')
    ctx.update(_build_reporte_data('Administrador', '/admin-dash/'))
    return render(request, 'admin/reportes.html', ctx)


def supervisor_reportes(request):
    ctx = _base_ctx('Supervisor')
    ctx.update(_build_reporte_data('Supervisor', '/supervisor/'))
    return render(request, 'supervisor/reportes.html', ctx)
