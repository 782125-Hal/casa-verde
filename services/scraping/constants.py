"""Constantes y mapeos geográficos para scrapers — Tijuana."""

ZONA_SLUGS = {
    'Zona Río': 'zona-rio',
    'La Mesa': 'la-mesa',
    'Las Palmas': 'las-palmas',
    'Playas de Tijuana': 'playas-de-tijuana',
    'Otay': 'otay',
    'Centro': 'centro',
}

CIUDAD = 'tijuana'
ESTADO_SLUG = 'baja-california'

USER_AGENT = (
    'CasaVerdeBot/1.0 (+https://localhost; inmobiliario-interno; contacto=admin@casaverde.local)'
)

RATE_LIMIT_SECONDS = 2.5
MAX_RESULTADOS_POR_FUENTE = 15
REQUEST_TIMEOUT = 20