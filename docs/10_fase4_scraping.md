# Fase 4 — Scraping y búsqueda automatizada

## Componentes implementados

| Componente | Ubicación |
|------------|-----------|
| Scrapers portales | `services/scraping/lamudi.py`, `propiedades_com.py`, `vivanuncios.py`, `inmuebles24.py` |
| Orquestador | `services/scraping/service.py` |
| Normalización | `services/scraping/normalizer.py` |
| Registro/dedup | `services/registro.py` |
| Log ejecuciones | Modelo `ScrapeEjecucion` |
| Comando semanal | `python manage.py busqueda_semanal` |
| Celery (opcional) | `config/celery.py`, `analisis/tasks.py` |
| Import URL | `/busqueda/` |
| Import CSV | `/busqueda/` |

## Flujo semanal

1. `busqueda_semanal` lee `ConfiguracionBusqueda` activas
2. Por cada zona ejecuta scrapers de fuentes `portal` activas
3. Normaliza y registra propiedades (dedup por URL)
4. Re-analiza ROI y genera alertas
5. Guarda log en `ScrapeEjecucion`

## Playwright (activo)

```bash
pip install playwright
playwright install chromium

# Probar un portal en La Mesa
python manage.py test_playwright --zona "La Mesa" --fuente lamudi

# Búsqueda completa con Playwright
python manage.py busqueda_semanal
```

Configuración en `config/settings.py`:
- `SCRAPING_USE_PLAYWRIGHT = True`
- `SCRAPING_PLAYWRIGHT_HEADLESS = True`
- `SCRAPING_PLAYWRIGHT_WAIT_MS = 3000`

Alternativas si un portal sigue bloqueando:
- **Importación CSV** desde exportaciones manuales
- **Importación URL** pegando enlaces individuales
- **APIs oficiales** cuando existan

## Programar con cron (macOS/Linux)

```bash
# Cada lunes 7:00 AM
0 7 * * 1 cd "/ruta/Casa Verde" && python3 manage.py busqueda_semanal >> /tmp/casaverde.log 2>&1
```

## Celery (opcional)

```bash
pip install celery redis
celery -A config worker -l info
celery -A config beat -l info
```