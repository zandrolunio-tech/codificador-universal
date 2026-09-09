from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any

from online.rastreador_javascript import (
    explicar_cadeia_variaveis,
)


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


def _extrair_variavel_da_fonte(
    conteudo: str,
    fonte_tipo: str,
) -> str | None:
    """
    Identifica uma variável atribuída diretamente a uma fonte conhecida.

    Exemplos reconhecidos:

        const resposta = xhr.response;
        let dados = xhr.response;
        var resultado = xhr.responseText;
        var corpo = xhr.response;

    A análise é puramente estática.
    """

    if not conteudo or not fonte_tipo:
        return None

    propriedades = {
        "XMLHttpRequest.response": "response",
        "XMLHttpRequest.responseText": "responseText",
    }

    propriedade = propriedades.get(fonte_tipo)

    if not propriedade:
        return None

    padrao = (
        r"\b(?:const|let|var)\s+"
        r"([A-Za-z_$][\w$]*)\s*=\s*"
        r"[A-Za-z_$][\w$]*\."
        + re.escape(propriedade)
        + r"\b"
    )

    correspondencia = re.search(
        padrao,
        conteudo,
    )

    if correspondencia:
        return correspondencia.group(1)

    return None


def _extrair_variavel_da_variavel(
    conteudo: str,
    variavel_origem: str,
) -> str | None:
    """
    Identifica uma variável que recebe diretamente o valor
    de outra variável conhecida.

    Exemplos reconhecidos:

        const dados = resposta;
        let dados = resposta;
        var resultado = resposta;

    A análise é puramente estática.
    """

    if not conteudo or not variavel_origem:
        return None

    padrao = (
        r"\b(?:const|let|var)\s+"
        r"([A-Za-z_$][\w$]*)\s*=\s*"
        rf"{re.escape(variavel_origem)}\b"
    )

    correspondencia = re.search(
        padrao,
        conteudo,
    )

    if correspondencia:
        return correspondencia.group(1)

    return None


def _encontrar_cadeia_variaveis(
    codigo: str,
    variavel_origem: str,
    variavel_destino: str,
) -> list[str]:
    """
    Verifica estaticamente se existe uma cadeia direta de
    atribuições entre variáveis.

    Exemplo:

        const resposta = xhr.responseText;
        const dados = resposta;
        element.innerHTML = dados;

    Para origem "resposta" e destino "dados",
    retorna:

        ["resposta", "dados"]

    A análise é puramente estática e não executa JavaScript.
    """

    if not codigo:
        return []

    if not variavel_origem or not variavel_destino:
        return []

    if variavel_origem == variavel_destino:
        return [variavel_origem]

    linhas = codigo.splitlines()

    padrao = re.compile(
        r"\b(?:const|let|var)\s+"
        r"([A-Za-z_$][\w$]*)\s*=\s*"
        r"([A-Za-z_$][\w$]*)\b"
    )

    atribuicoes = {}

    for linha in linhas:
        correspondencia = padrao.search(linha)

        if not correspondencia:
            continue

        destino = correspondencia.group(1)
        origem = correspondencia.group(2)

        atribuicoes[destino] = origem

    cadeia = [variavel_destino]
    atual = variavel_destino
    visitadas = set()

    while atual not in visitadas:
        visitadas.add(atual)

        origem = atribuicoes.get(atual)

        if origem is None:
            return []

        cadeia.append(origem)

        if origem == variavel_origem:
            cadeia.reverse()
            return cadeia

        atual = origem

    return []


