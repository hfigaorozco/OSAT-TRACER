from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('v1/list/empleados/', views.ListEmpleadoAPIView.as_view(), name='list_empleados'),
    path('v1/create/empleado/', views.CreateEmpleadoAPIView.as_view(), name='create_empleado'),
    path('v1/detail/empleado/<int:numero>/', views.DetailEmpleadoAPIView.as_view(), name='detail_empleado'),
    path('v1/update/empleado/<int:numero>/', views.UpdateEmpleadoAPIView.as_view(), name='update_empleado'),
    
    #Auth Movil
    path('v1/auth/login/', obtain_auth_token, name='login'),
    path('v1/auth/logout/', views.LogoutAPIView.as_view(), name='logout'),
    
    #UrlLogin
    path('v1/auth/login/web', views.LoginAPIView.as_view(), name='login_web')
]