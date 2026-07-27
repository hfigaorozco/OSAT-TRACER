from django.shortcuts import render
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser

from . import models, serializers
from .services import generar_pdf_reporte_inventario, registrar_movimiento_inventario

# Create your views here.

### CRUD PIEZA SERVICES

## Create Pieza
class CreatePiezaAPIView(generics.CreateAPIView):
    serializer_class = serializers.CreatePiezaSerializer
    parser_classes = [MultiPartParser, FormParser]


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


class CreateMovimientoInventarioAPIView(APIView):
    def post(self, request):
        serializer = serializers.CreateMovimientoInventarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            movimiento = registrar_movimiento_inventario(
                pieza=data['pieza'],
                tipo=data['tipo'],
                cantidad=data.get('cantidad', 0),
                cantidad_minima=data.get('cantidad_minima'),
                usuario=data.get('usuario', ''),
                comentario=data.get('comentario', ''),
            )
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response_data = serializers.ListMovimientoInventarioSerializer(movimiento).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class ListMovimientoInventarioAPIView(APIView):
    def get(self, request):
        movimientos = models.MovimientoInventario.objects.select_related('pieza').all()
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        pieza = request.GET.get('pieza')

        if fecha_inicio:
            movimientos = movimientos.filter(fecha__date__gte=fecha_inicio)
        if fecha_fin:
            movimientos = movimientos.filter(fecha__date__lte=fecha_fin)
        if pieza:
            movimientos = movimientos.filter(pieza_id=pieza)

        data = serializers.ListMovimientoInventarioSerializer(movimientos, many=True).data
        return Response(data)
    
class GenerarReporteInventarioView(APIView):
    def get(self, request):
        fecha_inicio = request.GET.get('fecha_inicio') or request.GET.get('desde')
        fecha_fin = request.GET.get('fecha_fin') or request.GET.get('hasta')

        try:
            pdf = generar_pdf_reporte_inventario(fecha_inicio, fecha_fin)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        filename = f"reporte_inventario_{fecha_inicio or 'inicio'}_{fecha_fin or 'actual'}.pdf"
        return FileResponse(
            pdf,
            as_attachment=False,
            filename=filename,
            content_type='application/pdf',
        )
