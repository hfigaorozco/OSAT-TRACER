from rest_framework import generics
from . import models, serializers
from api_usuarios.models import Empleado
#Imports Auth Movil
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
import json

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
    
    
## Login api view

class LoginAPIView(APIView):
    permission_classes = [AllowAny] 
    def post(self, request, *args, **kwargs):
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(username = username,  password=password)
            
            if user is not None and user.is_active:
                empleado = Empleado.objects.get(numero = user.id)
                empleado_data = serializers.EmpleadoListSerializer(empleado).data
                rol = empleado_data.get('rol').lower()
                
                return Response({
                'status': 'success',
                'user': {
                    'id' : user.id,
                    'username': user.username,
                    'rol': rol,
                }
            }, status=status.HTTP_200_OK)
                
            return Response({
            'status': 'error',
            'message': 'Credenciales inválidas'
            }, 
            status=status.HTTP_401_UNAUTHORIZED)