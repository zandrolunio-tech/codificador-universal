from __future__ import annotations

import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .modelos import HTTPHeader, HTTPResposta, OnlineResultado


USER_AGENT = (
    "CodificadorUniversal/2.0 "
    "(AnaliseTecnica-Autorizada)"
)


class RedirectTracker(HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.historico = []

    def redirect_request(
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        self.historico.append(newurl)
        return super().redirect_request(
            req,
            fp,
            code,
            msg,
            headers,
            newurl,
        )


def _converter_headers(headers):
    resultado = []

    for nome, valor in headers.items():
        resultado.append(
            HTTPHeader(
                nome=nome,
                valor=valor,
            )
        )

    return resultado


def _versao_http(response):
    versao = getattr(response, "version", None)

    mapa = {
        10: "HTTP/1.0",
        11: "HTTP/1.1",
    }

    return mapa.get(
        versao,
        str(versao or "DESCONHECIDA"),
    )


def coletar(
    url,
    timeout=10,
    max_bytes=1_000_000,
    user_agent=USER_AGENT,
):
    """
    Realiza uma coleta HTTP/HTTPS controlada.

    Não executa exploração, brute force ou bypass.
    Apenas solicita o recurso fornecido e registra
    metadados da resposta.
    """

    resultado = OnlineResultado(alvo=url)

    tracker = RedirectTracker()
    opener = build_opener(tracker)

    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "*/*",
        },
        method="GET",
    )

    inicio = time.perf_counter()

    try:
        with opener.open(
            request,
            timeout=timeout,
        ) as response:

            tempo_ms = (
                time.perf_counter() - inicio
            ) * 1000

            corpo_bytes = response.read(
                max_bytes + 1
            )

            truncado = (
                len(corpo_bytes) > max_bytes
            )

            if truncado:
                corpo_bytes = corpo_bytes[
                    :max_bytes
                ]

            charset = response.headers.get_content_charset()

            if charset:
                encoding = charset
            else:
                encoding = "utf-8"

            corpo = corpo_bytes.decode(
                encoding,
                errors="replace",
            )

            content_type = (
                response.headers.get(
                    "Content-Type",
                    "",
                )
            )

            resposta = HTTPResposta(
                url=response.geturl(),
                status_code=response.status,
                reason=response.reason or "",
                http_version=_versao_http(response),
                headers=_converter_headers(
                    response.headers
                ),
                content_type=content_type,
                tamanho=len(corpo_bytes),
                corpo=corpo,
                tempo_resposta_ms=round(
                    tempo_ms,
                    2,
                ),
                redirecionamentos=list(
                    tracker.historico
                ),
            )

            resultado.respostas.append(
                resposta
            )

            resultado.sucesso = True

            resultado.metadados.update(
                {
                    "timeout": timeout,
                    "limite_corpo_bytes": max_bytes,
                    "corpo_truncado": truncado,
                    "metodo": "GET",
                }
            )

    except HTTPError as erro:
        tempo_ms = (
            time.perf_counter() - inicio
        ) * 1000

        try:
            corpo_bytes = erro.read(
                max_bytes + 1
            )
        except Exception:
            corpo_bytes = b""

        if len(corpo_bytes) > max_bytes:
            corpo_bytes = corpo_bytes[
                :max_bytes
            ]

        corpo = corpo_bytes.decode(
            "utf-8",
            errors="replace",
        )

        resposta = HTTPResposta(
            url=erro.geturl(),
            status_code=erro.code,
            reason=erro.reason or "",
            http_version="DESCONHECIDA",
            headers=_converter_headers(
                erro.headers
            ),
            content_type=erro.headers.get(
                "Content-Type",
                "",
            ),
            tamanho=len(corpo_bytes),
            corpo=corpo,
            tempo_resposta_ms=round(
                tempo_ms,
                2,
            ),
            redirecionamentos=list(
                tracker.historico
            ),
        )

        resultado.respostas.append(
            resposta
        )

        resultado.metadados.update(
            {
                "timeout": timeout,
                "limite_corpo_bytes": max_bytes,
                "corpo_truncado": (
                    len(corpo_bytes) >= max_bytes
                ),
                "metodo": "GET",
                "tipo_erro": "HTTPError",
            }
        )

        resultado.observacoes.append(
            "O servidor respondeu com um "
            f"status HTTP {erro.code}."
        )

    except URLError as erro:
        resultado.erros.append(
            f"Falha de conexão: {erro.reason}"
        )

    except TimeoutError:
        resultado.erros.append(
            "A conexão excedeu o tempo limite."
        )

    except Exception as erro:
        resultado.erros.append(
            f"Erro inesperado: {type(erro).__name__}: {erro}"
        )

    return resultado
