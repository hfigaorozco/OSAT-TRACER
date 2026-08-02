from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics

from api_reportes import serializers
from api_reportes import models
from api_inventario.services import computar_snapshot_inventario, dibujar_pdf_inventario
from api_kpi.services import calcular_kpi_por_linea
from .pdf_kpi import dibujar_pdf_reporte_kpi
from .pdf_producto import (
    computar_snapshot_orden_o_lote, dibujar_pdf_reporte_produccion,
    computar_snapshot_produccion_mensual,
)
from .pdf_mensual import dibujar_pdf_reporte_mensual

# Create your views here.

## Reporte (producción) CRUD
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

#PDF — se recalcula desde la orden/lote actual (Reporte no guarda snapshot
# propio, solo los totales; una vez cerrada la orden sus pasos no cambian).
class PdfReporteAPIView(APIView):
    def get(self, request, pk):
        reporte = get_object_or_404(models.Reporte, pk=pk)
        snapshot = computar_snapshot_orden_o_lote(reporte.orden_id, reporte.oblea_id)
        pdf = dibujar_pdf_reporte_produccion(snapshot)
        return FileResponse(pdf, content_type='application/pdf', filename=f'reporte_{reporte.numero}.pdf')


## ReporteInventario CRUD
class CreateReporteInventarioAPIView(generics.CreateAPIView):
    queryset = models.ReporteInventario.objects.all()
    serializer_class = serializers.CreateReporteInventarioSerializer

    def perform_create(self, serializer):
        fecha_inicio = serializer.validated_data.get('fecha_inicio')
        fecha_fin = serializer.validated_data.get('fecha_fin')
        snapshot = computar_snapshot_inventario(
            fecha_inicio.isoformat() if fecha_inicio else None,
            fecha_fin.isoformat() if fecha_fin else None,
        )
        serializer.save(snapshot=snapshot)


class ListReporteInventarioAPIView(generics.ListAPIView):
    queryset = models.ReporteInventario.objects.all().order_by('-fecha_generado')
    serializer_class = serializers.ListReporteInventarioSerializer


class DetailReporteInventarioAPIView(generics.RetrieveAPIView):
    queryset = models.ReporteInventario.objects.all()
    serializer_class = serializers.DetailReporteInventarioSerializer


class PdfReporteInventarioAPIView(APIView):
    def get(self, request, pk):
        reporte = get_object_or_404(models.ReporteInventario, pk=pk)
        pdf = dibujar_pdf_inventario(reporte.snapshot)
        return FileResponse(pdf, content_type='application/pdf', filename=f'reporte_inventario_{reporte.numero}.pdf')


## ReporteKpi CRUD
class CreateReporteKpiAPIView(generics.CreateAPIView):
    queryset = models.ReporteKpi.objects.all()
    serializer_class = serializers.CreateReporteKpiSerializer

    def perform_create(self, serializer):
        fecha_inicio = serializer.validated_data.get('fecha_inicio')
        fecha_fin = serializer.validated_data.get('fecha_fin')
        filas = calcular_kpi_por_linea(
            fecha_inicio.isoformat() if fecha_inicio else None,
            fecha_fin.isoformat() if fecha_fin else None,
        )
        snapshot = {
            'fecha_inicio': fecha_inicio.isoformat() if fecha_inicio else None,
            'fecha_fin': fecha_fin.isoformat() if fecha_fin else None,
            'filas': filas,
        }
        serializer.save(snapshot=snapshot)


class ListReporteKpiAPIView(generics.ListAPIView):
    queryset = models.ReporteKpi.objects.all().order_by('-fecha_generado')
    serializer_class = serializers.ListReporteKpiSerializer


class DetailReporteKpiAPIView(generics.RetrieveAPIView):
    queryset = models.ReporteKpi.objects.all()
    serializer_class = serializers.DetailReporteKpiSerializer


class PdfReporteKpiAPIView(APIView):
    def get(self, request, pk):
        reporte = get_object_or_404(models.ReporteKpi, pk=pk)
        pdf = dibujar_pdf_reporte_kpi(reporte.snapshot)
        return FileResponse(pdf, content_type='application/pdf', filename=f'reporte_kpi_{reporte.numero}.pdf')


## ReporteMensual CRUD
class CreateReporteMensualAPIView(generics.CreateAPIView):
    queryset = models.ReporteMensual.objects.all()
    serializer_class = serializers.CreateReporteMensualSerializer

    def perform_create(self, serializer):
        anio = serializer.validated_data['anio']
        mes = serializer.validated_data['mes']
        primer_dia = f'{anio:04d}-{mes:02d}-01'
        ultimo_dia_num = 31
        if mes == 2:
            ultimo_dia_num = 29 if (anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0)) else 28
        elif mes in (4, 6, 9, 11):
            ultimo_dia_num = 30
        ultimo_dia = f'{anio:04d}-{mes:02d}-{ultimo_dia_num:02d}'

        snapshot_produccion = computar_snapshot_produccion_mensual(anio, mes)
        snapshot_inventario = computar_snapshot_inventario(primer_dia, ultimo_dia)
        snapshot_kpi = {
            'fecha_inicio': primer_dia,
            'fecha_fin': ultimo_dia,
            'filas': calcular_kpi_por_linea(primer_dia, ultimo_dia),
        }
        serializer.save(
            snapshot_produccion=snapshot_produccion,
            snapshot_inventario=snapshot_inventario,
            snapshot_kpi=snapshot_kpi,
        )


class ListReporteMensualAPIView(generics.ListAPIView):
    queryset = models.ReporteMensual.objects.all().order_by('-anio', '-mes')
    serializer_class = serializers.ListReporteMensualSerializer


class DetailReporteMensualAPIView(generics.RetrieveAPIView):
    queryset = models.ReporteMensual.objects.all()
    serializer_class = serializers.DetailReporteMensualSerializer


class PdfReporteMensualAPIView(APIView):
    def get(self, request, pk):
        reporte = get_object_or_404(models.ReporteMensual, pk=pk)
        pdf = dibujar_pdf_reporte_mensual(
            reporte.snapshot_produccion, reporte.snapshot_inventario, reporte.snapshot_kpi
        )
        return FileResponse(pdf, content_type='application/pdf', filename=f'reporte_mensual_{reporte.numero}.pdf')
