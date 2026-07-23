from django.shortcuts import render
from . import serializers, models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from django.http import FileResponse

from .services import generar_pdf_etiquetas_QR

# Create your views here.
# Vistas Defecto 

## Create 
class CreateDefectoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateDefectoSerializer


## List 
class ListDefectoAPIView(APIView):
    
    def get(self, request):
        defectos = models.Defecto.objects.all()
        data = serializers.ListDefectoSerializer(defectos, many=True).data
        return Response(data)


#Vistas  Tipo Oblea
#CREATE
class CreateTipoObleaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateTipoObleaSerializer


#LIST
class ListTipoObleaAPIView(APIView):

    def get(self, request):
        TipoObleas = models.Tipo_Oblea.objects.all()
        data = serializers.ListTipoObleaSerializer(TipoObleas, many=True).data
        return Response(data)
#DETAIL
class DetailTipoObleaAPIView(APIView):

    def get(self, request, pk):
        TipoOblea = models.Tipo_Oblea.objects.get(pk=pk)
        data = serializers.DetailTipoObleaSerializer(TipoOblea, many=False).data
        return Response(data)
#UPDATE
class UpdateTipoObleaAPIView(generics.UpdateAPIView):
    queryset = models.Tipo_Oblea.objects.all()
    serializer_class = serializers.UpdateTipoObleaSerializer
    lookup_field = 'pk'

#Vistas  Estado Paso
#CREATE
class CreateEstadoPasoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoPasoSerializer


#LIST
class ListEstadoPasoAPIView(APIView):
    
    def get(self, request):
        EstadoPasos = models.Estado_Paso.objects.all()
        data = serializers.ListEstadoPasoSerializer(EstadoPasos, many=True).data
        return Response(data)
#DETAIL
#UPDATE

#Vistas  EstadoOrden
#CREATE
class CreateEstadoOrdenAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoOrdenSerializer


#LIST
class ListEstadoOrdenAPIView(APIView):
    
    def get(self, request):
        EstadoOrdens = models.Estado_Orden.objects.all()
        data = serializers.ListEstadoOrdenSerializer(EstadoOrdens, many=True).data
        return Response(data)
#DETAIL
#UPDATE

#Vistas  EstadoOblea
#CREATE
class CreateEstadoObleaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateEstadoObleaSerializer


#LIST
class ListEstadoObleaAPIView(APIView):
    
    def get(self, request):
        EstadoObleas = models.Estado_Oblea.objects.all()
        data = serializers.ListEstadoObleaSerializer(EstadoObleas, many=True).data
        return Response(data)
#DETAIL
#UPDATE

#Vistas  Linea
#CREATE
class CreateLineaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateLineaSerializer


#LIST
class ListLineaAPIView(APIView):
    
    def get(self, request):
        Lineas = models.Linea.objects.all()
        data = serializers.ListLineaSerializer(Lineas, many=True).data
        return Response(data)
#DETAIL
class DetailLineaAPIView(APIView):

    def get(self, request, pk):
        Linea = models.Linea.objects.get(pk=pk)
        data = serializers.DetailLineaSerializer(Linea, many=False).data
        return Response(data)


#UPDATE
class UpdateLineaAPIView(generics.UpdateAPIView):
    queryset = models.Linea.objects.all()
    serializer_class = serializers.UpdateLineaSerializer
    lookup_field = 'pk'

#Vistas  Proceso
#CREATE
class CreateProcesoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateProcesoSerializer


#LIST
class ListProcesoAPIView(APIView):
    
    def get(self, request):
        Procesos = models.Proceso.objects.all()
        data = serializers.ListProcesoSerializer(Procesos, many=True).data
        return Response(data)
    
#DETAIL
class DetailProcesoAPIView(APIView):
    
    def get(self, request, pk):
        Proceso = models.Proceso.objects.get(pk=pk)
        data = serializers.DetailProcesoSerializer(Proceso, many=False).data
        return Response(data)


#UPDATE
class UpdateProcesoAPIView(generics.UpdateAPIView):
    queryset = models.Proceso.objects.all()
    serializer_class = serializers.UpdateProcesoSerializer
    lookup_field = 'pk'  
    
    
#Vistas  Paso
#CREATE
class CreatePasoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreatePasoSerializer

#DETAIL
class DetailPasoAPIView(APIView):
    
    def get(self, request, pk):
        Paso = models.Paso.objects.get(pk=pk)
        data = serializers.DetailPasoSerializer(Paso, many=False).data
        return Response(data)

#UPDATE
class UpdatePasoAPIView(generics.UpdateAPIView):
    queryset = models.Paso.objects.all()
    serializer_class = serializers.UpdatePasoSerializer
    lookup_field = 'pk'  
    
    
    
#Vistas  orden
#CREATE
class CreateOrdenAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateOrdenSerializer

#LIST
class ListOrdenAPIView(APIView):
    
    def get(self, request):
        Ordens = models.Orden.objects.all()
        data = serializers.ListOrdenSerializer(Ordens, many=True).data
        return Response(data)
    
#DETAIL
class DetailOrdenAPIView(APIView):
    
    def get(self, request, pk):
        Ordens = models.Orden.objects.get(pk=pk)
        data = serializers.DetailOrdenSerializer(Ordens, many=False).data
        return Response(data)

#UPDATE

#Vistas  Oblea
#CREATE
class CreateObleaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateObleaSerializer

#LIST
class ListObleaAPIView(APIView):
    
    def get(self, request):
        Obleas = models.Oblea.objects.all()
        data = serializers.ListObleaSerializer(Obleas, many=True).data
        return Response(data)
    
