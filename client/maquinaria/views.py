import re
from datetime import date
from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.views import View
from home.views import _base_ctx, _get, _get_many, _post, _patch, _FakeObj

PAGE_SIZE_MAQUINARIA = 9

_NUM_SERIE_RE = re.compile(r'^[A-Za-z0-9]+$')


def _parse_fecha(valor):
    try:
        return date.fromisoformat(str(valor)[:10])
    except (TypeError, ValueError):
        return None


def _lineas_por_maquina(lineas_map):
    """numSerie -> lista de líneas (dicts {pk, nombre}) a las que pertenece
    la máquina, derivado de a qué Pasos está ligada: MaquinaPaso -> Paso ->
    PasoProceso -> Proceso -> LineaProceso -> Linea. Ya no se elige a mano
    en el form de crear/editar máquina — una máquina puede terminar ligada
    a más de una línea si sus pasos participan en procesos de líneas
    distintas, o a ninguna todavía si no se ha asignado a ningún paso."""
    maquina_paso_bd, pasos_proceso_bd, linea_proceso_bd = _get_many(
        '/v1/list/MaquinaPaso/', '/v1/list/PasoProceso/', '/v1/list/LineaProceso/',
    )
    procesos_por_paso = {}
    for pp in pasos_proceso_bd:
        procesos_por_paso.setdefault(str(pp.get('paso', '')), set()).add(str(pp.get('proceso', '')))
    lineas_por_proceso = {}
    for lp in linea_proceso_bd:
        lineas_por_proceso.setdefault(str(lp.get('proceso', '')), set()).add(str(lp.get('linea', '')))

    resultado = {}
    for mp in maquina_paso_bd:
        num_serie = str(mp.get('maquina', ''))
        procesos = procesos_por_paso.get(str(mp.get('paso', '')), set())
        lineas_pk = set()
        for proc in procesos:
            lineas_pk |= lineas_por_proceso.get(proc, set())
        if not lineas_pk:
            continue
        existentes = {l['pk'] for l in resultado.get(num_serie, [])}
        for pk in lineas_pk:
            if pk in existentes:
                continue
            resultado.setdefault(num_serie, []).append(
                {'pk': pk, 'nombre': lineas_map.get(pk, {}).get('nombre', pk)}
            )
    return resultado


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
        lineas_por_maquina = _lineas_por_maquina(lineas_map)

        maquinas = []
        for m in maquinas_bd:
            tipo_pk = str(m.get('tipoMaquina', '')) if m.get('tipoMaquina') else ''
            estado_pk = str(m.get('estado', '')) if m.get('estado') else ''
            empleado_pk = str(m.get('empleado', '')) if m.get('empleado') else ''
            emp = empleados_map.get(empleado_pk, {})
            lineas_maquina = lineas_por_maquina.get(str(m.get('numSerie', '')), [])
            maquinas.append({
                'pk': m.get('numSerie'),
                'nombre': m.get('nombre', ''),
                'tipo_pk': tipo_pk,
                'tipo_nombre': tipos_map.get(tipo_pk, {}).get('descripcion', tipo_pk or '—'),
                'estado_pk': estado_pk,
                'estado_nombre': estados_map.get(estado_pk, {}).get('descripcion', estado_pk or '—'),
                'lineas_pk': [l['pk'] for l in lineas_maquina],
                'linea_nombre': ', '.join(l['nombre'] for l in lineas_maquina) if lineas_maquina else None,
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
            maquinas_filtradas = [m for m in maquinas_filtradas if linea_filtro in m['lineas_pk']]

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
                                for e in empleados_bd if e.get('rol') == 'Operador'],
            'breadcrumbs': [
                {'label': 'Dashboard', 'url': '/admin-dash/'},
                {'label': 'Maquinaria','url': '/admin/maquinaria/'},
            ],
        })
        return render(request, self.template_name, ctx)


class AdminMaquinariaCrear(View):
    def post(self, request):
        num_serie = request.POST.get('num_serie', '').strip().upper()
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        estado = request.POST.get('estado', '').strip()
        empleado = request.POST.get('empleado', '').strip()

        errores = []
        if not num_serie:
            errores.append('El número de serie es obligatorio.')
        elif len(num_serie) > 5:
            errores.append('El número de serie no puede tener más de 5 caracteres.')
        elif not _NUM_SERIE_RE.match(num_serie):
            errores.append('El número de serie solo puede tener letras y números.')

        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 30:
            errores.append('El nombre no puede tener más de 30 caracteres.')

        if not tipo:
            errores.append('Selecciona el tipo de máquina.')
        if not estado:
            errores.append('Selecciona el estado.')
        if not empleado:
            errores.append('Selecciona el operador asignado.')

        if not errores and num_serie:
            maquinas_bd = _get('/v1/list/maquinaria/', [])
            if any(str(m.get('numSerie', '')).upper() == num_serie for m in maquinas_bd):
                errores.append(f'Ya existe una máquina con el número de serie "{num_serie}".')
            if nombre and any(str(m.get('nombre', '')).strip().lower() == nombre.lower() for m in maquinas_bd):
                errores.append(f'Ya existe una máquina con el nombre "{nombre}".')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_maquinaria')

        ok, resp = _post('/v1/create/maquinaria/', {
            'numSerie': num_serie,
            'nombre': nombre,
            'tipoMaquina': tipo,
            'estado': estado,
            'empleado': empleado,
        })
        if ok:
            messages.success(request, 'Máquina registrada')
        else:
            messages.error(request, f'Error: {resp}')
        return redirect('admin_maquinaria')


class AdminMaquinariaEditar(View):
    def post(self, request, pk):
        estado = request.POST.get('estado', '').strip()
        empleado = request.POST.get('empleado', '').strip()

        errores = []
        if not estado:
            errores.append('Selecciona el estado.')
        if not empleado:
            errores.append('Selecciona el operador asignado.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return redirect('admin_maquinaria')

        ok, resp = _patch(f'/v1/update/maquinaria/{pk}/', {
            'estado': estado,
            'empleado': empleado,
        })
        if ok:
            messages.success(request, 'Máquina actualizada.')
        else:
            messages.error(request, f'Error: {resp}')
        return redirect('admin_maquinaria')


class AdminMaquinariaToggleEstado(View):
    """Activa/desactiva una máquina directamente desde el listado, sin abrir Editar."""
    def post(self, request, pk):
        maquinas = _get('/v1/list/maquinaria/', [])
        maq = next((m for m in maquinas if str(m.get('numSerie')) == str(pk)), None)
        if maq:
            estado_actual = str(maq.get('estado', '')).lower()
            nuevo_estado = 'ina' if estado_actual == 'act' else 'act'
            ok, resp = _patch(f'/v1/update/maquinaria/{pk}/', {'estado': nuevo_estado})
            if ok:
                accion = 'desactivada' if nuevo_estado == 'ina' else 'activada'
                messages.success(request, f'Máquina {accion} correctamente.')
            else:
                messages.error(request, f'Error: {resp}')
        return redirect('admin_maquinaria')