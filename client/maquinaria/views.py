from django.shortcuts import render, redirect
from django.contrib import messages
from home.views import _base_ctx, _get, _get_many, _post, _FakeObj


def admin_maquinaria(request):
    maquinas_bd, tipos_maquina, estados_maquina, lineas_bd, alertas_bd = _get_many(
        '/v1/list/maquinaria/',
        '/v1/list/tipo_maquinaria/',
        '/v1/list/estado_maquinaria/',
        '/v1/list/Linea/',
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

    maquinas = [
        {
            'pk':              m.get('numSerie'),
            'id_maquina':      m.get('numSerie'),
            'tipo':            _FakeObj(nombre=str(m.get('tipoMaquina', '—'))),
            'linea':           _FakeObj(nombre=str(m.get('linea', '—'))),
            'estado':          _FakeObj(nombre=str(m.get('estado', '—'))),
            'operador_actual': _FakeObj(primer_nombre=str(m.get('empleado', '—')),
                                        apellido_paterno=''),
            'created_at':      '—',
        }
        for m in maquinas_bd
    ]
    ctx.update({
        'maquinas':        maquinas,
        'tipos_maquina':   [_FakeObj(pk=t.get('clave'), nombre=t.get('descripcion', ''))
                            for t in tipos_maquina],
        'estados_maquina': [_FakeObj(pk=e.get('clave'), nombre=e.get('descripcion', ''))
                            for e in estados_maquina],
        'lineas':          [_FakeObj(pk=l.get('codigo'), nombre=l.get('nombre', ''))
                            for l in lineas_bd],
        'breadcrumbs': [
            {'label': 'Dashboard',  'url': '/admin-dash/'},
            {'label': 'Maquinaria', 'url': '/admin/maquinaria/'},
        ],
    })
    return render(request, 'admin/maquinaria.html', ctx)


def admin_maquinaria_crear(request):
    if request.method == 'POST':
        ok, resp = _post('/v1/create/maquinaria/', {
            'numSerie':    request.POST.get('num_serie', ''),
            'nombre':      request.POST.get('nombre', ''),
            'tipoMaquina': request.POST.get('tipo', ''),
            'estado':      request.POST.get('estado', ''),
            'empleado':    request.POST.get('empleado', ''),
            'linea':       request.POST.get('linea', ''),
        })
        if ok:
            messages.success(request, 'Máquina registrada.')
        else:
            messages.error(request, f'Error: {resp}')
    return redirect('admin_maquinaria')
