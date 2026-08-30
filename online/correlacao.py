from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


NIVEIS = {
    "informativo": 1,
    "baixo": 2,
    "medio": 3,
    "alto": 4,
    "critico": 5,
}

CONFIANCAS = {
    "BAIXA": 1,
    "MEDIA": 2,
    "ALTA": 3,
}


@dataclass
class Correlacao:
    identificador: str
    titulo: str
    categoria: str
    severidade: str
    confianca: str
    evidencias_relacionadas: list[str] = field(default_factory=list)
    observacao: str = ""
    recomendacao: str = ""
    metadados: dict[str, Any] = field(default_factory=dict)


def _nivel(valor: str) -> int:
    return NIVEIS.get(
        (valor or "informativo").strip().lower(),
        1,
    )


def _confianca(valor: str) -> int:
    return CONFIANCAS.get(
        (valor or "MEDIA").strip().upper(),
        2,
    )


def correlacionar(
    evidencias: list[Any],
) -> list[Correlacao]:
    """
    Analisa evidências que já foram produzidas
    pelos módulos anteriores.

    Não realiza:
    - novas conexões;
    - requisições;
    - exploração;
    - alteração do alvo.
    """

    resultado: list[Correlacao] = []

    por_id = {
        getattr(e, "identificador", ""): e
        for e in evidencias
    }

    # ========================================================
    # TLS
    # ========================================================

    if {
        "TLS-VERSAO",
        "TLS-CONEXAO",
    }.issubset(por_id):

        resultado.append(
            Correlacao(
                identificador="CORR-TLS-CONEXAO",
                titulo="Postura TLS observada",
                categoria="tls",
                severidade="informativo",
                confianca="ALTA",
                evidencias_relacionadas=[
                    "TLS-VERSAO",
                    "TLS-CONEXAO",
                ],
                observacao=(
                    "Foram observadas evidências "
                    "consistentes sobre a negociação TLS."
                ),
                recomendacao=(
                    "Manter TLS moderno e acompanhar "
                    "periodicamente a configuração criptográfica."
                ),
            )
        )

    # ========================================================
    # CERTIFICADO
    # ========================================================

    if {
        "TLS-CERT-VALIDADE",
        "TLS-CERT-SAN",
    }.issubset(por_id):

        resultado.append(
            Correlacao(
                identificador="CORR-CERTIFICADO",
                titulo="Perfil do certificado observado",
                categoria="certificado",
                severidade="informativo",
                confianca="ALTA",
                evidencias_relacionadas=[
                    "TLS-CERT-VALIDADE",
                    "TLS-CERT-SAN",
                ],
                observacao=(
                    "Foram observadas informações "
                    "sobre validade e nomes associados "
                    "ao certificado."
                ),
                recomendacao=(
                    "Confirmar periodicamente a validade "
                    "e os nomes esperados no certificado."
                ),
            )
        )

    # ========================================================
    # HTTP
    # ========================================================

    if "HTTP-STATUS" in por_id:

        evidencia = por_id["HTTP-STATUS"]

        detalhes = getattr(
            evidencia,
            "detalhes",
            {},
        ) or {}

        observacao = detalhes.get(
            "observacao",
            "Código HTTP observado.",
        )

        resultado.append(
            Correlacao(
                identificador="CORR-HTTP-STATUS",
                titulo="Comportamento HTTP observado",
                categoria="http",
                severidade="informativo",
                confianca=getattr(
                    evidencia,
                    "confianca",
                    "MEDIA",
                ),
                evidencias_relacionadas=[
                    "HTTP-STATUS",
                ],
                observacao=observacao,
                recomendacao=(
                    "Interpretar o código HTTP junto "
                    "com headers, conteúdo e contexto."
                ),
            )
        )

    # ========================================================
    # COOKIE + AUTENTICAÇÃO
    # ========================================================

    ids = set(por_id)

    if (
        "COOKIE-OBSERVADO" in ids
        and "AUTH-OBSERVADA" in ids
    ):

        resultado.append(
            Correlacao(
                identificador="CORR-SESSAO-AUTENTICACAO",
                titulo="Mecanismos de sessão e autenticação observados",
                categoria="sessao",
                severidade="informativo",
                confianca="MEDIA",
                evidencias_relacionadas=[
                    "COOKIE-OBSERVADO",
                    "AUTH-OBSERVADA",
                ],
                observacao=(
                    "Foram observados indicadores "
                    "relacionados a sessão e autenticação."
                ),
                recomendacao=(
                    "Revisar atributos de cookies, "
                    "políticas de sessão e mecanismos "
                    "de autenticação."
                ),
            )
        )

    return resultado


def ordenar_correlacoes(
    correlacoes: list[Correlacao],
) -> list[Correlacao]:

    return sorted(
        correlacoes,
        key=lambda item: (
            -_nivel(item.severidade),
            -_confianca(item.confianca),
            item.identificador,
        ),
    )


def serializar_correlacoes(
    correlacoes: list[Correlacao],
) -> list[dict[str, Any]]:

    return [
        {
            "identificador": item.identificador,
            "titulo": item.titulo,
            "categoria": item.categoria,
            "severidade": item.severidade,
            "confianca": item.confianca,
            "evidencias_relacionadas": (
                list(item.evidencias_relacionadas)
            ),
            "observacao": item.observacao,
            "recomendacao": item.recomendacao,
            "metadados": dict(item.metadados),
        }
        for item in correlacoes
    ]
