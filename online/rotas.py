from __future__ import annotations

from urllib.parse import parse_qsl, urlparse

from .urls import normalizar_url


def _metodo_normalizado(metodo: str) -> str:
    return (metodo or "").strip().upper()


def _parametros_da_query(query: str) -> list[str]:
    if not query:
        return []

    parametros = []

    for nome, _valor in parse_qsl(
        query,
        keep_blank_values=True,
    ):
        if nome and nome not in parametros:
            parametros.append(nome)

    return parametros


def normalizar_rota(
    url: str,
    base_url: str = "",
    origem: str = "",
    metodo: str = "",
) -> dict:
    """
    Normaliza uma URL observada para o inventário de rotas.

    A função é passiva: não realiza requisições.
    """

    item_url = normalizar_url(
        url,
        base_url=base_url,
        origem=origem,
    )

    if not item_url:
        return {}

    url_normalizada = item_url["url"]

    try:
        parsed = urlparse(url_normalizada)
    except (TypeError, ValueError):
        return {}

    esquema = item_url.get(
        "esquema",
        "",
    )

    if esquema not in {
        "http",
        "https",
        "ws",
        "wss",
    }:
        return {}

    host = item_url.get(
        "host",
        "",
    )

    if not host:
        return {}

    porta = item_url.get(
        "porta",
    )

    if porta is not None:
        if esquema in {"http", "https"}:
            url_base_normalizada = (
                f"{esquema}://{host}:{porta}"
                if (
                    (esquema == "http" and porta != 80)
                    or (esquema == "https" and porta != 443)
                )
                else f"{esquema}://{host}"
            )
        else:
            url_base_normalizada = (
                f"{esquema}://{host}:{porta}"
                if (
                    (esquema == "ws" and porta != 80)
                    or (esquema == "wss" and porta != 443)
                )
                else f"{esquema}://{host}"
            )
    else:
        url_base_normalizada = f"{esquema}://{host}"

    return {
        "rota": parsed.path or "/",
        "metodo": _metodo_normalizado(metodo),
        "origens": list(
            item_url.get(
                "origens",
                [],
            )
        ),
        "url_base": url_base_normalizada,
        "parametros": _parametros_da_query(
            parsed.query
        ),
        "tipo": item_url.get(
            "tipo",
            "desconhecida",
        ),
        "interna": bool(
            item_url.get(
                "interna",
                False,
            )
        ),
        "confianca": "alta",
    }
