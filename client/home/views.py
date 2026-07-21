import requests
from requests.adapters import HTTPAdapter
from requests.sessions import Session
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
BACKEND_URL = 'http://localhost:8001/api'


# ── Helpers HTTP ──────────────────────────────────────────────────────────────

# Sesión compartida con keep-alive y connection pooling: reutiliza las
# conexiones TCP en vez de abrir una nueva por request.
_session = Session()
_adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=1,
)
_session.mount('http://', _adapter)
_session.mount('https://', _adapter)


def _get(endpoint, default=None):
    try:
        r = _session.get(f'{BACKEND_URL}{endpoint}', timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default if default is not None else []


def _get_many(*endpoints):
    """
    Lanza todas las llamadas en paralelo — siempre datos frescos, sin cache.
    Devuelve los resultados en el mismo orden que los endpoints recibidos.
    """
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(_get, ep, []) for ep in endpoints]
        return [f.result() for f in futures]


def _post(endpoint, data):
    try:
        r = _session.post(f'{BACKEND_URL}{endpoint}', json=data, timeout=5)
        r.raise_for_status()
        return True, r.json()
    except requests.HTTPError as e:
        try:
            return False, str(e.response.json())
        except Exception:
            return False, str(e)
    except Exception as e:
        return False, str(e)
    
    
def _post_file(endpoint, data, files):
    try:
        r = _session.post(
            f'{BACKEND_URL}{endpoint}',
            data=data,
            files=files,
            timeout=5
        )

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
        r = _session.patch(f'{BACKEND_URL}{endpoint}', json=data, timeout=5)
        r.raise_for_status()
        return True, r.json()
    except Exception as e:
        return False, str(e)


def _delete(endpoint):
    try:
        r = _session.delete(f'{BACKEND_URL}{endpoint}', timeout=5)
        r.raise_for_status()
        return True, None
    except Exception as e:
        return False, str(e)


# ── Objeto falso para templates ───────────────────────────────────────────────

class _FakeObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __str__(self):
        return str(getattr(self, 'nombre', getattr(self, 'descripcion', '')))


# ── Contexto base ─────────────────────────────────────────────────────────────

def _base_ctx(role='Administrador'):
    alertas = _get('/v1/list/alertas/', [])
    unread  = sum(1 for a in alertas
                  if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))
    return {
        'user_role':            role,
        'unread_count':         unread,
        'recent_notifications': [
            {
                'titulo': a.get('descripcion', ''),
                'tipo':   'alerta',
                'leida':  str(a.get('estadoAlerta', '')).lower()
                          not in ('activo', 'sinre'),
            }
            for a in alertas[:5]
        ],
        'breadcrumbs': [],
    }


# ── Semáforo KPI ──────────────────────────────────────────────────────────────

def _semaforo_color(valor, kpi_dict, unidad='%'):
    val_str = f'{valor:.1f}' if isinstance(valor, float) else str(valor)
    if not kpi_dict:
        return {'bg': '#E9ECEF', 'color': '#495057',
                'valor': val_str, 'unidad': unidad}
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        payload = {
            'username': username,
            'password': password
        }
        try:
            response = requests.post('http://127.0.0.1:8001/api/v1/auth/login/web', json=payload, timeout=5)
            print(response.cookies)  # justo después del requests.post

            if response.status_code == 200:
                data = response.json()
                usuarioRol = data['user']['rol'].lower()
                usuarioNombre = data['user']['username'].lower()
                usuarioID = data['user']['id']
                request.session['user_id'] = usuarioID 
                request.session['user_name'] = usuarioNombre 
                request.session['user_rol'] = usuarioRol 
                if 'supervisor' in usuarioRol:
                    response_redirect = redirect('supervisor_dashboard')
                elif 'admin' in usuarioRol:
                    response_redirect = redirect('admin_dashboard')
                
                DJANGO_RESERVED_COOKIES = {'sessionid', 'csrftoken'}

                for cookie_name, cookie_value in response.cookies.items():
                    if cookie_name in DJANGO_RESERVED_COOKIES:
                        continue
                    response_redirect.set_cookie(
                        cookie_name,
                        cookie_value,
                        httponly=True,
                        domain='127.0.0.1'
                    )
                return response_redirect
            elif response.status_code == 401:
                messages.error(request, 'Usuario o contraseña incorrectos.')
            else:
                messages.error(request, 'Error en el servidor. Porfavor contactar al administrador')
        except requests.exceptions.RequestException:
            messages.error(request, 'La conexion al servidor es inestable.')
    return render(request, 'base/login.html')


