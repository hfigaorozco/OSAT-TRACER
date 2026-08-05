from django.urls import path
from . import views
from django.shortcuts import render
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('horario_no_laboral/', views.horario_laboral, name='horario_laboral'),
    path('notificaciones/recientes/', views.api_alertas_recientes, name='api_alertas_recientes'),
]


