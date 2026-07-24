from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from api_maquinaria import serializers
from api_maquinaria import models

# Create your views here.

## Maquina CRUD
#CREATE
class CreateMaquinaAPIView(generics.CreateAPIView):
    queryset = models.Maquina.objects.all()
    serializer_class = serializers.CreateMaquinaSerializer

#LIST
class ListMaquinaAPIView(generics.ListAPIView):
    queryset = models.Maquina.objects.all()
    serializer_class = serializers.ListMaquinaSerializer

#DETAIL
class DetailMaquinaAPIView(generics.RetrieveAPIView):
    queryset = models.Maquina.objects.all()
    serializer_class = serializers.DetailMaquinaSerializer

#UPDATE
class UpdateMaquinaAPIView(generics.UpdateAPIView):
    queryset = models.Maquina.objects.all()
    serializer_class = serializers.UpdateMaquinaSerializer
    lookup_field = "pk"
    
## Estado_Maquina CRUD
#CREATE
class CreateEstadoMaquinaAPIView(generics.CreateAPIView):
    queryset = models.Estado_Maquina.objects.all()
    serializer_class = serializers.CreateEstadoMaquinaSerializer

#LIST
class ListEstadoMaquinaAPIView(generics.ListAPIView):
    queryset = models.Estado_Maquina.objects.all()
    serializer_class = serializers.ListEstadoMaquinaSerializer

#DETAIL
#UPDATE

## Tipo_Maquina CRUD
#CREATE
class CreateTipoMaquinaAPIView(generics.CreateAPIView):
    queryset = models.Tipo_Maquina.objects.all()
    serializer_class = serializers.CreateTipoMaquinaSerializer

#LIST
class ListTipoMaquinaAPIView(generics.ListAPIView):
    queryset = models.Tipo_Maquina.objects.all()
    serializer_class = serializers.ListTipoMaquinaSerializer

#DETAIL
#UPDATE