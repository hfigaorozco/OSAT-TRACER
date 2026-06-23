from django.urls import path
from . import views

urlpatterns = [
<<<<<<< HEAD
    path('v1/list/piezas', views.ListPiezaAPIView.as_view(), name='list_piezas'),
    path('v1/create/pieza', views.CreatePiezaAPIView.as_view(), name='create_pieza'),
    path('v1/detail/pieza/<str:pk>', views.CreatePiezaAPIView.as_view(), name='create_pieza'),
=======
    path('v1/list/piezas/', views.ListPiezaAPIView.as_view(), name='list_piezas'),
    path('v1/create/pieza/', views.CreatePiezaAPIView.as_view(), name='create_pieza'),
    path('v1/detail/pieza/<str:pk>/', views.CreatePiezaAPIView.as_view(), name='detail_pieza'),
>>>>>>> f7ca8c94e196b8c15f7543c16d6d50ab2fab240a
]
