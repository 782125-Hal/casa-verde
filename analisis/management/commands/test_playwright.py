"""Prueba rápida de Playwright contra un portal."""
from django.conf import settings
from django.core.management.base import BaseCommand

from analisis.models import ConfiguracionBusqueda
from services.scraping.playwright_fetcher import PlaywrightSession, playwright_disponible
from services.scraping.registry import obtener_scraper


class Command(BaseCommand):
    help = 'Prueba scraping con Playwright en una zona'

    def add_arguments(self, parser):
        parser.add_argument('--zona', default='La Mesa', help='Nombre de zona Tijuana')
        parser.add_argument('--fuente', default='mercado libre', help='mercado libre, lamudi, inmuebles24, vivanuncios')

    def handle(self, *args, **options):
        if not playwright_disponible():
            self.stdout.write(self.style.ERROR(
                'Playwright no instalado. Ejecute: pip install playwright && playwright install chromium'
            ))
            return

        config = ConfiguracionBusqueda.objects.filter(
            zona__nombre=options['zona'], activa=True,
        ).select_related('zona', 'usuario').first()

        if not config:
            self.stdout.write(self.style.ERROR(f'Sin ConfiguracionBusqueda para zona {options["zona"]}'))
            return

        from mercado.models import FuenteDatos
        fuente = FuenteDatos.objects.filter(nombre__icontains=options['fuente'], activa=True).first()
        if not fuente:
            self.stdout.write(self.style.ERROR(f'Fuente no encontrada: {options["fuente"]}'))
            return

        self.stdout.write(f'Motor: Playwright (headless={settings.SCRAPING_PLAYWRIGHT_HEADLESS})')
        self.stdout.write(f'Zona: {config.zona.nombre} | Fuente: {fuente.nombre}')

        with PlaywrightSession() as pw:
            scraper = obtener_scraper(fuente, playwright_session=pw)
            listings = scraper.buscar(config)

        self.stdout.write(self.style.SUCCESS(f'Listados encontrados: {len(listings)}'))
        for i, item in enumerate(listings[:5], 1):
            self.stdout.write(f"  {i}. {item.get('titulo', '')[:60]}")
            self.stdout.write(f"     ${item.get('precio_texto', 'N/A')} — {item.get('url_anuncio', '')[:70]}")