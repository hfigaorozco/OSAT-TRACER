# client/client/middleware.py
from datetime import time
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

HORA_INICIO = time(7, 0)   # 7:00 am
HORA_FIN = time(17, 0)     # 5:00 pm

class AccesoPorRol:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwds):
        urls_publicas = [
            reverse('login'),
            reverse('registro'),
            reverse('logout'),
            reverse('horario_laboral'),
        ]

        if request.path in urls_publicas:
            return self.get_response(request)

        usuario_id = request.session.get('user_id')
        usuario_rol = request.session.get('user_rol')

        if not usuario_id:
            return redirect('login')

        # Ventana de disponibilidad del sistema 
        hora_actual = timezone.localtime(timezone.now()).time()
        horario = HORA_INICIO <= hora_actual <= HORA_FIN
        
        if not horario and 'administrador' not in usuario_rol:
            return redirect('horario_laboral')

        # Control de acceso por rol (lógica original del Chema) 
        if 'supervisor' in request.path and 'supervisor' not in usuario_rol:
            return redirect('admin_dashboard')

        if 'admin' in request.path and 'administrador' not in usuario_rol:
            return redirect('supervisor_dashboard')

        return self.get_response(request)