from __future__ import annotations

from urllib.parse import urljoin, urlparse


def _porta_padrao(esquema: str) -> int | None:
    esquema = esquema.lower()

    if esquema in {"http", "ws"}:
        return 80

    if esquema in {"https", "wss"}:
        return 443

    return None


def _tipo_url(esquema: str) -> str:
    esquema = esquema.lower()

    if esquema in {"http", "https"}:
        return "http"

    if esquema in {"ws", "wss"}:
        return "websocket"

    if esquema:
        return esquema

    return "desconhecida"


def _mesma_origem(url: str, base_url: str) -> bool:
    try:
        alvo = urlparse(url)
        base = urlparse(base_url)

        if not alvo.netloc or not base.netloc:
            return False

        esquema_alvo = alvo.scheme.lower()
        esquema_base = base.scheme.lower()

        if esquema_alvo != esquema_base:
            return False

        host_alvo = alvo.hostname.lower() if alvo.hostname else ""
        host_base = base.hostname.lower() if base.hostname else ""

        if host_alvo != host_base:
            return False

        porta_alvo = alvo.port or _porta_padrao(esquema_alvo)
        porta_base = base.port or _porta_padrao(esquema_base)

        return porta_alvo == porta_base

    except ValueError:
        return False


def normalizar_url(
    url: str,
    base_url: str = "",
    origem: str = "",
) -> dict:
    referencia = (url or "").strip()

    if not referencia:
        return {}

    # Rejeita referências que aparentam possuir um esquema
    # malformado antes de tentar resolver uma URL relativa.
    if "://" in referencia and not referencia.split("://", 1)[0].strip():
        return {}

    try:
        absoluta = (
            urljoin(base_url, referencia)
            if base_url
            else referencia
        )

        parsed = urlparse(absoluta)

        if not parsed.scheme:
            return {}

        host = parsed.hostname or ""

        if not host and parsed.scheme not in {
            "mailto",
            "tel",
            "data",
            "blob",
            "javascript",
        }:
            return {}

        esquema = parsed.scheme.lower()

        try:
            porta = parsed.port
        except ValueError:
            return {}

        if porta is None:
            porta = _porta_padrao(esquema)

        tipo = _tipo_url(esquema)

        interna = _mesma_origem(
            absoluta,
            base_url,
        )

        return {
            "url": absoluta,
            "esquema": esquema,
            "host": host.lower(),
            "porta": porta,
            "caminho": parsed.path,
            "query": parsed.query,
            "fragmento": parsed.fragment,
            "origens": [origem] if origem else [],
            "interna": interna,
            "tipo": tipo,
        }

    except (TypeError, ValueError):
        return {}
