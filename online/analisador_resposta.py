from __future__ import annotations

import json
import re

from .modelos import (
    CookieObservado,
    Evidencia,
    HTTPResposta,
)


def _normalizar_nome(nome):
    return nome.strip().lower()


def _headers_dict(resposta):
    return {
        _normalizar_nome(header.nome): header.valor
        for header in resposta.headers
    }


def _detectar_json(resposta):
    content_type = resposta.content_type.lower()
    corpo = resposta.corpo.strip()

    if "application/json" in content_type:
        try:
            objeto = json.loads(corpo)
            return {
                "detectado": True,
                "valido": True,
                "tipo": type(objeto).__name__,
                "quantidade": 1,
            }
        except json.JSONDecodeError:
            return {
                "detectado": True,
                "valido": False,
                "tipo": None,
                "quantidade": 0,
            }

    if corpo.startswith("{") or corpo.startswith("["):
        try:
            objeto = json.loads(corpo)
            return {
                "detectado": True,
                "valido": True,
                "tipo": type(objeto).__name__,
                "quantidade": 1,
            }
        except json.JSONDecodeError:
            pass

    return {
        "detectado": False,
        "valido": False,
        "tipo": None,
        "quantidade": 0,
    }


def _detectar_html(resposta):
    content_type = resposta.content_type.lower()
    corpo = resposta.corpo.lower()

    detectado = (
        "text/html" in content_type
        or "<html" in corpo
        or "<!doctype html" in corpo
    )

    return {
        "detectado": detectado,
        "content_type": resposta.content_type,
    }


def _detectar_cookies(resposta):
    cookies = []

    for header in resposta.headers:
        if _normalizar_nome(header.nome) != "set-cookie":
            continue

        partes = [
            parte.strip()
            for parte in header.valor.split(";")
        ]

        if not partes or "=" not in partes[0]:
            continue

        nome, _ = partes[0].split("=", 1)

        atributos = {}

        for atributo in partes[1:]:
            if "=" in atributo:
                chave, valor = atributo.split(
                    "=", 1
                )
                atributos[
                    _normalizar_nome(chave)
                ] = valor.strip()
            else:
                atributos[
                    _normalizar_nome(atributo)
                ] = True

        cookies.append(
            CookieObservado(
                nome=nome.strip(),
                atributos=atributos,
            )
        )

    return cookies


def _detectar_autenticacao(headers):
    encontrados = []

    authorization = headers.get("authorization")

    if authorization:
        encontrados.append(
            {
                "tipo": "Authorization",
                "esquema": (
                    authorization.split(
                        None, 1
                    )[0]
                    if authorization
                    else ""
                ),
            }
        )

    www_authenticate = headers.get(
        "www-authenticate"
    )

    if www_authenticate:
        encontrados.append(
            {
                "tipo": "WWW-Authenticate",
                "valor_observado": True,
            }
        )

    return encontrados


def _detectar_tecnologias(headers):
    tecnologias = []

    servidor = headers.get("server", "")
    powered = headers.get(
        "x-powered-by",
        "",
    )

    texto = (
        f"{servidor} {powered}"
    ).lower()

    padroes = {
        "nginx": r"\bnginx\b",
        "apache": r"\bapache\b",
        "cloudflare": r"\bcloudflare\b",
        "express": r"\bexpress\b",
        "php": r"\bphp\b",
        "iis": r"\biis\b",
    }

    for nome, padrao in padroes.items():
        if re.search(padrao, texto):
            tecnologias.append(nome)

    return sorted(set(tecnologias))


def _analisar_headers(headers):
    nomes = sorted(headers.keys())

    seguranca = {
        "strict_transport_security": (
            "strict-transport-security" in headers
        ),
        "content_security_policy": (
            "content-security-policy" in headers
        ),
        "x_content_type_options": (
            "x-content-type-options" in headers
        ),
        "x_frame_options": (
            "x-frame-options" in headers
        ),
        "referrer_policy": (
            "referrer-policy" in headers
        ),
    }

    ausentes = [
        nome
        for nome, presente in seguranca.items()
        if not presente
    ]

    return {
        "quantidade": len(nomes),
        "nomes": nomes,
        "cabecalhos_seguranca": seguranca,
        "indicadores_ausentes": ausentes,
    }


