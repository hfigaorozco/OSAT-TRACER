from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from api_reportes import serializers
from api_reportes import models
# Create your views here.

## Maquina CRUD
#CREATE
class CreateReporteAPIView(generics.CreateAPIView):
    queryset = models.Reporte.objects.all()
    serializer_class = serializers.CreateReporteSerializer
#LIST
class ListReportesAPIView(generics.ListAPIView):
    queryset = models.Reporte.objects.all()
    serializer_class = serializers.ListReporteSerializer
#DETAIL
class DetailReporteAPIView(generics.RetrieveAPIView):
    queryset = models.Reporte.objects.all()
    serializer_class = serializers.DetailReporteSerializer
#UPDATE
class UpdateReporteAPIView(generics.UpdateAPIView):
    queryset = models.Reporte.objects.all()
    serializer_class = serializers.UpdateReporteSerializer
    lookup_field = "pk"