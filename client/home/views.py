import requests
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

BACKEND_URL = 'http://localhost:8001/api'


# ── Helpers HTTP ─────────────────────────────────────────────────────────────

def _get(endpoint, default=None):
    try:
        r = requests.get(f'{BACKEND_URL}{endpoint}', timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default if default is not None else []


def _post(endpoint, data):
    try:
        r = requests.post(f'{BACKEND_URL}{endpoint}', json=data, timeout=5)
        r.raise_for_status()
        return True, r.json()
    except requests.HTTPError as e:
        try:
            return False, str(e.response.json())
        except Exception:
            return False, str(e)
    except Exception as e:
        return False, str(e)


def _patch(endpoint, data):
    try:
        r = requests.patch(f'{BACKEND_URL}{endpoint}', json=data, timeout=5)
        r.raise_for_status()
        return True, r.json()
    except Exception as e:
        return False, str(e)


# ── Objeto falso para templates que esperan atributos de modelo ──────────────

class _FakeObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __str__(self):
        return str(getattr(self, 'nombre', getattr(self, 'descripcion', '')))


# ── Contexto base ─────────────────────────────────────────────────────────────

def _base_ctx(role='Administrador'):
    alertas = _get('/v1/list/alertas/', [])
    unread  = sum(1 for a in alertas if str(a.get('estadoAlerta', '')).lower() == 'activo')
    return {
        'user_role':            role,
        'unread_count':         unread,
        'recent_notifications': [
            {
                'titulo': a.get('descripcion', ''),
                'tipo':   'alerta',
                'leida':  str(a.get('estadoAlerta', '')).lower() != 'activo',
            }
            for a in alertas[:5]
        ],
        'breadcrumbs': [],
    }


# ── Semáforo KPI reutilizable ─────────────────────────────────────────────────

def _semaforo_color(valor, kpi_dict, unidad='%'):
    val_str = f'{valor:.1f}' if isinstance(valor, float) else str(valor)
    if not kpi_dict:
        return {'bg': '#E9ECEF', 'color': '#495057', 'valor': val_str, 'unidad': unidad}
    if valor >= kpi_dict.get('umbralVerde', 0):
        bg, color = '#D4EDDA', '#155724'
    elif valor >= kpi_dict.get('umbralAmarillo', 0):
        bg, color = '#FFF3CD', '#856404'
    else:
        bg, color = '#F8D7DA', '#721C24'
    return {'bg': bg, 'color': color, 'valor': val_str, 'unidad': unidad}


def _build_semaforo(kpi_list):
    kpi_map = {k.get('nombre', '').lower(): k for k in kpi_list}
    ky = kpi_map.get('yield')
    kt = kpi_map.get('throughput')
    ko = kpi_map.get('oee')
    return [
        {'nombre': 'Yield',
         'celdas': [_semaforo_color(94.2, ky), _semaforo_color(91.5, ky),
                    _semaforo_color(88.3, ky), _semaforo_color(91.3, ky)]},
        {'nombre': 'Throughput',
         'celdas': [_semaforo_color(210, kt, ''), _semaforo_color(185, kt, ''),
                    _semaforo_color(95,  kt, ''), _semaforo_color(163, kt, '')]},
        {'nombre': 'OEE',
         'celdas': [_semaforo_color(88.1, ko), _semaforo_color(82.4, ko),
                    _semaforo_color(71.2, ko), _semaforo_color(80.6, ko)]},
    ]


# ════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════

def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user:
            login(request, user)
            empleados = _get('/v1/list/empleados/', [])
            rol = 'administrador'
            for e in empleados:
                if e.get('username') == user.username:
                    rol = (e.get('rol') or '').lower()
                    break
            if 'supervisor' in rol:
                return redirect('supervisor_dashboard')
            return redirect('admin_dashboard')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'base/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
