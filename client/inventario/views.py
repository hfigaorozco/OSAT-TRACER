from django.shortcuts import render, redirect
from django.contrib import messages
from home.views import _base_ctx, _get, _post, _patch


# ════════════════════════════════════════════════════════════════
# ADMIN — INVENTARIO
# ════════════════════════════════════════════════════════════════

def admin_inventario(request):
    ctx = _base_ctx('Administrador')
    piezas_bd = _get('/v1/list/piezas/', [])
    piezas = [
        {
            'pk':             p.get('codigo', ''),
            'codigo':         p.get('codigo', '—'),
            'nombre':         p.get('nombre', '—'),
            'descripcion':    p.get('descripcion', ''),
            'stock':          p.get('stockActual', 0),
            'stock_minimo':   p.get('stockMinimo', 0),
            'linea':          '—',
            'operador':       '—',
            'fecha_registro': '—',
        }
        for p in piezas_bd
    ]
    ctx.update({
        'piezas':     piezas,
        'categorias': [],
        'breadcrumbs': [
            {'label': 'Dashboard',  'url': '/admin-dash/'},
            {'label': 'Inventario', 'url': '/admin/inventario/'},
        ],
    })
    return render(request, 'admin/inventario.html', ctx)


def admin_inventario_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/pieza/', {
            'codigo':      request.POST.get('codigo', ''),
            'nombre':      request.POST.get('nombre', ''),
            'descripcion': request.POST.get('descripcion', ''),
            'stockActual': int(request.POST.get('stock', 0)),
            'stockMinimo': int(request.POST.get('stock_minimo', 0)),
        })
        if ok:
            messages.success(request, 'Pieza creada correctamente.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_inventario')


def admin_inventario_movimiento(request):
    if request.method == 'POST':
        pieza_id = request.POST.get('pieza_id', '')
        tipo     = request.POST.get('tipo_mov', '')
        cantidad = int(request.POST.get('cantidad', 0))

        pieza        = _get(f'/v1/detail/pieza/{pieza_id}/', {})
        stock_actual = pieza.get('stockActual', 0)

        if tipo == 'entrada':
            nuevo_stock = stock_actual + cantidad
        elif tipo == 'salida':
            nuevo_stock = max(0, stock_actual - cantidad)
        else:
            nuevo_stock = cantidad

        ok, resp = _patch(f'/v1/update/pieza/{pieza_id}/', {'stockActual': nuevo_stock})
        if ok:
            messages.success(request, 'Movimiento registrado.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_inventario')


# ════════════════════════════════════════════════════════════════
# SUPERVISOR — INVENTARIO (solo entradas, sin crear piezas)
# ════════════════════════════════════════════════════════════════

def supervisor_inventario(request):
    ctx = _base_ctx('Supervisor')
    piezas_bd = _get('/v1/list/piezas/', [])
    piezas = [
        {
            'pk':           p.get('codigo', ''),
            'codigo':       p.get('codigo', '—'),
            'nombre':       p.get('nombre', '—'),
            'descripcion':  p.get('descripcion', ''),
            'stock':        p.get('stockActual', 0),
            'stock_minimo': p.get('stockMinimo', 0),
        }
        for p in piezas_bd
    ]
    ctx.update({
        'piezas': piezas,
        'breadcrumbs': [
            {'label': 'Dashboard',  'url': '/supervisor/'},
            {'label': 'Inventario', 'url': '/supervisor/inventario/'},
        ],
    })
    return render(request, 'supervisor/inventario.html', ctx)


def supervisor_inventario_entrada(request):
    if request.method == 'POST':
        pieza_id     = request.POST.get('pieza_id', '')
        cantidad     = int(request.POST.get('cantidad', 0))
        pieza        = _get(f'/v1/detail/pieza/{pieza_id}/', {})
        stock_actual = pieza.get('stockActual', 0)
        nuevo_stock  = stock_actual + cantidad
        ok, resp = _patch(f'/v1/update/pieza/{pieza_id}/', {'stockActual': nuevo_stock})
        if ok:
            messages.success(request, 'Entrada registrada.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('supervisor_inventario')
