from __future__ import annotations

from .analisador_resposta import analisar_resposta
from .analisador_servidor import analisar_servidor
from .analisador_tls import analisar_tls
from .cliente_http import coletar
from .correlacao import correlacionar, ordenar_correlacoes
from .evidencias import (
    evidenciar_status_http,
    evidenciar_tls,
    ordenar_evidencias,
)
from .inventario_superficie import (
    construir_inventario,
)
from .analisador_portas import analisar_portas

from .modelos import OnlineResultado


def _host_do_alvo(alvo: str) -> str:
    """Obtém somente o hostname do alvo."""
    from urllib.parse import urlparse

    parsed = urlparse(alvo)

    if parsed.hostname:
        return parsed.hostname

    return ""


def analisar_online(
    alvo: str,
    timeout: float = 10.0,
    analisar_certificado: bool = True,
    portas: list[int] | None = None,
) -> OnlineResultado:
    resultado = OnlineResultado(alvo=alvo)

    # ---------------------------------------------------------
    # 1. COLETA HTTP
    # ---------------------------------------------------------
    coleta = coletar(
        alvo,
        timeout=timeout,
    )

    resultado.sucesso = coleta.sucesso
    resultado.respostas = list(coleta.respostas)
    resultado.cookies = list(coleta.cookies)
    resultado.erros.extend(coleta.erros)

    # ---------------------------------------------------------
    # 2. ANÁLISE DAS RESPOSTAS HTTP
    # ---------------------------------------------------------
    for resposta in resultado.respostas:
        analise = analisar_resposta(resposta)

        status = analise.get("status_code")

        if status is not None:
            resultado.evidencias.append(
                evidenciar_status_http(status)
            )

            resultado.observacoes.append(
                f"Resposta HTTP observada: {status}."
            )

        html = analise.get("html", {})

        if html.get("detectado"):
            resultado.observacoes.append(
                "Conteúdo HTML identificado."
            )

        json_info = analise.get("json", {})

        if json_info.get("detectado"):
            resultado.observacoes.append(
                "Conteúdo JSON identificado."
            )

    # ---------------------------------------------------------
    # 3. ANÁLISE TLS
    # ---------------------------------------------------------
    tls_resultado = analisar_tls(
        alvo,
        timeout=timeout,
    )

    if tls_resultado.get("sucesso"):
        resultado.tls = tls_resultado

        if analisar_certificado:
            resultado.evidencias.extend(
                evidenciar_tls(tls_resultado)
            )

        resultado.observacoes.append(
            "Negociação TLS observada."
        )

    elif tls_resultado.get("detectado"):
        resultado.erros.append(
            tls_resultado.get(
                "erro",
                "Falha na análise TLS.",
            )
        )

    # ---------------------------------------------------------
    # 4. IDENTIFICAÇÃO DE SERVIDORES
    # ---------------------------------------------------------
    for resposta in resultado.respostas:
        servidores = analisar_servidor(resposta)

        if servidores:
            resultado.servidores.extend(servidores)

    # ---------------------------------------------------------
    # 5. SERVIÇOS OBSERVADOS
    # ---------------------------------------------------------
    #
    # O serviço HTTP/HTTPS é derivado apenas das informações
    # que já foram observadas pela coleta.
    #
    # Não existe varredura ampla de portas aqui.
    #
    from .servicos import (
        consolidar_servicos,
        observar_http,
        observar_tls,
    )

    servicos = []

    for resposta in resultado.respostas:
        servicos.append(
            observar_http(resposta)
        )

    if resultado.tls is not None:
        servico_tls = observar_tls(
            alvo,
            resultado.tls,
        )

        if servico_tls is not None:
            servicos.append(servico_tls)

    resultado.servicos = consolidar_servicos(servicos)

    # ---------------------------------------------------------
    # 6. ANÁLISE DE PORTAS
    # ---------------------------------------------------------
    #
    # Somente portas explicitamente fornecidas pelo chamador
    # são verificadas.
    #
    if portas:
        host = _host_do_alvo(alvo)

        if host:
            resultado.metadados["portas_verificadas"] = analisar_portas(
                host=host,
                portas=portas,
                timeout=timeout,
            )

    # ---------------------------------------------------------
    # 7. CORRELAÇÃO DE EVIDÊNCIAS
    # ---------------------------------------------------------
    resultado.evidencias = ordenar_evidencias(
        resultado.evidencias
    )

    correlacoes = ordenar_correlacoes(
        correlacionar(resultado.evidencias)
    )

    # As correlações são mantidas no metadado para não quebrar
    # a estrutura existente do OnlineResultado.
    resultado.metadados["correlacoes"] = correlacoes

    # ---------------------------------------------------------
    # 8. INVENTÁRIO DE SUPERFÍCIE
    # ---------------------------------------------------------
    inventario = construir_inventario(
        alvo=alvo,
        portas=resultado.metadados.get("portas_verificadas", []),
        servicos=resultado.servicos,
        servidores=resultado.servidores,
        evidencias=resultado.evidencias,
        observacoes=resultado.observacoes,
    )

    resultado.metadados["inventario_superficie"] = inventario

    return resultado


def _porta_da_url(url: str) -> int | None:
    """
    Obtém a porta efetivamente indicada na URL.

    Se a URL não especificar uma porta:
      HTTP  -> 80
      HTTPS -> 443

    Não realiza nenhuma conexão de rede.
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)

        if parsed.port:
            return parsed.port

        if parsed.scheme.lower() == "https":
            return 443

        if parsed.scheme.lower() == "http":
            return 80

    except ValueError:
        return None

    return None
