"""Fetcher con Playwright — navegador headless anti-detección."""
import logging
import time

from django.conf import settings

from services.scraping.constants import RATE_LIMIT_SECONDS

logger = logging.getLogger(__name__)

BROWSER_USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['es-MX', 'es', 'en'] });
window.chrome = { runtime: {} };
"""


class PlaywrightSession:
    """Sesión reutilizable de Chromium para múltiples URLs."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._last_request = 0.0

    def __enter__(self):
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=getattr(settings, 'SCRAPING_PLAYWRIGHT_HEADLESS', True),
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ],
        )
        self._context = self._browser.new_context(
            user_agent=BROWSER_USER_AGENT,
            locale='es-MX',
            timezone_id='America/Tijuana',
            viewport={'width': 1366, 'height': 768},
            extra_http_headers={'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8'},
        )
        self._context.add_init_script(STEALTH_SCRIPT)
        logger.info('Playwright: navegador iniciado (stealth)')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info('Playwright: navegador cerrado')

    def _es_captcha(self, html):
        html_lower = html.lower()
        indicadores = ('human verification', 'captcha', 'cf-challenge', 'just a moment', 'access denied')
        return any(x in html_lower for x in indicadores) or len(html) < 8000

    def fetch(self, url, wait_selector=None, wait_ms=None, reintentos=2):
        if not self._context:
            raise RuntimeError('PlaywrightSession no iniciada')

        rate = getattr(settings, 'SCRAPING_PLAYWRIGHT_RATE_LIMIT', RATE_LIMIT_SECONDS)
        wait_ms = wait_ms or getattr(settings, 'SCRAPING_PLAYWRIGHT_WAIT_MS', 3000)
        timeout = getattr(settings, 'SCRAPING_PLAYWRIGHT_TIMEOUT', 45000)

        ultimo_error = None
        for intento in range(reintentos):
            elapsed = time.time() - self._last_request
            if elapsed < rate:
                time.sleep(rate - elapsed)

            page = self._context.new_page()
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=timeout)

                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=20000)
                    except Exception:
                        logger.debug('Selector timeout: %s', wait_selector)

                page.wait_for_timeout(wait_ms + intento * 2000)
                page.evaluate('window.scrollTo(0, Math.min(800, document.body.scrollHeight))')
                page.wait_for_timeout(1000)

                html = page.content()
                self._last_request = time.time()

                if self._es_captcha(html):
                    ultimo_error = f'Captcha o página bloqueada ({len(html)} bytes)'
                    logger.warning('Intento %d/%d bloqueado: %s', intento + 1, reintentos, url)
                    continue

                return html
            except Exception as exc:
                ultimo_error = str(exc)
                logger.warning('Intento %d Playwright error: %s', intento + 1, exc)
            finally:
                page.close()

        raise ValueError(ultimo_error or 'No se pudo cargar la página')


def fetch_con_playwright(url, wait_selector=None):
    with PlaywrightSession() as session:
        return session.fetch(url, wait_selector=wait_selector)


def playwright_disponible():
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False