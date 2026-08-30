from __future__ import annotations

import socket

from .inventario_superficie import PortaObservada
from .servicos import inferir_servico


def analisar_porta(
    host: str,
    porta: int,
    timeout: float = 2.0,
    transporte: str = "TCP",
) -> PortaObservada:
    """
    Verifica uma porta TCP específica e classifica o resultado.

    Estados:
      - aberta: conexão TCP estabelecida
      - fechada: conexão recusada
      - filtrada: timeout ou bloqueio sem resposta conclusiva
    """

    transporte = transporte.upper()

    servico = inferir_servico(
        porta,
        transporte=transporte,
    )

    resultado = PortaObservada(
        porta=porta,
        transporte=transporte,
        estado="nao_verificada",
        servico=servico.servico,
        protocolo=servico.protocolo,
        origem="verificacao_tcp",
        confianca="BAIXA",
    )

    if porta < 1 or porta > 65535:
        resultado.detalhes["erro"] = "Porta fora do intervalo válido."
        return resultado

    try:
        with socket.create_connection(
            (host, porta),
            timeout=timeout,
        ):
            resultado.estado = "aberta"
            resultado.confianca = "ALTA"
            resultado.detalhes["metodo"] = "conexao_tcp"

    except ConnectionRefusedError:
        resultado.estado = "fechada"
        resultado.confianca = "ALTA"
        resultado.detalhes["metodo"] = "recusa_tcp"

    except TimeoutError:
        resultado.estado = "filtrada"
        resultado.confianca = "MEDIA"
        resultado.detalhes["metodo"] = "timeout"

    except socket.timeout:
        resultado.estado = "filtrada"
        resultado.confianca = "MEDIA"
        resultado.detalhes["metodo"] = "timeout"

    except OSError as erro:
        resultado.estado = "filtrada"
        resultado.confianca = "BAIXA"
        resultado.detalhes["metodo"] = "erro_socket"
        resultado.detalhes["erro"] = str(erro)

    return resultado


def analisar_portas(
    host: str,
    portas: list[int],
    timeout: float = 2.0,
    transporte: str = "TCP",
) -> list[PortaObservada]:
    """
    Analisa somente as portas explicitamente fornecidas.
    """

    resultados = []

    for porta in portas:
        resultados.append(
            analisar_porta(
                host=host,
                porta=porta,
                timeout=timeout,
                transporte=transporte,
            )
        )

    return sorted(
        resultados,
        key=lambda item: (
            item.porta,
            item.transporte,
        ),
    )
