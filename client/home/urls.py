from django.urls import path
from . import views
from django.shortcuts import render
from . import views
def registro_view(request):
    return render(request, 'base/registro.html')
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
]


