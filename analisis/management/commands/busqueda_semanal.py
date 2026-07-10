"""Comando para ejecutar búsqueda semanal — programar con cron o Celery."""
from django.core.management.base import BaseCommand

from analisis.models import ConfiguracionBusqueda
from services.busqueda import BusquedaService


class Command(BaseCommand):
    help = 'Ejecuta búsqueda semanal en todas las configuraciones activas'

    def handle(self, *args, **options):
        total_configs = ConfiguracionBusqueda.objects.filter(activa=True).count()
        if total_configs == 0:
            self.stdout.write(self.style.WARNING(
                'No hay configuraciones de búsqueda activas. '
                'Crea una en /busqueda/ o en el Admin.'
            ))
            return

        resultados = BusquedaService.ejecutar_todas()

        for r in resultados:
            sc = r.get('scrape', {})
            self.stdout.write(
                f"  {r['zona']} ({r['usuario']}): "
                f"scrape +{sc.get('nuevos', 0)} nuevas, "
                f"{r['propiedades_reanalizadas']} reanalizadas, "
                f"{r['oportunidades']} oportunidades"
            )
            for f in sc.get('fuentes', []):
                if f.get('omitido'):
                    continue
                self.stdout.write(
                    f"    {f['fuente']}: {f['encontrados']} encontrados, "
                    f"{f['nuevos']} nuevos, {f.get('estado', '')}"
                )

        self.stdout.write(self.style.SUCCESS(
            f'Búsqueda completada: {len(resultados)} configuración(es) procesada(s)'
        ))