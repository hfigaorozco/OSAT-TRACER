from django.urls import path
from . import views

urlpatterns = [
    path('v1/config/movil/', views.ConfiguracionMovilAPIView.as_view(), name='config_movil'),
]
