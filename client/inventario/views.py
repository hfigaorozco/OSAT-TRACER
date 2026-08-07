import re
from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import generic
from django.http import JsonResponse
from django.core.paginator import Paginator

from home.views import _base_ctx, _get, _get_many, _post, _patch, _post_file
import requests

_CODIGO_RE = re.compile(r'^[a-z0-9-]+$')
PAGE_SIZE_INVENTARIO = 10


# ADMIN — INVENTARIO

class AdminInventario(generic.View):
    template_name = 'admin/inventario.html'
    url_base = 'http://localhost:8001/api/v1/list/piezas/'
    context = {}
    response = None

    def get(self, request):
        self.request = requests.get(url=self.url_base).json()
        procesos_bd, tipos_oblea_bd = _get_many('/v1/list/Proceso/', '/v1/list/TipoOblea/')
        self.context = {
            "piezas": self.request,
            "procesos": procesos_bd,
            "tipos_oblea": tipos_oblea_bd,
        }

        return render(request, self.template_name, self.context)
    

class AdminInventarioDetail(generic.View):

    url_base = "http://localhost:8001/api/v1/detail/pieza/"

    def get(self, request, codigo):

        response = requests.get(f"{self.url_base}{codigo}/")

        return JsonResponse(response.json())
    

def admin_inventario_crear(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().lower()
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        stock_raw = request.POST.get('stock', '').strip()
        stock_min_raw = request.POST.get('stock_minimo', '').strip()

        errores = []
        if not codigo:
            errores.append('El código es obligatorio.')
        elif len(codigo) > 5:
            errores.append('El código no puede tener más de 5 caracteres.')
        elif not _CODIGO_RE.match(codigo):
            errores.append('El código solo puede tener letras minúsculas, números y guiones.')

        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 20:
            errores.append('El nombre no puede tener más de 20 caracteres.')

        if len(descripcion) > 80:
            errores.append('La descripción no puede tener más de 80 caracteres.')

        if not stock_raw.isdigit():
            errores.append('El stock inicial debe ser un número mayor o igual a 0.')
        if not stock_min_raw.isdigit():
            errores.append('El stock mínimo debe ser un número mayor o igual a 0.')

        if not errores:
            piezas_bd = _get('/v1/list/piezas/', [])
            if any(str(p.get('codigo', '')).lower() == codigo for p in piezas_bd):
                errores.append(f'Ya existe una pieza con el código "{codigo}".')
            if nombre and any(str(p.get('nombre', '')).strip().lower() == nombre.lower() for p in piezas_bd):
                errores.append(f'Ya existe una pieza con el nombre "{nombre}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_inventario')

        data = {
            'codigo': codigo,
            'nombre': nombre,
            'descripcion': descripcion,
            'stockActual': stock_raw,
            'stockMinimo': stock_min_raw,
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
        pieza_id = request.POST.get('pieza_id', '').strip()
        tipo = request.POST.get('tipo_mov', '').strip()
        cantidad_raw = request.POST.get('cantidad', '').strip()
        cantidad_minima_raw = request.POST.get('cantidad_minima', '').strip()

        errores = []
        if not pieza_id:
            errores.append('Selecciona una pieza.')
        if tipo not in ('entrada', 'salida', 'ajuste'):
            errores.append('Tipo de movimiento no válido.')

        if tipo in ('entrada', 'salida'):
            if not cantidad_raw.isdigit() or int(cantidad_raw) < 1:
                errores.append('La cantidad debe ser un número mayor a 0.')
        elif tipo == 'ajuste':
            if not cantidad_minima_raw.isdigit():
                errores.append('El nuevo stock mínimo debe ser un número mayor o igual a 0.')

        pieza = None
        if tipo == 'salida' and not errores:
            piezas_bd = _get('/v1/list/piezas/', [])
            pieza = next((p for p in piezas_bd if str(p.get('codigo')) == pieza_id), None)
            if pieza and int(cantidad_raw) > int(pieza.get('stockActual', 0)):
                errores.append(f'No hay suficiente stock: disponible {pieza.get("stockActual", 0)}.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_inventario')

        payload = {
            'pieza': pieza_id,
            'tipo': tipo,
            'cantidad': int(cantidad_raw or 0),
            'usuario': request.session.get('user_name', ''),
        }
        if tipo == 'ajuste':
            payload['cantidad_minima'] = int(cantidad_minima_raw)

        ok, resp = _post('/v1/create/movimiento_inventario/', payload)

        if ok:
            messages.success(request, 'Movimiento registrado')
            if tipo == 'salida' and pieza:
                restante = int(pieza.get('stockActual', 0)) - int(cantidad_raw)
                minimo = int(pieza.get('stockMinimo', 0))
                if restante < minimo:
                    messages.warning(request,
                        f'"{pieza.get("nombre", pieza_id)}" quedará con {restante} unidades — '
                        f'por debajo del mínimo ({minimo}), queda en estado crítico.')
        else:
            messages.error(request, f'Error: {resp}')

    return redirect('admin_inventario')


# SUPERVISOR — INVENTARIO (solo entradas, sin crear piezas)

def supervisor_inventario(request):
    piezas_bd = _get('/v1/list/piezas/', [])
    procesos_bd, tipos_oblea_bd = _get_many('/v1/list/Proceso/', '/v1/list/TipoOblea/')
    # unread_count/recent_notifications los pone home.context_processors.
    # notificaciones() para toda la app — no armarlos aquí a mano, porque
    # el contexto explícito de esta vista gana sobre el del context
    # processor y tapaba el valor correcto (icono/color/tipo reales) con
    # una forma vieja que dejaba la campana rota en esta página.
    ctx = {
        'user_role': 'Supervisor',
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

    piezas_page = Paginator(piezas, PAGE_SIZE_INVENTARIO).get_page(request.GET.get('page', 1))
    inventario_extra_params = (urlencode({'q': q}) + '&') if q else ''

    ctx.update({
        'piezas_page': piezas_page,
        'inventario_extra_params': inventario_extra_params,
        'procesos': procesos_bd,
        'tipos_oblea': tipos_oblea_bd,
        'breadcrumbs': [
            {'label': 'Dashboard', 'url': '/supervisor/'},
            {'label': 'Inventario', 'url': '/supervisor/inventario/'},
        ],
    })
    return render(request, 'supervisor/inventario.html', ctx)


def supervisor_inventario_entrada(request):
    if request.method == 'POST':
        pieza_id = request.POST.get('pieza_id', '').strip()
        cantidad_raw = request.POST.get('cantidad', '').strip()

        errores = []
        if not pieza_id:
            errores.append('Selecciona una pieza.')
        if not cantidad_raw.isdigit() or int(cantidad_raw) < 1:
            errores.append('La cantidad debe ser un número mayor a 0.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('supervisor_inventario')

        ok, resp = _post('/v1/create/movimiento_inventario/', {
            'pieza': pieza_id,
            'tipo': 'entrada',
            'cantidad': int(cantidad_raw),
            'usuario': request.session.get('user_name', ''),
        })
        if ok:
            messages.success(request, 'Entrada registrada')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('supervisor_inventario')


def supervisor_inventario_salida(request):
    if request.method == 'POST':
        pieza_id = request.POST.get('pieza_id', '').strip()
        cantidad_raw = request.POST.get('cantidad', '').strip()

        errores = []
        if not pieza_id:
            errores.append('Selecciona una pieza.')
        if not cantidad_raw.isdigit() or int(cantidad_raw) < 1:
            errores.append('La cantidad debe ser un número mayor a 0.')

        pieza = None
        if not errores:
            piezas_bd = _get('/v1/list/piezas/', [])
            pieza = next((p for p in piezas_bd if str(p.get('codigo')) == pieza_id), None)
            if pieza and int(cantidad_raw) > int(pieza.get('stockActual', 0)):
                errores.append(f'No hay suficiente stock: disponible {pieza.get("stockActual", 0)}.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('supervisor_inventario')

        ok, resp = _post('/v1/create/movimiento_inventario/', {
            'pieza': pieza_id,
            'tipo': 'salida',
            'cantidad': int(cantidad_raw),
            'usuario': request.session.get('user_name', ''),
        })
        if ok:
            messages.success(request, 'Salida registrada')
            if pieza:
                restante = int(pieza.get('stockActual', 0)) - int(cantidad_raw)
                minimo = int(pieza.get('stockMinimo', 0))
                if restante < minimo:
                    messages.warning(request,
                        f'"{pieza.get("nombre", pieza_id)}" quedará con {restante} unidades — '
                        f'por debajo del mínimo ({minimo}), queda en estado crítico.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('supervisor_inventario')


class SupervisorInventarioDetail(generic.View):
    url_base = "http://localhost:8001/api/v1/detail/pieza/"

    def get(self, request, codigo):
        response = requests.get(f"{self.url_base}{codigo}/")
        return JsonResponse(response.json())
