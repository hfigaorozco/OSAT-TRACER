from rest_framework import generics
from . import models, serializers
#Imports Auth Movil
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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

##Logout Movil
class LogoutAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Sesión cerrada.'}, status=status.HTTP_200_OK)