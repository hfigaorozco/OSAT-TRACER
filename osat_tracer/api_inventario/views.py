from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from . import models, serializers

# Create your views here.

### CRUD PIEZA SERVICES

## Create Pieza
class CreatePiezaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreatePiezaSerializer


## List Pieza
class ListPiezaAPIView(APIView):
    
    def get(self, request):
        piezas = models.Pieza.objects.all()
        data = serializers.ListPiezaSerializer(piezas, many=True).data
        return Response(data)


## Detail Pieza
class DetailPiezaAPIView(APIView):
    
    def get(self, request, pk):
        pieza = models.Pieza.objects.get(pk=pk)
        data = serializers.DetailPiezaSerializer(pieza, many=False).data
        return Response(data)
    
    
## Update Pieza
class UpdatePiezaAPIView(generics.UpdateAPIView):
    queryset = models.Pieza.objects.all()
    serializer_class = serializers.UpdatePiezaSerializer
    lookup_field = 'pk'  