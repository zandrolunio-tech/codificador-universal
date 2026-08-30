from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .modelos import Evidencia


SEVERIDADES = {
    "informativo": 1,
    "baixo": 2,
    "medio": 3,
    "alto": 4,
    "critico": 5,
}


def _normalizar_severidade(valor: str) -> str:
    valor = (valor or "informativo").strip().lower()

    if valor not in SEVERIDADES:
        return "informativo"

    return valor


def criar_evidencia(
    identificador: str,
    titulo: str,
    categoria: str,
    descricao: str,
    confianca: str = "MEDIA",
    severidade: str = "informativo",
    origem: str = "online",
    observacao: str = "",
    recomendacao: str = "",
    metadados: dict[str, Any] | None = None,
) -> Evidencia:

    detalhes = {
        "severidade": _normalizar_severidade(
            severidade
        ),
        "observacao": observacao,
        "recomendacao": recomendacao,
        "metadados": metadados or {},
    }

    return Evidencia(
        identificador=identificador,
        categoria=categoria,
        titulo=titulo,
        descricao=descricao,
        origem=origem,
        confianca=confianca.upper(),
        detalhes=detalhes,
    )


def evidenciar_status_http(
    status_code: int,
) -> Evidencia:

    if status_code >= 500:
        severidade = "medio"
        titulo = "Resposta HTTP de erro do servidor"
        descricao = (
            "O endpoint respondeu com um código "
            "HTTP da classe 5xx."
        )

    elif status_code >= 400:
        severidade = "informativo"
        titulo = "Resposta HTTP de erro do cliente"
        descricao = (
            "O endpoint respondeu com um código "
            "HTTP da classe 4xx."
        )

    elif status_code >= 300:
        severidade = "informativo"
        titulo = "Redirecionamento HTTP observado"
        descricao = (
            "O endpoint respondeu com um código "
            "HTTP da classe 3xx."
        )

    else:
        severidade = "informativo"
        titulo = "Resposta HTTP bem-sucedida"
        descricao = (
            "O endpoint respondeu com um código "
            "HTTP da classe 2xx."
        )

    return criar_evidencia(
        identificador="HTTP-STATUS",
        titulo=titulo,
        categoria="http",
        descricao=descricao,
        confianca="ALTA",
        severidade=severidade,
        origem="resposta_http",
        observacao=f"HTTP {status_code}",
    )


def evidenciar_tls(
    tls: dict[str, Any],
) -> list[Evidencia]:

    evidencias: list[Evidencia] = []

    if not tls.get("detectado"):
        return evidencias

    if tls.get("sucesso"):

        versao = tls.get("versao_tls")

        evidencias.append(
            criar_evidencia(
                identificador="TLS-CONEXAO",
                titulo="Conexão TLS estabelecida",
                categoria="tls",
                descricao=(
                    "Foi possível estabelecer uma conexão "
                    "TLS com o endpoint."
                ),
                confianca="ALTA",
                origem="negociacao_tls",
                observacao=(
                    f"Versão negociada: "
                    f"{versao or 'não informada'}"
                ),
            )
        )

        if versao:
            evidencias.append(
                criar_evidencia(
                    identificador="TLS-VERSAO",
                    titulo="Versão TLS observada",
                    categoria="tls",
                    descricao=(
                        "A versão do protocolo TLS negociada "
                        "foi identificada."
                    ),
                    confianca="ALTA",
                    origem="negociacao_tls",
                    observacao=versao,
                )
            )

        certificado = (
            tls.get("certificado") or {}
        )

        if certificado.get("not_after"):

            dias = certificado.get(
                "dias_para_expirar"
            )

            severidade = "informativo"

            if dias is not None and dias < 0:
                severidade = "alto"

            elif dias is not None and dias <= 30:
                severidade = "medio"

            evidencias.append(
                criar_evidencia(
                    identificador="TLS-CERT-VALIDADE",
                    titulo="Validade do certificado observada",
                    categoria="certificado",
                    descricao=(
                        "A data de expiração do certificado "
                        "foi identificada."
                    ),
                    confianca="ALTA",
                    severidade=severidade,
                    origem="certificado_tls",
                    observacao=(
                        f"Expiração: "
                        f"{certificado['not_after']}; "
                        f"dias restantes: {dias}"
                    ),
                )
            )

        sans = certificado.get(
            "subject_alt_names"
        ) or []

        if sans:
            evidencias.append(
                criar_evidencia(
                    identificador="TLS-CERT-SAN",
                    titulo="Nomes alternativos do certificado",
                    categoria="certificado",
                    descricao=(
                        "Foram identificados nomes DNS "
                        "associados ao certificado."
                    ),
                    confianca="ALTA",
                    origem="certificado_tls",
                    observacao=", ".join(sans),
                )
            )

    else:

        for erro in tls.get("erros", []):
            evidencias.append(
                criar_evidencia(
                    identificador="TLS-ERRO",
                    titulo="Falha na análise TLS",
                    categoria="tls",
                    descricao=(
                        "A conexão TLS não pôde ser "
                        "analisada com sucesso."
                    ),
                    confianca="ALTA",
                    severidade="informativo",
                    origem="negociacao_tls",
                    observacao=str(erro),
                )
            )

    return evidencias


def ordenar_evidencias(
    evidencias: list[Evidencia],
) -> list[Evidencia]:

    def chave(item: Evidencia):
        severidade = (
            item.detalhes.get(
                "severidade",
                "informativo",
            )
        )

        return (
            SEVERIDADES.get(
                _normalizar_severidade(
                    severidade
                ),
                1,
            ),
            item.identificador,
        )

    return sorted(
        evidencias,
        key=chave,
        reverse=True,
    )


def serializar_evidencias(
    evidencias: list[Evidencia],
) -> list[dict[str, Any]]:

    return [
        asdict(evidencia)
        for evidencia in evidencias
    ]
