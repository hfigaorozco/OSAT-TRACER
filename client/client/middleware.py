from django.shortcuts import redirect
from django.urls import reverse

class AccesoPorRol:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self,request, *args, **kwds):
        urls_publicas=[
            reverse('login')
        ]

        if request.path in urls_publicas:
            return self.get_response(request)
        
        usuario_id = request.session.get('user_id')
        usuario_rol = request.session.get('user_rol')
        
        if not usuario_id :
            return redirect('login')
        
        if 'supervisor' in request.path and 'supervisor' not in usuario_rol:
            return redirect('admin_dashboard')
        
        if 'admin' in request.path and 'administrador' not in usuario_rol:
            return redirect('supervisor_dashboard')
        
        return self.get_response(request)