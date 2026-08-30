from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse


def _parse_data_certificado(valor):
    if not valor:
        return None

    try:
        return datetime.strptime(
            valor,
            "%b %d %H:%M:%S %Y %Z",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _dias_para_expirar(data_expiracao):
    if not data_expiracao:
        return None

    agora = datetime.now(timezone.utc)
    return (data_expiracao - agora).days


def analisar_tls(url: str, timeout: float = 5.0):
    """
    Analisa passivamente a camada TLS de um endpoint HTTPS.

    Não envia requisições HTTP e não realiza exploração.
    Apenas estabelece a conexão TLS necessária para obter
    informações do certificado e da negociação criptográfica.
    """

    parsed = urlparse(url)

    if parsed.scheme.lower() != "https":
        return {
            "detectado": False,
            "sucesso": False,
            "url": url,
            "erro": "O alvo não utiliza HTTPS.",
        }

    host = parsed.hostname

    if not host:
        return {
            "detectado": False,
            "sucesso": False,
            "url": url,
            "erro": "Hostname não identificado.",
        }

    porta = parsed.port or 443

    resultado = {
        "detectado": True,
        "sucesso": False,
        "url": url,
        "host": host,
        "porta": porta,
        "versao_tls": None,
        "cipher": None,
        "alpn": None,
        "certificado": {},
        "erros": [],
    }

    contexto = ssl.create_default_context()

    try:
        with socket.create_connection(
            (host, porta),
            timeout=timeout,
        ) as socket_bruta:

            with contexto.wrap_socket(
                socket_bruta,
                server_hostname=host,
            ) as conexao:

                resultado["sucesso"] = True

                resultado["versao_tls"] = (
                    conexao.version()
                )

                cifra = conexao.cipher()

                if cifra:
                    resultado["cipher"] = {
                        "nome": cifra[0],
                        "protocolo": cifra[1],
                        "bits": cifra[2],
                    }

                resultado["alpn"] = (
                    conexao.selected_alpn_protocol()
                )

                certificado = (
                    conexao.getpeercert()
                )

                emissor = certificado.get(
                    "issuer",
                    (),
                )

                sujeito = certificado.get(
                    "subject",
                    (),
                )

                def nomes_distinguished_name(
                    estrutura
                ):
                    valores = []

                    for grupo in estrutura:
                        for chave, valor in grupo:
                            if chave in {
                                "commonName",
                                "organizationName",
                            }:
                                valores.append(
                                    {
                                        "campo": chave,
                                        "valor": valor,
                                    }
                                )

                    return valores

                not_before = _parse_data_certificado(
                    certificado.get("notBefore")
                )

                not_after = _parse_data_certificado(
                    certificado.get("notAfter")
                )

                resultado["certificado"] = {
                    "sujeito": (
                        nomes_distinguished_name(
                            sujeito
                        )
                    ),
                    "emissor": (
                        nomes_distinguished_name(
                            emissor
                        )
                    ),
                    "serial_number": certificado.get(
                        "serialNumber"
                    ),
                    "not_before": certificado.get(
                        "notBefore"
                    ),
                    "not_after": certificado.get(
                        "notAfter"
                    ),
                    "dias_para_expirar": (
                        _dias_para_expirar(
                            not_after
                        )
                    ),
                    "subject_alt_names": [
                        valor
                        for tipo, valor
                        in certificado.get(
                            "subjectAltName",
                            (),
                        )
                        if tipo == "DNS"
                    ],
                }

    except (
        socket.timeout,
        TimeoutError,
    ) as erro:
        resultado["erros"].append(
            f"Timeout: {erro}"
        )

    except ssl.SSLCertVerificationError as erro:
        resultado["erros"].append(
            "Falha na verificação do certificado: "
            f"{erro}"
        )

    except ssl.SSLError as erro:
        resultado["erros"].append(
            f"Erro TLS: {erro}"
        )

    except OSError as erro:
        resultado["erros"].append(
            f"Erro de conexão: {erro}"
        )

    return resultado