def logout_view(request):
    response = requests.post("http://127.0.0.1:8001/api/v1/auth/logout/web", cookies= request.COOKIES, timeout=5)
    request.session.flush()
    response_redirect = redirect('login')

    response_redirect.delete_cookie('sesionid', domain='127.0.0.1')

    return response_redirect


def errorview404(request, exception = None):
    return render(request,'base/404page.html', status=404)


def registro_view(request):
    """
    GET  — muestra la landing page con el wizard
    POST — crea el empleado admin y hace login automático
    """
    if request.method == 'POST':
        # Recoger datos del formulario
        empresa_nombre = request.POST.get('empresa_nombre', '').strip()
        empresa_rfc    = request.POST.get('empresa_rfc', '').strip().upper()
        empresa_sector = request.POST.get('empresa_sector', '').strip()

        nombre    = request.POST.get('nombre', '').strip()
        apell1    = request.POST.get('apellido_paterno', '').strip()
        apell2    = request.POST.get('apellido_materno', '').strip()
        username  = request.POST.get('username', '').strip().lower()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')

        # Validaciones básicas del lado servidor
        errores = []
        if not empresa_nombre: errores.append('El nombre de la empresa es obligatorio.')
        if not empresa_rfc or len(empresa_rfc) != 13: errores.append('El RFC debe tener 13 caracteres.')
        if not nombre:   errores.append('El nombre es obligatorio.')
        if not apell1:   errores.append('El apellido paterno es obligatorio.')
        if not username: errores.append('El usuario es obligatorio.')
        if not email:    errores.append('El correo es obligatorio.')
        if not password or len(password) < 8: errores.append('La contraseña debe tener al menos 8 caracteres.')

        if errores:
            return render(request, 'base/registro.html', {
                'errores': errores,
                'post': request.POST,  # para repoblar el form
            })

        # Crear empleado en el backend
        payload = {
            'nombre':      nombre,
            'primerApell': apell1,
            'seguApell':   apell2 if apell2 else '',
            'rfc': request.POST.get('rfc', '').strip().upper(),
            'estado':      'act',
            'rol':         'admin',
            'username':    username,
            'password':    password,
            'email':       email,
        }

        try:
            r = requests.post(
                f'{BACKEND_URL}/v1/create/empleado/',
                json=payload,
                timeout=10
            )
            if r.status_code == 201:
                # Empleado creado — hacer login automático con Django auth
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                    # Guardar datos en sesión igual que login_view normal
                    request.session['user_id']   = user.id
                    request.session['user_name'] = username
                    request.session['user_rol']  = 'administrador'
                    # Guardar también el nombre de empresa en sesión
                    request.session['empresa_nombre'] = empresa_nombre
                    return redirect('admin_dashboard')
                else:
                    # El usuario se creó pero no pudo autenticarse (raro)
                    return render(request, 'base/registro.html', {
                        'errores': ['Cuenta creada pero no se pudo iniciar sesión. Intenta hacer login manualmente.'],
                        'post': request.POST,
                    })
            else:
                # Error del backend
                try:
                    detalle = r.json()
                    # Extraer mensajes de error del DRF
                    msgs = []
                    for campo, errlist in detalle.items():
                        if isinstance(errlist, list):
                            for e in errlist:
                                if 'already exists' in str(e) or 'ya existe' in str(e):
                                    if campo == 'rfc':
                                        msgs.append('El RFC ya está registrado.')
                                    elif 'username' in str(e).lower():
                                        msgs.append('El nombre de usuario ya está en uso. Elige otro.')
                                    else:
                                        msgs.append(f'{campo}: {e}')
                                else:
                                    msgs.append(f'{e}')
                        else:
                            msgs.append(str(errlist))
                    return render(request, 'base/registro.html', {
                        'errores': msgs or ['Error al crear la cuenta. Intenta de nuevo.'],
                        'post': request.POST,
                    })
                except Exception:
                    return render(request, 'base/registro.html', {
                        'errores': [f'Error del servidor ({r.status_code}). Intenta de nuevo.'],
                        'post': request.POST,
                    })
        except requests.exceptions.ConnectionError:
            return render(request, 'base/registro.html', {
                'errores': ['No se pudo conectar al servidor. Verifica que el backend esté corriendo.'],
                'post': request.POST,
            })
        except Exception as e:
            return render(request, 'base/registro.html', {
                'errores': [f'Error inesperado: {str(e)}'],
                'post': request.POST,
            })

    return render(request, 'base/registro.html')
