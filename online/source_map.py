from __future__ import annotations

from urllib.parse import urljoin


def normalizar_referencia_source_map(referencia: str) -> str:
    """Normaliza uma referência de Source Map observada no JavaScript."""
    return referencia.strip()


def classificar_referencia_source_map(referencia: str) -> str:
    """Classifica a forma da referência do Source Map."""
    referencia = normalizar_referencia_source_map(referencia)

    if referencia.startswith(("http://", "https://")):
        return "absoluta"

    if referencia.startswith("/"):
        return "absoluta_site"

    return "relativa"


def resolver_url_source_map(
    referencia: str,
    script_url: str = "",
) -> str:
    """Resolve uma referência de Source Map em relação à URL do script."""
    referencia = normalizar_referencia_source_map(referencia)

    if not referencia:
        return ""

    if not script_url:
        return referencia

    return urljoin(script_url, referencia)
