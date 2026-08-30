from __future__ import annotations

from urllib.parse import urlparse

from .modelos import HTTPResposta, ServicoObservado


PORTAS_CONHECIDAS = {
    21: ("FTP", "FTP"),
    22: ("SSH", "SSH"),
    25: ("SMTP", "SMTP"),
    53: ("DNS", "DNS"),
    80: ("HTTP", "HTTP"),
    110: ("POP3", "POP3"),
    143: ("IMAP", "IMAP"),
    443: ("HTTPS", "TLS"),
    465: ("SMTPS", "TLS"),
    587: ("SMTP Submission", "SMTP"),
    993: ("IMAPS", "TLS"),
    995: ("POP3S", "TLS"),
    3306: ("MySQL", "MySQL"),
    5432: ("PostgreSQL", "PostgreSQL"),
    6379: ("Redis", "Redis"),
    8080: ("HTTP Alternativo", "HTTP"),
    8443: ("HTTPS Alternativo", "TLS"),
}


def porta_do_alvo(alvo: str) -> int:
    """Obtém a porta explícita ou a porta padrão do esquema."""
    parsed = urlparse(alvo)

    if parsed.port:
        return parsed.port

    if parsed.scheme.lower() == "https":
        return 443

    if parsed.scheme.lower() == "http":
        return 80

    return 0


def inferir_servico(
    porta: int,
    transporte: str = "TCP",
) -> ServicoObservado:
    """Cria uma identificação baseada somente na porta conhecida."""

    servico, protocolo = PORTAS_CONHECIDAS.get(
        porta,
        ("Desconhecido", ""),
    )

    if servico == "Desconhecido":
        confianca = "BAIXA"
        estado = "inferido"
    else:
        confianca = "MEDIA"
        estado = "inferido"

    return ServicoObservado(
        porta=porta,
        transporte=transporte,
        servico=servico,
        protocolo=protocolo,
        estado=estado,
        origem="mapeamento_porta",
        confianca=confianca,
        detalhes={
            "base": "porta_conhecida",
        },
    )


def observar_http(
    resposta: HTTPResposta,
) -> ServicoObservado:
    """Registra HTTP como serviço realmente observado."""

    porta = porta_do_alvo(resposta.url)

    return ServicoObservado(
        porta=porta,
        transporte="TCP",
        servico="HTTPS" if porta == 443 else "HTTP",
        protocolo="TLS" if porta == 443 else "HTTP",
        estado="observado",
        origem="resposta_http",
        confianca="ALTA",
        detalhes={
            "status_code": resposta.status_code,
            "content_type": resposta.content_type,
        },
    )


def observar_tls(
    alvo: str,
    tls: dict,
) -> ServicoObservado | None:
    """Registra TLS somente quando a negociação foi observada."""

    if not tls:
        return None

    if not tls.get("sucesso"):
        return None

    porta = porta_do_alvo(alvo)

    if not porta:
        return None

    return ServicoObservado(
        porta=porta,
        transporte="TCP",
        servico="HTTPS" if porta == 443 else "TLS",
        protocolo=tls.get("versao_tls", "TLS"),
        estado="observado",
        origem="negociacao_tls",
        confianca="ALTA",
        detalhes={
            "cipher": tls.get("cipher"),
            "alpn": tls.get("alpn"),
        },
    )


def consolidar_servicos(
    servicos: list[ServicoObservado],
) -> list[ServicoObservado]:
    """
    Remove duplicações e prefere observações reais
    sobre simples inferências.
    """

    melhores: dict[tuple[int, str], ServicoObservado] = {}

    for servico in servicos:
        chave = (
            servico.porta,
            servico.transporte.upper(),
        )

        atual = melhores.get(chave)

        if atual is None:
            melhores[chave] = servico
            continue

        if atual.estado != "observado" and servico.estado == "observado":
            melhores[chave] = servico
            continue

        if (
            atual.confianca != "ALTA"
            and servico.confianca == "ALTA"
        ):
            melhores[chave] = servico

    return sorted(
        melhores.values(),
        key=lambda item: (
            item.porta,
            item.transporte,
        ),
    )
