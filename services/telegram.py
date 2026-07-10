"""Envío de alertas por Telegram Bot API (gratis)."""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def telegram_configurado():
    return bool(getattr(settings, 'TELEGRAM_BOT_TOKEN', ''))


def enviar_mensaje(chat_id, mensaje):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token or not chat_id:
        return False

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    try:
        resp = requests.post(
            url,
            json={
                'chat_id': chat_id,
                'text': mensaje,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return True
        logger.warning('Telegram error %s: %s', resp.status_code, resp.text[:200])
    except requests.RequestException as exc:
        logger.warning('Telegram request failed: %s', exc)
    return False