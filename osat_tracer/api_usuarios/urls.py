from django.urls import path
from . import views

urlpatterns = [
    path('v1/list/empleados/', views.ListEmpleadoAPIView.as_view(), name='list_empleados'),
    path('v1/create/empleado/', views.CreateEmpleadoAPIView.as_view(), name='create_empleado'),
    path('v1/detail/empleado/<int:numero>/', views.DetailEmpleadoAPIView.as_view(), name='detail_empleado'),
    path('v1/update/empleado/<int:numero>/', views.UpdateEmpleadoAPIView.as_view(), name='update_empleado'),
]