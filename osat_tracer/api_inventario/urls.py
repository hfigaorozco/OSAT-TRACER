from django.urls import path
from . import views

urlpatterns = [
    path('v1/list/piezas/', views.ListPiezaAPIView.as_view(), name='list_piezas'),
    path('v1/create/pieza/', views.CreatePiezaAPIView.as_view(), name='create_pieza'),
    path('v1/detail/pieza/<str:pk>/', views.DetailPiezaAPIView.as_view(), name='detail_pieza'),
]