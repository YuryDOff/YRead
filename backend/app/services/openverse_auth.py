"""Openverse OAuth2: получение и автообновление access token каждые 10 часов."""
import logging
import os
import threading
import time

import httpx

logger = logging.getLogger(__name__)

OPENVERSE_TOKEN_URL = "https://api.openverse.org/v1/auth_tokens/token/"
REFRESH_INTERVAL_SEC = 9 * 3600  # обновлять за 1 час до истечения (токен живёт 10 ч)

_token: str | None = None
_token_expires_at: float = 0.0
_lock = threading.Lock()


def fetch_token(client_id: str, client_secret: str) -> tuple[str, int]:
    """
    Запросить access token по client_credentials.
    Возвращает (access_token, expires_in секундах).
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            OPENVERSE_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        body = resp.json()
    token = body.get("access_token") or ""
    expires_in = int(body.get("expires_in", 36000))
    return token, expires_in


def _refresh_if_needed() -> None:
    global _token, _token_expires_at
    client_id = os.getenv("OPENVERSE_CLIENT_ID", "").strip()
    client_secret = os.getenv("OPENVERSE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return
    try:
        token, expires_in = fetch_token(client_id, client_secret)
        with _lock:
            _token = token
            _token_expires_at = time.time() + expires_in
        logger.info("Openverse access token refreshed, expires in %s s", expires_in)
    except Exception as e:
        logger.exception("Openverse token refresh failed: %s", e)


def _background_refresh_loop() -> None:
    while True:
        time.sleep(REFRESH_INTERVAL_SEC)
        _refresh_if_needed()


def get_token() -> str:
    """
    Возвращает текущий access token для Openverse API.
    Если заданы OPENVERSE_CLIENT_ID и OPENVERSE_CLIENT_SECRET — использует автообновляемый токен.
    Иначе — OPENVERSE_ACCESS_TOKEN из .env (без автообновления).
    """
    client_id = os.getenv("OPENVERSE_CLIENT_ID", "").strip()
    client_secret = os.getenv("OPENVERSE_CLIENT_SECRET", "").strip()
    if client_id and client_secret:
        with _lock:
            if _token and time.time() < _token_expires_at - 60:
                return _token
        _refresh_if_needed()
        with _lock:
            return _token or ""
    return os.getenv("OPENVERSE_ACCESS_TOKEN", "").strip()


def start_background_refresh() -> None:
    """Запустить фоновое обновление токена каждые ~9 часов (если заданы client_id/secret)."""
    client_id = os.getenv("OPENVERSE_CLIENT_ID", "").strip()
    client_secret = os.getenv("OPENVERSE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        logger.debug("Openverse: OPENVERSE_CLIENT_ID/CLIENT_SECRET not set, skipping token refresh")
        return
    _refresh_if_needed()
    thread = threading.Thread(target=_background_refresh_loop, daemon=True)
    thread.start()
    logger.info("Openverse token background refresh started (every %s h)", REFRESH_INTERVAL_SEC / 3600)
