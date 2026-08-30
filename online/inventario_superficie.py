from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .modelos import Evidencia, ServidorObservado, ServicoObservado


ESTADOS_PORTA = {
    "aberta",
    "fechada",
    "filtrada",
    "inferida",
    "nao_verificada",
}


@dataclass
class PortaObservada:
    porta: int
    transporte: str = "TCP"
    estado: str = "nao_verificada"
    servico: str = ""
    protocolo: str = ""
    origem: str = ""
    confianca: str = "BAIXA"
    detalhes: dict[str, Any] = field(default_factory=dict)


@dataclass
class InventarioSuperficie:
    alvo: str
    portas: list[PortaObservada] = field(default_factory=list)
    servicos: list[ServicoObservado] = field(default_factory=list)
    servidores: list[ServidorObservado] = field(default_factory=list)
    evidencias: list[Evidencia] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)
    metadados: dict[str, Any] = field(default_factory=dict)


def _normalizar_estado(estado: str) -> str:
    estado = (estado or "").strip().lower()

    if estado in ESTADOS_PORTA:
        return estado

    if estado == "observado":
        return "aberta"

    return "nao_verificada"


def _prioridade_confianca(valor: str) -> int:
    return {
        "BAIXA": 1,
        "MEDIA": 2,
        "ALTA": 3,
    }.get((valor or "").upper(), 0)


def _converter_servico_para_porta(
    servico: ServicoObservado,
) -> PortaObservada:
    return PortaObservada(
        porta=servico.porta,
        transporte=servico.transporte,
        estado=_normalizar_estado(servico.estado),
        servico=servico.servico,
        protocolo=servico.protocolo,
        origem=servico.origem,
        confianca=servico.confianca,
        detalhes=dict(servico.detalhes),
    )


def _mesclar_portas(
    portas: list[PortaObservada],
) -> list[PortaObservada]:
    """
    Consolida registros da mesma porta/transporte.

    Quando existem várias observações, mantém a informação
    com maior confiança e preserva as fontes adicionais.
    """

    agrupadas: dict[tuple[int, str], PortaObservada] = {}

    for porta in portas:
        chave = (
            porta.porta,
            porta.transporte.upper(),
        )

        atual = agrupadas.get(chave)

        if atual is None:
            agrupadas[chave] = porta
            continue

        if _prioridade_confianca(porta.confianca) > _prioridade_confianca(
            atual.confianca
        ):
            principal = porta
            secundario = atual
        else:
            principal = atual
            secundario = porta

        fontes = list(
            principal.detalhes.get("fontes_adicionais", [])
        )

        if secundario.origem:
            fontes.append(secundario.origem)

        principal.detalhes["fontes_adicionais"] = sorted(
            set(fontes)
        )

        if not principal.servico and secundario.servico:
            principal.servico = secundario.servico

        if not principal.protocolo and secundario.protocolo:
            principal.protocolo = secundario.protocolo

        agrupadas[chave] = principal

    return sorted(
        agrupadas.values(),
        key=lambda item: (
            item.porta,
            item.transporte,
        ),
    )


def construir_inventario(
    alvo: str,
    portas: list[PortaObservada] | None = None,
    servicos: list[ServicoObservado] | None = None,
    servidores: list[ServidorObservado] | None = None,
    evidencias: list[Evidencia] | None = None,
    observacoes: list[str] | None = None,
) -> InventarioSuperficie:
    """
    Constrói uma visão consolidada da superfície observada.

    Este módulo não realiza conexões de rede.
    Ele apenas organiza e correlaciona informações
    já coletadas pelos outros analisadores.
    """

    portas = list(portas or [])
    servicos = servicos or []
    servidores = servidores or []
    evidencias = evidencias or []
    observacoes = observacoes or []

    portas.extend(
        _converter_servico_para_porta(servico)
        for servico in servicos
    )

    # Um servidor observado também confirma contexto
    # para a porta correspondente.
    for servidor in servidores:
        if servidor.porta <= 0:
            continue

        portas.append(
            PortaObservada(
                porta=servidor.porta,
                transporte="TCP",
                estado="aberta",
                servico=servidor.produto,
                protocolo=servidor.protocolo,
                origem=servidor.origem,
                confianca=servidor.confianca,
                detalhes={
                    "produto": servidor.produto,
                    "versao": servidor.versao,
                    "familia": servidor.familia,
                },
            )
        )

    portas = _mesclar_portas(portas)

    return InventarioSuperficie(
        alvo=alvo,
        portas=portas,
        servicos=list(servicos),
        servidores=list(servidores),
        evidencias=list(evidencias),
        observacoes=list(observacoes),
    )


def resumir_inventario(
    inventario: InventarioSuperficie,
) -> dict[str, Any]:
    abertas = [
        porta for porta in inventario.portas
        if porta.estado == "aberta"
    ]

    fechadas = [
        porta for porta in inventario.portas
        if porta.estado == "fechada"
    ]

    filtradas = [
        porta for porta in inventario.portas
        if porta.estado == "filtrada"
    ]

    inferidas = [
        porta for porta in inventario.portas
        if porta.estado == "inferida"
    ]

    nao_verificadas = [
        porta for porta in inventario.portas
        if porta.estado == "nao_verificada"
    ]

    return {
        "alvo": inventario.alvo,
        "total_portas": len(inventario.portas),
        "portas_abertas": len(abertas),
        "portas_fechadas": len(fechadas),
        "portas_filtradas": len(filtradas),
        "portas_inferidas": len(inferidas),
        "portas_nao_verificadas": len(nao_verificadas),
        "servicos": len(inventario.servicos),
        "servidores": len(inventario.servidores),
        "evidencias": len(inventario.evidencias),
    }


def serializar_inventario(
    inventario: InventarioSuperficie,
) -> dict[str, Any]:
    return {
        "alvo": inventario.alvo,
        "portas": [
            asdict(porta)
            for porta in inventario.portas
        ],
        "servicos": [
            asdict(servico)
            for servico in inventario.servicos
        ],
        "servidores": [
            asdict(servidor)
            for servidor in inventario.servidores
        ],
        "evidencias": [
            asdict(evidencia)
            for evidencia in inventario.evidencias
        ],
        "observacoes": list(inventario.observacoes),
        "metadados": dict(inventario.metadados),
        "resumo": resumir_inventario(inventario),
    }
