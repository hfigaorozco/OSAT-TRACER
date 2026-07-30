from django.urls import path
from . import views

urlpatterns = [
    #Defecto
    path('v1/list/Defecto/', views.ListDefectoAPIView.as_view(), name='list_Defectos'),
    path('v1/create/Defecto/', views.CreateDefectoAPIView.as_view(), name='create_Defecto'),
    path('v1/update/Defecto/<str:codigo>/', views.UpdateDefectoAPIView.as_view(), name='update_Defecto'),
    #PasoDefecto
    path('v1/list/PasoDefecto/', views.ListPasoDefectoAPIView.as_view(), name='list_PasoDefectos'),
    path('v1/create/PasoDefecto/', views.CreatePasoDefectoAPIView.as_view(), name='create_PasoDefecto'),
    path('v1/delete/PasoDefecto/<int:pk>/', views.DeletePasoDefectoAPIView.as_view(), name='delete_PasoDefecto'),
    #TipoOblea
    path('v1/list/TipoOblea/', views.ListTipoObleaAPIView.as_view(), name='list_TipoObleas'),
    path('v1/create/TipoOblea/', views.CreateTipoObleaAPIView.as_view(), name='create_TipoOblea'),
    path('v1/detail/TipoOblea/<str:pk>/', views.DetailTipoObleaAPIView.as_view(), name='detail_TipoOblea'),
    path('v1/update/TipoOblea/<str:pk>/', views.UpdateTipoObleaAPIView.as_view(), name='update_TipoOblea'),
    #EstadoPaso
    path('v1/list/EstadoPaso/', views.ListEstadoPasoAPIView.as_view(), name='list_EstadoPasos'),
    path('v1/create/EstadoPaso/', views.CreateEstadoPasoAPIView.as_view(), name='create_EstadoPaso'),
    #EstadoOrden
    path('v1/list/EstadoOrden/', views.ListEstadoOrdenAPIView.as_view(), name='list_EstadoOrdens'),
    path('v1/create/EstadoOrden/', views.CreateEstadoOrdenAPIView.as_view(), name='create_EstadoOrden'),
    #EstadoOblea
    path('v1/list/EstadoOblea/', views.ListEstadoObleaAPIView.as_view(), name='list_EstadoObleas'),
    path('v1/create/EstadoOblea/', views.CreateEstadoObleaAPIView.as_view(), name='create_EstadoOblea'),
    #Linea
    path('v1/list/Linea/', views.ListLineaAPIView.as_view(), name='list_Lineas'),
    path('v1/create/Linea/', views.CreateLineaAPIView.as_view(), name='create_Linea'),
    path('v1/detail/Linea/<str:pk>/', views.DetailLineaAPIView.as_view(), name='detail_Linea'),
    path('v1/update/Linea/<str:pk>/', views.UpdateLineaAPIView.as_view(), name='update_Linea'),
    #Proceso
    path('v1/list/Proceso/', views.ListProcesoAPIView.as_view(), name='list_Procesos'),
    path('v1/create/Proceso/', views.CreateProcesoAPIView.as_view(), name='create_Proceso'),
    path('v1/detail/Proceso/<str:pk>/', views.DetailProcesoAPIView.as_view(), name='detail_Proceso'),
    path('v1/update/Proceso/<str:pk>/', views.UpdateProcesoAPIView.as_view(), name='update_Proceso'),
    #Paso
    path('v1/list/Paso/', views.ListPasoAPIView.as_view(), name='list_Pasos'),
    path('v1/create/Paso/', views.CreatePasoAPIView.as_view(), name='create_Paso'),
    path('v1/detail/Paso/<str:pk>/', views.DetailPasoAPIView.as_view(), name='detail_Paso'),
    path('v1/update/Paso/<str:pk>/', views.UpdatePasoAPIView.as_view(), name='update_Paso'),
    path('v1/list/pasos/', views.ListPasoAPIView.as_view(), name='list_pasos'),
    #Orden
    path('v1/list/Orden/', views.ListOrdenAPIView.as_view(), name='list_Ordens'),
    path('v1/create/Orden/', views.CreateOrdenAPIView.as_view(), name='create_Orden'),
    path('v1/detail/Orden/<int:pk>/', views.DetailOrdenAPIView.as_view(), name='detail_Orden'),
    path('v1/update/Orden/<int:pk>/', views.UpdateOrdenAPIView.as_view(), name='update_Orden'),
    #Oblea
    path('v1/list/Oblea/', views.ListObleaAPIView.as_view(), name='list_Obleas'),
    path('v1/create/Oblea/', views.CreateObleaAPIView.as_view(), name='create_Oblea'),
    path('v1/detail/Oblea/<int:pk>/', views.DetailObleaConEtapasAPIView.as_view(), name='detail_Oblea'),
    path('v1/update/Oblea/<int:pk>/', views.UpdateObleaAPIView.as_view(), name='update_Oblea'),
    # ----- TABLAS CON PK COMPUESTAS -----#
    #Las marco porque tengo duda de como llamarlas desde el endpoint
    #LineaProceso
    path('v1/list/LineaProceso/', views.ListLineaProcesoAPIView.as_view(), name='list_LineaProcesos'),
    path('v1/create/LineaProceso/', views.CreateLineaProcesoAPIView.as_view(), name='create_LineaProceso'),
    path('v1/detail/LineaProceso/<str:pk>/', views.DetailLineaProcesoAPIView.as_view(), name='detail_LineaProceso'),
    #PasoProceso
    path('v1/list/PasoProceso/', views.ListPasoProcesoAPIView.as_view(), name='list_PasoProcesos'),
    path('v1/create/PasoProceso/', views.CreatePasoProcesoAPIView.as_view(), name='create_PasoProceso'),
    path('v1/detail/PasoProceso/<str:pk>/', views.DetailPasoProcesoAPIView.as_view(), name='detail_PasoProceso'),
    path('v1/update/PasoProceso/<str:pk>/', views.UpdatePasoProcesoAPIView.as_view(), name='update_PasoProceso'),
    path('v1/delete/PasoProceso/<int:pk>/', views.DeletePasoProcesoAPIView.as_view(), name='delete_PasoProceso'),
    #ProcesoPieza
    path('v1/list/ProcesoPieza/', views.ListProcesoPiezaAPIView.as_view(), name='list_ProcesoPiezas'),
    path('v1/create/ProcesoPieza/', views.CreateProcesoPiezaAPIView.as_view(), name='create_ProcesoPieza'),
    path('v1/detail/ProcesoPieza/<str:pk>/', views.DetailProcesoPiezaAPIView.as_view(), name='detail_ProcesoPieza'),
    path('v1/update/ProcesoPieza/<str:pk>/', views.UpdateProcesoPiezaAPIView.as_view(), name='update_ProcesoPieza'),
    path('v1/delete/ProcesoPieza/<int:pk>/', views.DeleteProcesoPiezaAPIView.as_view(), name='delete_ProcesoPieza'),
    #MaquinaPaso
    path('v1/list/MaquinaPaso/', views.ListMaquinaPasoAPIView.as_view(), name='list_MaquinaPasos'),
    path('v1/create/MaquinaPaso/', views.CreateMaquinaPasoAPIView.as_view(), name='create_MaquinaPaso'),
    #PasoRealizado
    path('v1/list/PasoRealizado/', views.ListPasoRealizadoAPIView.as_view(), name='list_PasoRealizados'),
    path('v1/create/PasoRealizado/', views.CreatePasoRealizadoAPIView.as_view(), name='create_PasoRealizado'),
    #HistorialDefecto
    path('v1/list/HistorialDefecto/', views.ListHistorialDefectoAPIView.as_view(), name='list_HistorialDefectoss'),
    path('v1/create/HistorialDefecto/', views.CreateHistorialDefectoAPIView.as_view(), name='create_HistorialDefectos'),
    
    #Servicios
    path('v1/orden/<int:id_orden>/etiquetas/QR/', views.GenerarEtiquetasQRView.as_view(), name='generar_etiquetas_qr'),
    path('v1/oblea/<int:pk>/etiqueta/QR/', views.GenerarEtiquetaQRLoteView.as_view(), name='generar_etiqueta_qr_lote'),
    path('v1/oblea/<int:pk>/qr.png/', views.ObleaQRImagenView.as_view(), name='oblea_qr_imagen'),
]
