from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from . import models


class EmpleadoCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)

    # seguApell es opcional, puede venir vacío o nulo
    seguApell = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )

    class Meta:
        model = models.Empleado
        fields = [
            'nombre',
            'primerApell',
            'seguApell',
            'rfc',
            'estado',
            'rol',
            'username',
            'password',
            'email',
        ]

    def validate_username(self, value):
        from django.contrib.auth.models import User
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este nombre de usuario ya está en uso.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        email    = validated_data.pop('email')
        # seguApell puede venir vacío
        validated_data.setdefault('seguApell', '')
        user     = User.objects.create_user(username=username, email=email, password=password)
        empleado = models.Empleado.objects.create(usuario=user, **validated_data)
        return empleado


class EmpleadoListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)
    last_login = serializers.DateTimeField(source='usuario.last_login', read_only=True)
    date_joined = serializers.DateTimeField(source='usuario.date_joined', read_only=True)
    estado = serializers.StringRelatedField()
    rol = serializers.StringRelatedField()

    class Meta:
        model = models.Empleado
        fields = [
            'numero',
            'nombre',
            'primerApell',
            'seguApell',
            'rfc',
            'username',
            'email',
            'last_login',
            'date_joined',
            'estado',
            'rol'
        ]


class EmpleadoUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', required=False)
    email = serializers.EmailField(source='usuario.email', required=False)
    password = serializers.CharField(write_only=True, required=False)
    seguApell = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = models.Empleado
        fields = [
            'nombre',
            'primerApell',
            'seguApell',
            'estado',
            'rol',
            'username',
            'email',
            'password'
        ]

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', {})
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        user = instance.usuario

        if 'username' in usuario_data:
            user.username = usuario_data['username']
            
        if 'email' in usuario_data:
            user.email = usuario_data['email']
            
        if password:
            user.set_password(password)

        user.save()

        return instance