from django.urls import path

from api_maquinaria import views

app_name = "api_maquinaria"

urlpatterns = [
    ## Maquinaria
    path('v1/create/maquinaria/', views.CreateMaquinaAPIView.as_view(), name="create_maquinaria"),
    path('v1/list/maquinaria/', views.ListMaquinaAPIView.as_view(), name="list_maquinaria"),
    path('v1/detail/maquinaria/<str:pk>/', views.DetailMaquinaAPIView.as_view(), name="detail_maquinaria"),
    path('v1/update/maquinaria/<str:pk>/', views.UpdateMaquinaAPIView.as_view(), name="update_maquinaria"),
    
    ## Estado_Maquinaria
    path('v1/create/estado_maquinaria/', views.CreateEstadoMaquinaAPIView.as_view(), name="create_estado_maquinaria"),
    path('v1/list/estado_maquinaria/', views.ListEstadoMaquinaAPIView.as_view(), name="list_estado_maquinaria"),

    ## Tipo_Maquinaria
    path('v1/create/tipo_maquinaria/', views.CreateTipoMaquinaAPIView.as_view(), name="create_tipo_maquinaria"),
    path('v1/list/tipo_maquinaria/', views.ListTipoMaquinaAPIView.as_view(), name="list_tipo_maquinaria"),

]