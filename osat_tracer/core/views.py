from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ConfiguracionMovil


class ConfiguracionMovilAPIView(APIView):
    """Configuración de la app móvil, editable desde la web en
    Configuración > Configuración de la app móvil. Independiente del
    horario laboral (HorarioSistema) — modelo, vista y endpoint propios."""

    def get(self, request):
        config = ConfiguracionMovil.obtener()
        return Response({
            'inactividad_minutos': config.inactividad_minutos,
        })
