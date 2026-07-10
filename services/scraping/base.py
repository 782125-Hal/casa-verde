"""Clase base para scrapers — requests + fallback Playwright."""
import json
import logging
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from django.conf import settings

from services.scraping.constants import (
    MAX_RESULTADOS_POR_FUENTE,
    RATE_LIMIT_SECONDS,
    REQUEST_TIMEOUT,
    USER_AGENT,
    ZONA_SLUGS,
)

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    pass


class BaseScraper:
    fuente_nombre = 'Base'
    base_url = ''
    rate_limit = RATE_LIMIT_SECONDS
    max_resultados = MAX_RESULTADOS_POR_FUENTE
    wait_selector = None

    def __init__(self, fuente, playwright_session=None):
        self.fuente = fuente
        self.playwright_session = playwright_session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept-Language': 'es-MX,es;q=0.9',
            'Accept': 'text/html,application/xhtml+xml',
        })
        self._last_request = 0.0
        self._robots_cache = {}

    def zona_slug(self, zona_nombre):
        return ZONA_SLUGS.get(zona_nombre, zona_nombre.lower().replace(' ', '-'))

    def puede_rastrear(self, url):
        if not getattr(settings, 'SCRAPING_RESPECT_ROBOTS', True):
            return True
        parsed = urlparse(url)
        base = f'{parsed.scheme}://{parsed.netloc}'
        if base not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(urljoin(base, '/robots.txt'))
            try:
                rp.read()
                self._robots_cache[base] = rp
            except Exception:
                self._robots_cache[base] = None
        rp = self._robots_cache[base]
        if rp is None:
            return True
        return rp.can_fetch(USER_AGENT, url)

    def _fetch_requests(self, url):
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        self._last_request = time.time()
        if resp.status_code in (403, 202, 429):
            raise ScraperError(f'Bloqueado ({resp.status_code})')
        resp.raise_for_status()
        if len(resp.text) < 500:
            raise ScraperError('Respuesta vacía')
        return resp.text

    def _fetch_playwright(self, url):
        if self.playwright_session:
            return self.playwright_session.fetch(url, wait_selector=self.wait_selector)
        from services.scraping.playwright_fetcher import fetch_con_playwright
        return fetch_con_playwright(url, wait_selector=self.wait_selector)

    def fetch(self, url):
        if not self.puede_rastrear(url):
            raise ScraperError(f'robots.txt bloquea: {url}')

        usar_playwright = getattr(settings, 'SCRAPING_USE_PLAYWRIGHT', True)

        if usar_playwright and self.playwright_session:
            try:
                logger.info('Playwright fetch: %s', url)
                return self._fetch_playwright(url)
            except Exception as exc:
                raise ScraperError(f'Playwright falló {url}: {exc}') from exc

        try:
            return self._fetch_requests(url)
        except (ScraperError, requests.RequestException) as exc:
            if usar_playwright:
                logger.info('Fallback Playwright tras error requests: %s', exc)
                try:
                    return self._fetch_playwright(url)
                except Exception as pw_exc:
                    raise ScraperError(
                        f'No se pudo obtener {url}. Requests: {exc}. Playwright: {pw_exc}'
                    ) from pw_exc
            raise ScraperError(f'Error HTTP {url}: {exc}') from exc

    def parse_html(self, html):
        return BeautifulSoup(html, 'lxml')

    def extraer_json_ld(self, soup):
        items = []
        for tag in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(tag.string or '')
                if isinstance(data, list):
                    items.extend(data)
                else:
                    items.append(data)
            except (json.JSONDecodeError, TypeError):
                continue
        return items

    def extraer_links(self, soup, patrones_href):
        """Extrae enlaces únicos que coinciden con patrones de listado."""
        vistos = set()
        resultados = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '').strip()
            if not href or href in vistos:
                continue
            if any(p in href for p in patrones_href):
                full = urljoin(self.base_url, href)
                if full in vistos:
                    continue
                vistos.add(href)
                vistos.add(full)
                resultados.append((a, full))
        return resultados

    def buscar(self, config):
        raise NotImplementedError

    def parse_detalle_url(self, url):
        raise NotImplementedError