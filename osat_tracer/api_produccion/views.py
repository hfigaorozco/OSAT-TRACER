from django.shortcuts import render
from . import serializers, models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

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
#UPDATE

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


#LIST
class ListPasoAPIView(APIView):
    
    def get(self, request):
        Pasos = models.Paso.objects.all()
        data = serializers.ListProcesoSerializer(Pasos, many=True).data
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