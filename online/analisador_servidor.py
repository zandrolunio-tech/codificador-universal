from __future__ import annotations

import re
from urllib.parse import urlparse

from .modelos import HTTPResposta, ServidorObservado


PADROES_SERVIDORES = {
    "nginx": "servidor web",
    "apache": "servidor web",
    "apache httpd": "servidor web",
    "iis": "servidor web",
    "caddy": "servidor web",
    "openresty": "servidor web",
    "lighttpd": "servidor web",
    "gunicorn": "servidor de aplicação",
    "uvicorn": "servidor de aplicação",
    "node.js": "runtime/servidor",
    "express": "framework/servidor",
}


def _porta(url: str) -> int:
    parsed = urlparse(url)

    if parsed.port:
        return parsed.port

    if parsed.scheme.lower() == "https":
        return 443

    if parsed.scheme.lower() == "http":
        return 80

    return 0


def _extrair_produto_versao(valor: str) -> tuple[str, str]:
    valor = (valor or "").strip()

    if not valor:
        return "", ""

    primeiro = valor.split()[0]

    if "/" in primeiro:
        produto, versao = primeiro.split("/", 1)
        return produto.strip(), versao.strip()

    return primeiro.strip(), ""


def _familia(produto: str) -> str:
    produto_lower = produto.lower()

    for nome, familia in PADROES_SERVIDORES.items():
        if nome in produto_lower:
            return familia

    return "desconhecida"


def _header(resposta: HTTPResposta, nome: str) -> str:
    nome = nome.lower()

    for header in resposta.headers:
        if header.nome.lower() == nome:
            return header.valor

    return ""


def analisar_servidor(
    resposta: HTTPResposta,
) -> list[ServidorObservado]:
    """
    Identifica servidores apenas a partir de informações
    explicitamente presentes na resposta HTTP.
    """

    encontrados: list[ServidorObservado] = []

    porta = _porta(resposta.url)

    fontes = [
        ("Server", "header_server"),
        ("X-Powered-By", "header_x_powered_by"),
    ]

    for nome_header, origem in fontes:
        valor = _header(resposta, nome_header)

        if not valor:
            continue

        produto, versao = _extrair_produto_versao(valor)

        if not produto:
            continue

        encontrados.append(
            ServidorObservado(
                produto=produto,
                versao=versao,
                familia=_familia(produto),
                porta=porta,
                protocolo=(
                    "HTTPS/TLS"
                    if porta == 443
                    else "HTTP"
                ),
                origem=origem,
                estado="observado",
                confianca="ALTA",
                detalhes={
                    "header": nome_header,
                    "valor_observado": valor,
                },
            )
        )

    return encontrados


def consolidar_servidores(
    servidores: list[ServidorObservado],
) -> list[ServidorObservado]:
    """
    Consolida identificações repetidas sem descartar
    informações provenientes de fontes diferentes.
    """

    resultado: list[ServidorObservado] = []
    vistos: set[tuple[str, str, int, str]] = set()

    for servidor in servidores:
        chave = (
            servidor.produto.lower(),
            servidor.versao.lower(),
            servidor.porta,
            servidor.protocolo.lower(),
        )

        if chave in vistos:
            continue

        vistos.add(chave)
        resultado.append(servidor)

    return sorted(
        resultado,
        key=lambda item: (
            item.porta,
            item.produto.lower(),
            item.versao.lower(),
        ),
    )
