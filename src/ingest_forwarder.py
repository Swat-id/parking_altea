"""
Reenvío asíncrono de ingestión v5.0.1

Copia el cuerpo HTTP original (bytes) hacia parking-monitor sin bloquear
el procesamiento local. Un fallo remoto nunca altera la respuesta al dispositivo.
"""

import logging
import threading

import requests

import config

logger = logging.getLogger(__name__)


def _post_raw(url, raw_body, content_type):
    headers = {
        'Content-Type': content_type or 'application/json'
    }
    try:
        response = requests.post(
            url,
            data=raw_body,
            headers=headers,
            timeout=config.INGEST_FORWARD_TIMEOUT,
            verify=True
        )
        if response.status_code >= 400:
            logger.warning(
                "Ingest forward HTTP %s a %s (body_len=%s)",
                response.status_code, url, len(raw_body or b'')
            )
        else:
            logger.info(
                "Ingest forward OK HTTP %s a %s (body_len=%s)",
                response.status_code, url, len(raw_body or b'')
            )
    except Exception as exc:
        logger.warning("Ingest forward falló hacia %s: %s", url, exc)


def forward_ingest(url, raw_body, content_type=None):
    """
    Dispara el reenvío en un hilo daemon y vuelve de inmediato.

    Args:
        url: destino remoto
        raw_body: bytes exactamente como llegaron (o str; se codifica utf-8)
        content_type: Content-Type original; default application/json
    """
    if not getattr(config, 'INGEST_FORWARD_ENABLED', True):
        return
    if not url:
        return
    if raw_body is None:
        raw_body = b''
    if isinstance(raw_body, str):
        raw_body = raw_body.encode('utf-8')

    thread = threading.Thread(
        target=_post_raw,
        args=(url, raw_body, content_type),
        daemon=True,
        name='ingest-forward'
    )
    thread.start()
