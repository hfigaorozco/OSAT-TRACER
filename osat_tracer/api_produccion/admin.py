from django.contrib import admin
from api_produccion import models
@admin.register(models.Estado_Orden)
# Register your models here.
class BankAdmin(admin.ModelAdmin):
    list_display= [
        "codigo",
        "descripcion",
    ]