#DETAIL
class DetailObleaAPIView(APIView):
    
    def get(self, request, pk):
        Oblea = models.Oblea.objects.get(pk=pk)
        data = serializers.DetailObleaSerializer(Oblea, many=False).data
        return Response(data)

#DETAIL Movil
class DetailObleaConEtapasAPIView(APIView):
    """
    Detalle de oblea para la app móvil — incluye trazabilidad completa.
    Usado por GET /api/v1/detail/Oblea/<pk>/
    """
    def get(self, request, pk):
        try:
            oblea = models.Oblea.objects.select_related(
                'orden', 'orden__proceso', 'estado', 'tipo'
            ).get(pk=pk)
        except models.Oblea.DoesNotExist:
            return Response({'error': 'Lote no encontrado.'}, status=404)

        data = serializers.DetailObleaConEtapasSerializer(oblea, many=False).data
        return Response(data)

#UPDATE Movil
class UpdateObleaAPIView(generics.UpdateAPIView):
    queryset = models.Oblea.objects.all()
    serializer_class = serializers.UpdateObleaSerializer
    lookup_field = 'pk'


#Vistas  LineaProceso
#CREATE
class CreateLineaProcesoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateLineaProcesoSerializer

#LIST
class ListLineaProcesoAPIView(APIView):
    
    def get(self, request):
        LineaProcesos = models.LineaProceso.objects.all()
        data = serializers.ListLineaProcesoSerializer(LineaProcesos, many=True).data
        return Response(data)
    
#DETAIL
class DetailLineaProcesoAPIView(APIView):
    
    def get(self, request, pk):
        LineaProceso = models.LineaProceso.objects.get(pk=pk)
        data = serializers.DetailLineaProcesoSerializer(LineaProceso, many=False).data
        return Response(data)
    
#Vistas  PasoProceso
#CREATE
class CreatePasoProcesoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreatePasoProcesoSerializer

#LIST
class ListPasoProcesoAPIView(APIView):
    
    def get(self, request):
        PasoProcesos = models.PasoProceso.objects.all()
        data = serializers.ListPasoProcesoSerializer(PasoProcesos, many=True).data
        return Response(data)
    
#DETAIL
class DetailPasoProcesoAPIView(APIView):
    
    def get(self, request, pk):
        PasoProceso = models.PasoProceso.objects.get(pk=pk)
        data = serializers.DetailPasoProcesoSerializer(PasoProceso, many=False).data
        return Response(data)
    
#UPDATE
class UpdatePasoProcesoAPIView(generics.UpdateAPIView):
    queryset = models.PasoProceso.objects.all()
    serializer_class = serializers.UpdatePasoProcesoSerializer
    lookup_field = 'pk'

#DELETE (quita solo la relación paso-proceso, no borra el Paso)
class DeletePasoProcesoAPIView(generics.DestroyAPIView):
    queryset = models.PasoProceso.objects.all()
    lookup_field = 'pk'


#View ProcesoPieza
#CREATE
class CreateProcesoPiezaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateProcesoPiezaSerializer

#LIST
class ListProcesoPiezaAPIView(APIView):
    
    def get(self, request):
        ProcesoPiezas = models.ProcesoPieza.objects.all()
        data = serializers.ListProcesoPiezaSerializer(ProcesoPiezas, many=True).data
        return Response(data)
    
#DETAIL
class DetailProcesoPiezaAPIView(APIView):
    
    def get(self, request, pk):
        ProcesoPieza = models.ProcesoPieza.objects.get(pk=pk)
        data = serializers.DetailProcesoPiezaSerializer(ProcesoPieza, many=False).data
        return Response(data)
    
#UPDATE
class UpdateProcesoPiezaAPIView(generics.UpdateAPIView):
    queryset = models.ProcesoPieza.objects.all()
    serializer_class = serializers.UpdateProcesoPiezaSerializer
    lookup_field = 'pk'

#DELETE (quita solo la relación proceso-pieza, no borra la Pieza)
class DeleteProcesoPiezaAPIView(generics.DestroyAPIView):
    queryset = models.ProcesoPieza.objects.all()
    lookup_field = 'pk'


#Vistas  MaquinaPaso
#CREATE
class CreateMaquinaPasoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateMaquinaPasoSerializer

#LIST
class ListMaquinaPasoAPIView(APIView):
    
    def get(self, request):
        MaquinaPasos = models.MaquinaPaso.objects.all()
        data = serializers.ListMaquinaPasoSerializer(MaquinaPasos, many=True).data
        return Response(data)
    
#Vistas  PasoRealizado
#CREATE
class CreatePasoRealizadoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreatePasoRealizadoSerializer

#LIST
class ListPasoRealizadoAPIView(APIView):
    
    def get(self, request):
        PasoRealizados = models.Paso_Realizado.objects.all()
        data = serializers.ListPasoRealizadoSerializer(PasoRealizados, many=True).data
        return Response(data)
    
#Vistas  HistorialDefecto
#CREATE
class CreateHistorialDefectoAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreateHistorialDefectoSerializer

#LIST
class ListHistorialDefectoAPIView(APIView):
    
    def get(self, request):
        HistorialDefectos = models.Historial_Defectos.objects.all()
        data = serializers.ListHistorialDefectoSerializer(HistorialDefectos, many=True).data
        return Response(data)
    
class ListPasoAPIView(generics.ListAPIView):
    queryset = models.Paso.objects.all()
    serializer_class = serializers.PasoSerializer


class GenerarEtiquetasQRView(APIView):
    def get(self, request, id_orden):
        try:
            pdf = generar_pdf_etiquetas_QR(id_orden)
            return FileResponse(
                pdf,
                as_attachment=False,
                filename=f"Orden_{id_orden}.pdf",
                content_type="application/pdf"
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )