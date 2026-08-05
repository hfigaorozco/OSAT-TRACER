from datetime import datetime

from .views import _get


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
    """
    if not request.session.get('user_id'):
        return {}

    alertas = _get('/v1/list/alertas/', [])
    unread = sum(1 for a in alertas if str(a.get('estadoAlerta', '')).lower() in ('activo', 'sinre'))

    recientes = sorted(alertas, key=lambda a: a.get('numero') or 0, reverse=True)[:5]
    notificaciones = []
    for a in recientes:
        creada_en = None
        if a.get('fecha') and a.get('hora'):
            try:
                creada_en = datetime.strptime(f"{a['fecha']} {a['hora']}", '%Y-%m-%d %H:%M:%S')
            except ValueError:
                creada_en = None
        notificaciones.append({
            'numero':     a.get('numero'),
            'titulo':     a.get('descripcion', ''),
            'tipo':       'alerta',
            'leida':      str(a.get('estadoAlerta', '')).lower() not in ('activo', 'sinre'),
            'creada_en':  creada_en,
        })

    return {
        'unread_count': unread,
        'recent_notifications': notificaciones,
    }