def _criar_evidencias(
    resposta,
    headers,
    cookies,
    json_info,
    autenticacao,
    tecnologias,
):
    evidencias = []

    if resposta.status_code >= 400:
        evidencias.append(
            Evidencia(
                identificador="HTTP-001",
                categoria="http",
                titulo="Resposta HTTP de erro",
                descricao=(
                    "Foi observada uma resposta "
                    "HTTP com código igual ou superior "
                    "a 400."
                ),
                origem="HTTP status",
                confianca="ALTA",
                detalhes={
                    "status_code": resposta.status_code
                },
            )
        )

    if json_info["detectado"]:
        evidencias.append(
            Evidencia(
                identificador="FMT-001",
                categoria="formato",
                titulo="JSON observado",
                descricao=(
                    "A resposta apresenta "
                    "indicadores compatíveis com JSON."
                ),
                origem="Content-Type/corpo",
                confianca=(
                    "ALTA"
                    if json_info["valido"]
                    else "MEDIA"
                ),
            )
        )

    if cookies:
        evidencias.append(
            Evidencia(
                identificador="SES-001",
                categoria="sessao",
                titulo="Cookie de resposta observado",
                descricao=(
                    "A resposta contém um ou mais "
                    "cookies enviados pelo servidor."
                ),
                origem="Set-Cookie",
                confianca="ALTA",
                detalhes={
                    "quantidade": len(cookies)
                },
            )
        )

    if autenticacao:
        evidencias.append(
            Evidencia(
                identificador="AUTH-001",
                categoria="autenticacao",
                titulo="Indicador de autenticação HTTP",
                descricao=(
                    "Foram observados headers associados "
                    "a mecanismos de autenticação."
                ),
                origem="Headers HTTP",
                confianca="ALTA",
            )
        )

    for tecnologia in tecnologias:
        evidencias.append(
            Evidencia(
                identificador=f"TECH-{len(evidencias)+1:03d}",
                categoria="tecnologia",
                titulo="Tecnologia indicada",
                descricao=(
                    "Um header da resposta apresenta "
                    "um indicador textual compatível "
                    f"com {tecnologia}."
                ),
                origem="Headers HTTP",
                confianca="MEDIA",
                detalhes={
                    "tecnologia": tecnologia
                },
            )
        )

    return evidencias


def analisar_resposta(resposta: HTTPResposta):
    """
    Analisa passivamente uma resposta HTTP já obtida.

    Não realiza novas requisições.
    Não testa exploração.
    Não altera a resposta original.
    """

    headers = _headers_dict(resposta)

    cookies = _detectar_cookies(resposta)

    json_info = _detectar_json(resposta)

    html_info = _detectar_html(resposta)

    autenticacao = _detectar_autenticacao(
        headers
    )

    tecnologias = _detectar_tecnologias(
        headers
    )

    headers_info = _analisar_headers(
        headers
    )

    evidencias = _criar_evidencias(
        resposta,
        headers,
        cookies,
        json_info,
        autenticacao,
        tecnologias,
    )

    return {
        "url": resposta.url,
        "status_code": resposta.status_code,
        "reason": resposta.reason,
        "http_version": resposta.http_version,
        "tempo_resposta_ms": (
            resposta.tempo_resposta_ms
        ),
        "headers": headers_info,
        "cookies": cookies,
        "json": json_info,
        "html": html_info,
        "autenticacao": autenticacao,
        "tecnologias": tecnologias,
        "redirecionamentos": (
            resposta.redirecionamentos
        ),
        "evidencias": evidencias,
    }
