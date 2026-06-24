from rest_framework import generics
from . import models, serializers

### CRUD EMPLEADOS

## List
class ListEmpleadoAPIView(generics.ListAPIView):
    queryset = models.Empleado.objects.all()
    serializer_class = serializers.EmpleadoListSerializer


## Detail
class DetailEmpleadoAPIView(generics.RetrieveAPIView):
    queryset = models.Empleado.objects.all()
    serializer_class = serializers.EmpleadoListSerializer
    lookup_field = 'numero'


## Create
class CreateEmpleadoAPIView(generics.CreateAPIView):
    serializer_class = serializers.EmpleadoCreateSerializer


## Update
class UpdateEmpleadoAPIView(generics.UpdateAPIView):
    queryset = models.Empleado.objects.all()
    serializer_class = serializers.EmpleadoUpdateSerializer
    lookup_field = 'numero'