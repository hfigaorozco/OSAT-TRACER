from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import generic
from django.http import JsonResponse

from home.views import _base_ctx, _get, _get_many, _post, _patch, _post_file
import requests


# ADMIN — INVENTARIO

class AdminInventario(generic.View):
    template_name = 'admin/inventario.html'
    url_base = 'http://localhost:8001/api/v1/list/piezas/'
    context = {}
    response = None
    
    def get(self, request):
        self.request = requests.get(url=self.url_base).json()
        self.context = {"piezas": self.request}
        
        return render(request, self.template_name, self.context)
    

class AdminInventarioDetail(generic.View):

    url_base = "http://localhost:8001/api/v1/detail/pieza/"

    def get(self, request, codigo):

        response = requests.get(f"{self.url_base}{codigo}/")

        return JsonResponse(response.json())
    

def admin_inventario_crear(request):
    if request.method == 'POST':
        data = {
            'codigo': request.POST.get('codigo', ''),
            'nombre': request.POST.get('nombre', ''),
            'descripcion': request.POST.get('descripcion', ''),
            'stockActual': request.POST.get('stock', 0),
            'stockMinimo': request.POST.get('stock_minimo', 0),
        }
        files = {}
        
        if request.FILES.get('imagen'):
            files['imagen'] = request.FILES['imagen']
        ok, resp = _post_file(
            '/v1/create/pieza/',
            data,
            files
        )

        if ok:
            messages.success(request, 'Pieza creada correctamente')
        else:
            messages.error(request, f'Error: {resp}')


    return redirect('admin_inventario')


def admin_inventario_movimiento(request):
    if request.method == 'POST':
        pieza_id = request.POST.get('pieza_id', '')
        tipo = request.POST.get('tipo_mov', '')
        cantidad = int(request.POST.get('cantidad', 0))
        cantidad_minima = int(request.POST.get('cantidad_minima', 0))

        payload = {
            'pieza': pieza_id,
            'tipo': tipo,
            'cantidad': cantidad,
            'usuario': request.session.get('user_name', ''),
        }
        if tipo == 'ajuste':
            payload['cantidad_minima'] = cantidad_minima

        ok, resp = _post('/v1/create/movimiento_inventario/', payload)

        if ok:
            messages.success(request, 'Movimiento registrado')
        else:
            messages.error(request, f'Error: {resp}')

    return redirect('admin_inventario')


# SUPERVISOR — INVENTARIO (solo entradas, sin crear piezas)

def supervisor_inventario(request):
    piezas_bd, alertas_bd = _get_many(
        '/v1/list/piezas/',
        '/v1/list/alertas/',
    )
    unread = sum(1 for a in alertas_bd if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    ctx = {
        'user_role': 'Supervisor',
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
    piezas = [
        {
            'pk': p.get('codigo', ''),
            'codigo': p.get('codigo', '—'),
            'nombre': p.get('nombre', '—'),
            'descripcion': p.get('descripcion', ''),
            'stock': p.get('stockActual', 0),
            'stock_minimo': p.get('stockMinimo', 0),
        }
        for p in piezas_bd
    ]

    q = request.GET.get('q', '').strip().lower()
    if q:
        piezas = [p for p in piezas if q in p['nombre'].lower()]

    ctx.update({
        'piezas': piezas,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Inventario', 'url': '/supervisor/inventario/'},
        ],
    })
    return render(request, 'supervisor/inventario.html', ctx)


def supervisor_inventario_entrada(request):
    if request.method == 'POST':
        pieza_id = request.POST.get('pieza_id', '')
        cantidad = int(request.POST.get('cantidad', 0))
        ok, resp = _post('/v1/create/movimiento_inventario/', {
            'pieza': pieza_id,
            'tipo': 'entrada',
            'cantidad': cantidad,
            'usuario': request.session.get('user_name', ''),
        })
        if ok:
            messages.success(request, 'Entrada registrada')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('supervisor_inventario')


class SupervisorInventarioDetail(generic.View):
    url_base = "http://localhost:8001/api/v1/detail/pieza/"

    def get(self, request, codigo):
        response = requests.get(f"{self.url_base}{codigo}/")
        return JsonResponse(response.json())
