import os
from datetime import datetime

from django.conf import settings

_CSS_PATH = os.path.join(settings.BASE_DIR, 'home', 'static', 'css', 'osat.css')


def static_version(request):
    """Query param de cache-busting para osat.css — sin esto, el navegador
    se queda con la versión vieja del CSS cacheada indefinidamente (pasó
    varias veces en pruebas: los cambios de color/forma de los badges no se
    veían hasta hacer un hard refresh manual). Se lee el mtime del archivo
    en cada request (no una sola vez al arrancar el proceso) porque en
    desarrollo el CSS se edita sin reiniciar el servidor — cachear el valor
    al importar el módulo dejaba el query param pegado al primer arranque
    y el navegador nunca se enteraba de ediciones posteriores."""
    try:
        version = int(os.path.getmtime(_CSS_PATH))
    except OSError:
        version = 0
    return {'css_version': version}


def notificaciones(request):
    """Pone recent_notifications/unread_count disponibles para el topbar en
    TODA página, sin que cada vista tenga que armarlos a mano — antes solo
    un puñado de vistas lo hacían (duplicado con la misma lógica en cada
    una) y el resto simplemente no tenía estas variables, así que la
    campanita se veía vacía aunque sí hubiera alertas reales. Si una vista
    ya pone sus propias 'recent_notifications'/'unread_count' en el
    contexto que le pasa a render(), esas ganan (Django prioriza el
    contexto explícito sobre el de un context processor) — este es solo
    el valor por defecto para las páginas que no lo hacían.

    Usa kpi.views._build_alertas() — la MISMA función que arma la pantalla
    de Alertas — en vez de reconstruir el tipo/color de cada alerta aquí.
    Antes 'tipo' venía hardcodeado a 'alerta' para todas, así que la
    campana siempre mostraba el mismo ícono sin importar si la alerta era
    de stock/producción/KPI, mientras que la pantalla de Alertas sí
    distinguía los 3 tipos con íconos y colores distintos — reusar la
    misma función garantiza que campana y pantalla de Alertas siempre
    coincidan (import diferido para evitar problemas de orden de carga
    entre apps de Django).
    """
    if not request.session.get('user_id'):
        return {}

    from kpi.views import _build_alertas

    rol = str(request.session.get('user_rol', ''))
    role = 'Administrador' if 'admin' in rol else 'Supervisor'
    alertas = _build_alertas(role)

    unread = sum(1 for a in alertas if not a['leida'])
    recientes = sorted(alertas, key=lambda a: a.get('pk') or 0, reverse=True)[:5]

    notificaciones = []
    for a in recientes:
        creada_en = None
        try:
            creada_en = datetime.strptime(a['tiempo'], '%Y-%m-%d %H:%M')
        except (ValueError, KeyError):
            creada_en = None
        notificaciones.append({
            'numero':     a['pk'],
            'titulo':     a['titulo'],
            'tipo':       a['tipo'],
            'color_icon': a['color_icon'],
            'leida':      a['leida'],
            'creada_en':  creada_en,
        })

    return {
        'unread_count': unread,
        'recent_notifications': notificaciones,
    }
