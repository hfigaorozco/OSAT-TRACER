from django.contrib import admin
from . import models

# Register your models here.
@admin.register(models.Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = [
        'codigo',
        'descripcion'
    ]
    

@admin.register(models.Estado_Empleado)
class EstadoEmpleadoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo',
        'descripcion'
    ]


@admin.register(models.Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = [
        'numero',
        'nombre',
        'primerApell',
        'seguApell',
        'rfc',
        'email',
        'username',
    ]

    def email(self, obj):
        return obj.usuario.email

    def username(self, obj):
        return obj.usuario.username