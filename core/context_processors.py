from django.conf import settings


def casa_verde_context(request):
    return {
        'CASA_VERDE': settings.CASA_VERDE,
    }