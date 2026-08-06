# client/client/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from core.models import HorarioSistema


def obtener_horario():
    horario = cache.get('horario_sistema')
    if horario is None:
        h = HorarioSistema.obtener()
        horario = {'inicio': h.hora_inicio, 'fin': h.hora_fin}
        cache.set('horario_sistema', horario, 300)
    return horario


class AccesoPorRol:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwds):
        urls_publicas = [
            reverse('login'),
            reverse('registro'),
            reverse('logout'),
            reverse('horario_laboral'),
            reverse('verificar_horario'),
        ]

        if request.path in urls_publicas:
            return self.get_response(request)

        usuario_id = request.session.get('user_id')
        usuario_rol = request.session.get('user_rol')

        if not usuario_id:
            return redirect('login')

        horario = obtener_horario()
        hora_actual = timezone.localtime(timezone.now()).time()
        dentro_de_horario = horario['inicio'] <= hora_actual <= horario['fin']

        if not dentro_de_horario and 'administrador' not in usuario_rol:
            return redirect('horario_laboral')

        if 'supervisor' in request.path and 'supervisor' not in usuario_rol:
            return redirect('admin_dashboard')

        if 'admin' in request.path and 'administrador' not in usuario_rol:
            return redirect('supervisor_dashboard')

        return self.get_response(request)