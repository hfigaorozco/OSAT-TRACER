from datetime import date
from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.views import View
from home.views import _base_ctx, _get, _get_many, _post, _patch, _FakeObj

PAGE_SIZE_MAQUINARIA = 10


def _parse_fecha(valor):
    try:
        return date.fromisoformat(str(valor)[:10])
    except (TypeError, ValueError):
        return None


class AdminMaquinaria(View):
    template_name = 'admin/maquinaria.html'

    def get(self, request):
        maquinas_bd, tipos_maquina_bd, estados_maquina_bd, lineas_bd, empleados_bd, alertas_bd = _get_many(
            '/v1/list/maquinaria/',
            '/v1/list/tipo_maquinaria/',
            '/v1/list/estado_maquinaria/',
            '/v1/list/Linea/',
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

        tipos_map = {str(t.get('codigo', '')): t for t in tipos_maquina_bd}
        estados_map = {str(e.get('codigo', '')): e for e in estados_maquina_bd}
        lineas_map = {str(l.get('codigo', '')): l for l in lineas_bd}
        empleados_map = {str(e.get('numero', '')): e for e in empleados_bd}

        maquinas = []
        for m in maquinas_bd:
            tipo_pk = str(m.get('tipoMaquina', '')) if m.get('tipoMaquina') else ''
            estado_pk = str(m.get('estado', '')) if m.get('estado') else ''
            linea_pk = str(m.get('linea', '')) if m.get('linea') else ''
            empleado_pk = str(m.get('empleado', '')) if m.get('empleado') else ''
            emp = empleados_map.get(empleado_pk, {})
            maquinas.append({
                'pk': m.get('numSerie'),
                'nombre': m.get('nombre', ''),
                'tipo_pk': tipo_pk,
                'tipo_nombre': tipos_map.get(tipo_pk, {}).get('descripcion', tipo_pk or '—'),
                'estado_pk': estado_pk,
                'estado_nombre': estados_map.get(estado_pk, {}).get('descripcion', estado_pk or '—'),
                'linea_pk': linea_pk,
                'linea_nombre': lineas_map.get(linea_pk, {}).get('nombre') if linea_pk else None,
                'empleado_pk': empleado_pk,
                'empleado_nombre': f"{emp.get('nombre', '')} {emp.get('primerApell', '')}".strip() if emp else None,
                'fecha_reg': _parse_fecha(m.get('fechaReg')),
            })

        tipo_filtro = request.GET.get('tipo', '')
        estado_filtro = request.GET.get('estado', '')
        linea_filtro = request.GET.get('linea', '')

        maquinas_filtradas = maquinas
        if tipo_filtro:
            maquinas_filtradas = [m for m in maquinas_filtradas if m['tipo_pk'] == tipo_filtro]
        if estado_filtro:
            maquinas_filtradas = [m for m in maquinas_filtradas if m['estado_pk'] == estado_filtro]
        if linea_filtro:
            maquinas_filtradas = [m for m in maquinas_filtradas if m['linea_pk'] == linea_filtro]

        maquinas_page = Paginator(maquinas_filtradas, PAGE_SIZE_MAQUINARIA).get_page(request.GET.get('page', 1))

        filtros_activos = {}
        if tipo_filtro:
            filtros_activos['tipo'] = tipo_filtro
        if estado_filtro:
            filtros_activos['estado'] = estado_filtro
        if linea_filtro:
            filtros_activos['linea'] = linea_filtro
        maquinaria_extra_params = (urlencode(filtros_activos) + '&') if filtros_activos else ''

        ctx.update({
            'maquinas': maquinas,
            'maquinas_page': maquinas_page,
            'maquinaria_extra_params': maquinaria_extra_params,
            'tipo_filtro': tipo_filtro,
            'estado_filtro': estado_filtro,
            'linea_filtro': linea_filtro,
            'tipos_maquina': [_FakeObj(pk=t.get('codigo'), nombre=t.get('descripcion', ''))
                                for t in tipos_maquina_bd],
            'estados_maquina': [_FakeObj(pk=e.get('codigo'), nombre=e.get('descripcion', ''))
                                for e in estados_maquina_bd],
            'lineas': [_FakeObj(pk=l.get('codigo'), nombre=l.get('nombre', ''))
                                for l in lineas_bd],
            'empleados': [_FakeObj(pk=e.get('numero'), nombre=f"{e.get('nombre', '')} {e.get('primerApell', '')}".strip())
                                for e in empleados_bd],
            'breadcrumbs': [
                {'label': 'Dashboard', 'url': '/admin-dash/'},
                {'label': 'Maquinaria','url': '/admin/maquinaria/'},
            ],
        })
        return render(request, self.template_name, ctx)


class AdminMaquinariaCrear(View):
    def post(self, request):
        ok, resp = _post('/v1/create/maquinaria/', {
            'numSerie': request.POST.get('num_serie', '').strip(),
            'nombre': request.POST.get('nombre', '').strip(),
            'tipoMaquina': request.POST.get('tipo', ''),
            'estado': request.POST.get('estado', ''),
            'empleado': request.POST.get('empleado', ''),
            'linea': request.POST.get('linea', ''),
        })
        if ok:
            messages.success(request, 'Máquina registrada')
        else:
            messages.error(request, f'Error: {resp}')
        return redirect('admin_maquinaria')


class AdminMaquinariaEditar(View):
    def post(self, request, pk):
        ok, resp = _patch(f'/v1/update/maquinaria/{pk}/', {
            'estado': request.POST.get('estado', ''),
            'empleado': request.POST.get('empleado', ''),
            'linea': request.POST.get('linea', ''),
        })
        if ok:
            messages.success(request, 'Máquina actualizada.')
        else:
            messages.error(request, f'Error: {resp}')
        return redirect('admin_maquinaria')