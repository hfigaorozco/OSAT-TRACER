from api_produccion.models import Oblea
from api_produccion.services import generarQR

for oblea in Oblea.objects.all():
    generarQR(oblea)