def correlacionar_javascript(
    analises: list[dict[str, Any]],
) -> list[Correlacao]:
    """
    Correlaciona padrões estáticos de JavaScript.

    Procura uma relação entre uma fonte de dados e um DOM sink
    que já tenham sido identificados pelo analisador.

    Esta função é puramente estática:
    - não executa JavaScript;
    - não realiza requisições;
    - não explora o alvo;
    - não confirma uma vulnerabilidade.

    Uma relação fonte -> sink é tratada como evidência para
    revisão manual.
    """

    resultado: list[Correlacao] = []

    for item in analises:
        if not isinstance(item, dict):
            continue

        analise = item.get("analise", {})

        if not isinstance(analise, dict):
            continue

        dom_sinks = analise.get(
            "dom_sinks",
            [],
        )

        fontes_dados = analise.get(
            "fontes_dados",
            [],
        )

        if not isinstance(dom_sinks, list):
            continue

        if not isinstance(fontes_dados, list):
            continue

        if not dom_sinks or not fontes_dados:
            continue

        origem = item.get(
            "origem",
            "",
        )

        url = item.get(
            "url",
            "",
        )

        codigo = item.get(
            "conteudo",
            "",
        )

        for sink in dom_sinks:
            if not isinstance(sink, dict):
                continue

            sink_tipo = sink.get(
                "tipo",
                "",
            )

            sink_linha = sink.get(
                "linha",
            )

            sink_conteudo = sink.get(
                "conteudo",
                "",
            )

            for fonte in fontes_dados:
                if not isinstance(fonte, dict):
                    continue

                fonte_tipo = fonte.get(
                    "tipo",
                    "",
                )

                fonte_linha = fonte.get(
                    "linha",
                )

                fonte_conteudo = fonte.get(
                    "conteudo",
                    "",
                )

                mesma_linha = (
                    sink_linha is not None
                    and fonte_linha is not None
                    and sink_linha == fonte_linha
                )

                if mesma_linha:
                    resultado.append(
                        Correlacao(
                            identificador=(
                                "CORR-JS-DOM-SOURCE-SINK"
                            ),
                            titulo=(
                                "Cadeia estática "
                                "fonte → DOM sink observada"
                            ),
                            categoria="javascript",
                            severidade="baixo",
                            confianca="ALTA",
                            observacao=(
                                "Foi observada, estaticamente, "
                                "uma fonte de dados associada "
                                "a um DOM sink na mesma linha. "
                                "Isso não confirma uma "
                                "vulnerabilidade e requer "
                                "revisão do fluxo de dados."
                            ),
                            recomendacao=(
                                "Revisar a origem, o tratamento "
                                "e a sanitização dos dados antes "
                                "de sua utilização no DOM."
                            ),
                            metadados={
                                "origem": origem,
                                "url": url,
                                "sink": sink_tipo,
                                "source": fonte_tipo,
                                "linha_sink": sink_linha,
                                "linha_source": fonte_linha,
                                "conteudo_sink": sink_conteudo,
                                "conteudo_source": fonte_conteudo,
                            },
                        )
                    )
                    continue

                variavel = _extrair_variavel_da_fonte(
                    fonte_conteudo,
                    fonte_tipo,
                )

                if not variavel:
                    continue

                variavel_sink = variavel

                variavel_no_sink = re.search(
                    rf"\b{re.escape(variavel_sink)}\b",
                    sink_conteudo,
                )

                cadeia_variaveis = [variavel]

                if not variavel_no_sink and codigo:
                    variaveis_no_sink = re.findall(
                        r"\b[A-Za-z_$][\w$]*\b",
                        sink_conteudo,
                    )

                    for variavel_candidata in variaveis_no_sink:
                        cadeia = _encontrar_cadeia_variaveis(
                            codigo,
                            variavel,
                            variavel_candidata,
                        )

                        if cadeia:
                            cadeia_variaveis = cadeia
                            variavel_sink = cadeia[-1]

                            variavel_no_sink = re.search(
                                rf"\b{re.escape(variavel_sink)}\b",
                                sink_conteudo,
                            )

                            if variavel_no_sink:
                                break

                if not variavel_no_sink:
                    continue

                resultado.append(
                    Correlacao(
                        identificador=(
                            "CORR-JS-FLUXO-DOM-SOURCE-SINK"
                        ),
                        titulo=(
                            "Fluxo estático "
                            "fonte → variável → DOM sink"
                        ),
                        categoria="javascript",
                        severidade="baixo",
                        confianca="ALTA",
                        observacao=(
                            "Foi identificado, estaticamente, "
                            "um fluxo em que uma variável recebe "
                            "dados de uma fonte conhecida e "
                            "posteriormente é utilizada em um "
                            "DOM sink. Isso não confirma uma "
                            "vulnerabilidade e requer revisão "
                            "manual do fluxo de dados."
                        ),
                        recomendacao=(
                            "Revisar a origem dos dados, as "
                            "transformações realizadas sobre a "
                            "variável e a sanitização antes do "
                            "uso no DOM."
                        ),
                        metadados={
                            "origem": origem,
                            "url": url,
                            "sink": sink_tipo,
                            "source": fonte_tipo,
                            "variavel": variavel_sink,
                            "cadeia_variaveis": cadeia_variaveis,
                            "explicacao_cadeia": (
                                explicar_cadeia_variaveis(
                                    cadeia_variaveis
                                )
                            ),
                            "linha_sink": sink_linha,
                            "linha_source": fonte_linha,
                            "conteudo_sink": sink_conteudo,
                            "conteudo_source": fonte_conteudo,
                        },
                    )
                )

    return resultado
