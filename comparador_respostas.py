#!/usr/bin/env python3

"""
COMPARADOR UNIVERSAL DE RESPOSTAS HTTP

Analisa e compara duas respostas HTTP salvas em arquivos.

Recursos:
- Status HTTP
- Versão HTTP
- Headers
- Cookies
- Corpo da resposta
- JSON
- success
- message
- URL Encoding
- Campos JSON adicionados/removidos
- Valores JSON alterados
- Relatório JSON
- Evita interpretar o corpo JSON como header
- Não exibe valores completos de cookies/sessões
"""

import json
import re
import sys


# ============================================================
# CONFIGURAÇÃO
# ============================================================

CAMPOS_SENSIVEIS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "password",
    "senha",
    "secret",
    "api_key",
    "apikey",
    "session",
    "session_id",
}


# ============================================================
# MÁSCARA DE DADOS SENSÍVEIS
# ============================================================

def mascarar_valor(valor, nome_campo=""):

    nome = str(nome_campo).lower().strip()

    if nome in CAMPOS_SENSIVEIS:

        if valor is None:
            return None

        texto = str(valor)

        if len(texto) <= 8:
            return "[REDACTED]"

        return (
            texto[:4]
            + "..."
            + texto[-4:]
            + " [REDACTED]"
        )

    return valor


# ============================================================
# CLASSIFICAÇÃO HTTP
# ============================================================

def classificar_status(codigo):

    if codigo is None:
        return "STATUS DESCONHECIDO"

    if 200 <= codigo < 300:
        return "SUCESSO"

    if 300 <= codigo < 400:
        return "REDIRECIONAMENTO"

    if codigo == 400:
        return "REQUISIÇÃO INVÁLIDA"

    if codigo == 401:
        return "NÃO AUTENTICADO"

    if codigo == 403:
        return "ACESSO NEGADO"

    if codigo == 404:
        return "NÃO ENCONTRADO"

    if codigo == 408:
        return "TIMEOUT"

    if codigo == 409:
        return "CONFLITO"

    if codigo == 429:
        return "LIMITE DE REQUISIÇÕES"

    if 400 <= codigo < 500:
        return "FALHA NA REQUISIÇÃO"

    if 500 <= codigo < 600:
        return "ERRO DO SERVIDOR"

    return "DESCONHECIDO"


# ============================================================
# SEPARAR CABEÇALHOS DO CORPO
# ============================================================

def separar_resposta(texto):

    """
    Divide a resposta em:

        cabeçalho HTTP
        corpo

    A primeira linha vazia marca o início do corpo.

    Isso é importante porque JSON pode conter ":" e ";"
    e não deve ser interpretado como header.
    """

    partes = re.split(
        r"\r?\n\r?\n",
        texto,
        maxsplit=1
    )

    if len(partes) == 2:

        cabecalho = partes[0].strip()

        corpo = partes[1].strip()

    else:

        cabecalho = texto.strip()

        corpo = ""

    return cabecalho, corpo


# ============================================================
# EXTRAIR STATUS HTTP
# ============================================================

def extrair_status(texto):

    primeira_linha = ""

    for linha in texto.splitlines():

        linha = linha.strip()

        if linha:

            primeira_linha = linha

            break

    padrao = re.match(
        r"^HTTP/(\d+(?:\.\d+)?)\s+(\d{3})(?:\s+(.*))?$",
        primeira_linha,
        re.IGNORECASE
    )

    if not padrao:

        return {
            "versao": None,
            "codigo": None,
            "descricao": None
        }

    return {
        "versao": padrao.group(1),
        "codigo": int(padrao.group(2)),
        "descricao": (
            padrao.group(3).strip()
            if padrao.group(3)
            else ""
        )
    }


# ============================================================
# EXTRAIR HEADERS
# ============================================================

def extrair_headers(cabecalho):

    """
    Analisa SOMENTE a parte de headers.

    Nunca analisa o corpo JSON.
    """

    headers = []

    linhas = cabecalho.splitlines()

    for indice, linha in enumerate(linhas):

        linha = linha.strip()

        if not linha:
            continue

        # Ignorar linha HTTP/2 200 OK
        if re.match(
            r"^HTTP/\d",
            linha,
            re.IGNORECASE
        ):
            continue

        # Header HTTP precisa ter nome antes dos dois pontos.
        if ":" not in linha:
            continue

        nome, valor = linha.split(":", 1)

        nome = nome.strip()

        valor = valor.strip()

        # Evita interpretar coisas estranhas como header.
        if not re.match(
            r"^[A-Za-z0-9!#$%&'*+\-.^_`|~]+$",
            nome
        ):
            continue

        headers.append({
            "nome": nome,
            "valor": valor
        })

    return headers


# ============================================================
# HEADERS -> DICIONÁRIO
# ============================================================

def headers_para_dict(headers):

    resultado = {}

    for header in headers:

        nome = header["nome"].lower()

        valor = header["valor"]

        if nome not in resultado:

            resultado[nome] = valor

        else:

            if not isinstance(
                resultado[nome],
                list
            ):

                resultado[nome] = [
                    resultado[nome]
                ]

            resultado[nome].append(valor)

    return resultado


# ============================================================
# EXTRAIR COOKIES
# ============================================================

def extrair_cookies(headers):

    cookies = []

    for header in headers:

        if header["nome"].lower() != "set-cookie":
            continue

        valor = header["valor"]

        primeira_parte = valor.split(
            ";",
            1
        )[0]

        if "=" not in primeira_parte:
            continue

        nome, conteudo = primeira_parte.split(
            "=",
            1
        )

        cookies.append({
            "nome": nome.strip(),
            "valor": conteudo.strip()
        })

    return cookies


# ============================================================
# DETECTAR JSON
# ============================================================

def analisar_json(corpo):

    if not corpo:
        return None

    try:

        return json.loads(corpo)

    except json.JSONDecodeError:

        return None


# ============================================================
# DETECTAR URL ENCODING
# ============================================================

def detectar_url_encoding(texto):

    encontrados = re.findall(
        r"%[0-9A-Fa-f]{2}",
        texto
    )

    return {
        "detectado": bool(encontrados),
        "quantidade": len(encontrados),
        "exemplos": encontrados[:20]
    }


# ============================================================
# EXTRAIR SUCCESS
# ============================================================

def extrair_success(dados):

    if not isinstance(dados, dict):
        return None

    if "success" in dados:

        return dados["success"]

    return None


# ============================================================
# EXTRAIR MENSAGEM
# ============================================================

def extrair_mensagem(dados):

    if not isinstance(dados, dict):
        return None

    campos = [
        "message",
        "mensagem",
        "error",
        "erro",
        "detail",
        "description"
    ]

    for campo in campos:

        if campo in dados:

            return dados[campo]

    return None


# ============================================================
# ANALISAR RESPOSTA
# ============================================================

def analisar_resposta(texto):

    cabecalho, corpo = separar_resposta(
        texto
    )

    status = extrair_status(
        cabecalho
    )

    headers = extrair_headers(
        cabecalho
    )

    cookies = extrair_cookies(
        headers
    )

    dados_json = analisar_json(
        corpo
    )

    success = extrair_success(
        dados_json
    )

    mensagem = extrair_mensagem(
        dados_json
    )

    url_encoding = detectar_url_encoding(
        texto
    )

    classificacao = classificar_status(
        status["codigo"]
    )

    # JSON pode determinar sucesso/falha
    if success is False:

        classificacao = "FALHA"

    elif (
        success is True
        and status["codigo"] is not None
        and 200 <= status["codigo"] < 300
    ):

        classificacao = "SUCESSO"

    return {
        "http": status,
        "classificacao": classificacao,
        "headers": headers,
        "cookies": cookies,
        "corpo": corpo,
        "json": dados_json,
        "success": success,
        "mensagem": mensagem,
        "url_encoding": url_encoding
    }


# ============================================================
# COMPARAÇÃO RECURSIVA DE JSON
# ============================================================

def comparar_json(
    valor1,
    valor2,
    caminho="",
    diferencas=None
):

    if diferencas is None:

        diferencas = []

    # --------------------------------------------------------
    # DICIONÁRIOS
    # --------------------------------------------------------

    if isinstance(valor1, dict) and isinstance(valor2, dict):

        chaves1 = set(valor1.keys())

        chaves2 = set(valor2.keys())

        somente1 = chaves1 - chaves2

        somente2 = chaves2 - chaves1

        comuns = chaves1 & chaves2

        # Campos removidos
        for chave in sorted(
            somente1,
            key=str
        ):

            campo = (
                f"{caminho}.{chave}"
                if caminho
                else str(chave)
            )

            diferencas.append({
                "tipo": "campo_removido",
                "campo": campo,
                "valor_1": mascarar_valor(
                    valor1[chave],
                    str(chave)
                ),
                "valor_2": None
            })

        # Campos adicionados
        for chave in sorted(
            somente2,
            key=str
        ):

            campo = (
                f"{caminho}.{chave}"
                if caminho
                else str(chave)
            )

            diferencas.append({
                "tipo": "campo_adicionado",
                "campo": campo,
                "valor_1": None,
                "valor_2": mascarar_valor(
                    valor2[chave],
                    str(chave)
                )
            })

        # Campos comuns
        for chave in sorted(
            comuns,
            key=str
        ):

            campo = (
                f"{caminho}.{chave}"
                if caminho
                else str(chave)
            )

            comparar_json(
                valor1[chave],
                valor2[chave],
                campo,
                diferencas
            )

        return diferencas

    # --------------------------------------------------------
    # LISTAS
    # --------------------------------------------------------

    if isinstance(valor1, list) and isinstance(valor2, list):

        tamanho1 = len(valor1)

        tamanho2 = len(valor2)

        tamanho = max(
            tamanho1,
            tamanho2
        )

        for indice in range(tamanho):

            campo = (
                f"{caminho}[{indice}]"
                if caminho
                else f"[{indice}]"
            )

            if indice >= tamanho1:

                diferencas.append({
                    "tipo": "item_adicionado",
                    "campo": campo,
                    "valor_1": None,
                    "valor_2": valor2[indice]
                })

                continue

            if indice >= tamanho2:

                diferencas.append({
                    "tipo": "item_removido",
                    "campo": campo,
                    "valor_1": valor1[indice],
                    "valor_2": None
                })

                continue

            comparar_json(
                valor1[indice],
                valor2[indice],
                campo,
                diferencas
            )

        return diferencas

    # --------------------------------------------------------
    # VALORES SIMPLES
    # --------------------------------------------------------

    if valor1 != valor2:

        nome_campo = (
            caminho.split(".")[-1]
            if caminho
            else "valor"
        )

        diferencas.append({
            "tipo": "valor_alterado",
            "campo": caminho or "valor",
            "valor_1": mascarar_valor(
                valor1,
                nome_campo
            ),
            "valor_2": mascarar_valor(
                valor2,
                nome_campo
            )
        })

    return diferencas


# ============================================================
# COMPARAR HEADERS
# ============================================================

def comparar_headers(
    headers1,
    headers2
):

    diferencas = []

    dict1 = headers_para_dict(
        headers1
    )

    dict2 = headers_para_dict(
        headers2
    )

    nomes1 = set(dict1.keys())

    nomes2 = set(dict2.keys())

    # Headers removidos
    for nome in sorted(nomes1):

        if nome not in nomes2:

            diferencas.append({
                "tipo": "header_removido",
                "campo": nome,
                "valor_1": mascarar_valor(
                    dict1[nome],
                    nome
                ),
                "valor_2": None
            })

    # Headers adicionados
    for nome in sorted(nomes2):

        if nome not in nomes1:

            diferencas.append({
                "tipo": "header_adicionado",
                "campo": nome,
                "valor_1": None,
                "valor_2": mascarar_valor(
                    dict2[nome],
                    nome
                )
            })

    # Headers alterados
    for nome in sorted(
        nomes1 & nomes2
    ):

        valor1 = dict1[nome]

        valor2 = dict2[nome]

        if valor1 != valor2:

            # Não compara valor de cookies/sessões
            # diretamente para evitar exposição.
            if nome in {
                "set-cookie",
                "cookie",
                "authorization"
            }:

                diferencas.append({
                    "tipo": "header_sensivel_alterado",
                    "campo": nome,
                    "valor_1": "[REDACTED]",
                    "valor_2": "[REDACTED]"
                })

            else:

                diferencas.append({
                    "tipo": "header_alterado",
                    "campo": nome,
                    "valor_1": valor1,
                    "valor_2": valor2
                })

    return diferencas


# ============================================================
# COMPARAR COOKIES
# ============================================================

def comparar_cookies(
    cookies1,
    cookies2
):

    diferencas = []

    dict1 = {
        cookie["nome"]: cookie["valor"]
        for cookie in cookies1
    }

    dict2 = {
        cookie["nome"]: cookie["valor"]
        for cookie in cookies2
    }

    nomes1 = set(dict1.keys())

    nomes2 = set(dict2.keys())

    # Cookie removido
    for nome in sorted(nomes1):

        if nome not in nomes2:

            diferencas.append({
                "tipo": "cookie_removido",
                "campo": nome,
                "valor_1": "[REDACTED]",
                "valor_2": None
            })

    # Cookie adicionado
    for nome in sorted(nomes2):

        if nome not in nomes1:

            diferencas.append({
                "tipo": "cookie_adicionado",
                "campo": nome,
                "valor_1": None,
                "valor_2": "[REDACTED]"
            })

    # Cookie alterado
    for nome in sorted(
        nomes1 & nomes2
    ):

        if dict1[nome] != dict2[nome]:

            diferencas.append({
                "tipo": "cookie_alterado",
                "campo": nome,
                "valor_1": "[REDACTED]",
                "valor_2": "[REDACTED]"
            })

    return diferencas


# ============================================================
# COMPARAR DUAS RESPOSTAS
# ============================================================

def comparar_respostas(
    primeira,
    segunda
):

    diferencas = []

    # --------------------------------------------------------
    # STATUS HTTP
    # --------------------------------------------------------

    if (
        primeira["http"]["codigo"]
        != segunda["http"]["codigo"]
    ):

        diferencas.append({
            "tipo": "codigo_http_alterado",
            "campo": "HTTP",
            "valor_1": primeira["http"]["codigo"],
            "valor_2": segunda["http"]["codigo"]
        })

    # --------------------------------------------------------
    # VERSÃO HTTP
    # --------------------------------------------------------

    if (
        primeira["http"]["versao"]
        != segunda["http"]["versao"]
    ):

        diferencas.append({
            "tipo": "versao_http_alterada",
            "campo": "HTTP.version",
            "valor_1": primeira["http"]["versao"],
            "valor_2": segunda["http"]["versao"]
        })

    # --------------------------------------------------------
    # DESCRIÇÃO
    # --------------------------------------------------------

    if (
        primeira["http"]["descricao"]
        != segunda["http"]["descricao"]
    ):

        diferencas.append({
            "tipo": "descricao_http_alterada",
            "campo": "HTTP.description",
            "valor_1": primeira["http"]["descricao"],
            "valor_2": segunda["http"]["descricao"]
        })

    # --------------------------------------------------------
    # CLASSIFICAÇÃO
    # --------------------------------------------------------

    if (
        primeira["classificacao"]
        != segunda["classificacao"]
    ):

        diferencas.append({
            "tipo": "classificacao_alterada",
            "campo": "classificacao",
            "valor_1": primeira["classificacao"],
            "valor_2": segunda["classificacao"]
        })

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if (
        primeira["success"]
        != segunda["success"]
    ):

        diferencas.append({
            "tipo": "success_alterado",
            "campo": "success",
            "valor_1": primeira["success"],
            "valor_2": segunda["success"]
        })

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    if (
        primeira["mensagem"]
        != segunda["mensagem"]
    ):

        diferencas.append({
            "tipo": "mensagem_alterada",
            "campo": "message",
            "valor_1": primeira["mensagem"],
            "valor_2": segunda["mensagem"]
        })

    # --------------------------------------------------------
    # JSON
    #
    # success e message já foram comparados acima.
    # Portanto são removidos temporariamente para evitar
    # duplicação.
    # --------------------------------------------------------

    json1 = primeira["json"]

    json2 = segunda["json"]

    if (
        isinstance(json1, dict)
        and isinstance(json2, dict)
    ):

        json1_comparacao = dict(json1)

        json2_comparacao = dict(json2)

        for campo in (
            "success",
            "message",
            "mensagem"
        ):

            json1_comparacao.pop(
                campo,
                None
            )

            json2_comparacao.pop(
                campo,
                None
            )

        diferencas.extend(
            comparar_json(
                json1_comparacao,
                json2_comparacao
            )
        )

    elif json1 != json2:

        diferencas.append({
            "tipo": "estrutura_json_alterada",
            "campo": "JSON",
            "valor_1": "[JSON diferente]",
            "valor_2": "[JSON diferente]"
        })

    # --------------------------------------------------------
    # HEADERS
    # --------------------------------------------------------

    diferencas.extend(
        comparar_headers(
            primeira["headers"],
            segunda["headers"]
        )
    )

    # --------------------------------------------------------
    # COOKIES
    # --------------------------------------------------------

    diferencas.extend(
        comparar_cookies(
            primeira["cookies"],
            segunda["cookies"]
        )
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return {
        "iguais": len(diferencas) == 0,
        "quantidade_diferencas": len(diferencas),
        "diferencas": diferencas
    }


# ============================================================
# IMPRIMIR RESUMO
# ============================================================

def imprimir_resumo(
    nome,
    resultado
):

    print("\n" + "=" * 70)

    print(nome)

    print("=" * 70)

    http = resultado["http"]

    versao = http["versao"] or "?"

    codigo = (
        str(http["codigo"])
        if http["codigo"] is not None
        else "?"
    )

    descricao = (
        http["descricao"]
        or ""
    )

    print(
        f"\nHTTP/{versao} "
        f"{codigo} "
        f"{descricao}"
    )

    print(
        f"Classificação: "
        f"{resultado['classificacao']}"
    )

    print(
        f"success: "
        f"{resultado['success']}"
    )

    print(
        f"Mensagem: "
        f"{resultado['mensagem']}"
    )

    print(
        f"Headers encontrados: "
        f"{len(resultado['headers'])}"
    )

    print(
        f"Cookies encontrados: "
        f"{len(resultado['cookies'])}"
    )

    if resultado["json"] is not None:

        print("JSON: detectado")

    else:

        print("JSON: não detectado")

    if resultado["url_encoding"]["detectado"]:

        print(
            "URL Encoding: detectado "
            f"({resultado['url_encoding']['quantidade']} ocorrências)"
        )

    else:

        print(
            "URL Encoding: não detectado"
        )


# ============================================================
# IMPRIMIR COMPARAÇÃO
# ============================================================

def imprimir_comparacao(
    comparacao
):

    print("\n" + "=" * 70)

    print("DIFERENÇAS SIGNIFICATIVAS")

    print("=" * 70)

    if comparacao["iguais"]:

        print(
            "\nNenhuma diferença encontrada."
        )

        return

    print(
        f"\nTotal de diferenças: "
        f"{comparacao['quantidade_diferencas']}"
    )

    for diferenca in comparacao["diferencas"]:

        print(
            f"\n[{diferenca['tipo']}]"
        )

        print(
            f"Campo: "
            f"{diferenca['campo']}"
        )

        print(
            f"  Resposta 1: "
            f"{diferenca['valor_1']}"
        )

        print(
            f"  Resposta 2: "
            f"{diferenca['valor_2']}"
        )


# ============================================================
# GERAR RELATÓRIO
# ============================================================

def gerar_relatorio(
    arquivo1,
    arquivo2,
    resposta1,
    resposta2,
    comparacao
):

    return {
        "arquivo_1": arquivo1,
        "arquivo_2": arquivo2,

        "resposta_1": {
            "http": resposta1["http"],
            "classificacao": resposta1[
                "classificacao"
            ],
            "success": resposta1[
                "success"
            ],
            "mensagem": resposta1[
                "mensagem"
            ],
            "quantidade_headers": len(
                resposta1["headers"]
            ),
            "quantidade_cookies": len(
                resposta1["cookies"]
            ),
            "json_detectado": (
                resposta1["json"]
                is not None
            ),
            "url_encoding": resposta1[
                "url_encoding"
            ]
        },

        "resposta_2": {
            "http": resposta2["http"],
            "classificacao": resposta2[
                "classificacao"
            ],
            "success": resposta2[
                "success"
            ],
            "mensagem": resposta2[
                "mensagem"
            ],
            "quantidade_headers": len(
                resposta2["headers"]
            ),
            "quantidade_cookies": len(
                resposta2["cookies"]
            ),
            "json_detectado": (
                resposta2["json"]
                is not None
            ),
            "url_encoding": resposta2[
                "url_encoding"
            ]
        },

        "comparacao": comparacao
    }


# ============================================================
# EXECUTAR COM ARQUIVOS
# ============================================================

def executar(
    arquivo1,
    arquivo2
):

    try:

        with open(
            arquivo1,
            "r",
            encoding="utf-8"
        ) as arquivo:

            texto1 = arquivo.read()

        with open(
            arquivo2,
            "r",
            encoding="utf-8"
        ) as arquivo:

            texto2 = arquivo.read()

    except OSError as erro:

        print(
            f"\nErro ao abrir arquivos: {erro}"
        )

        return 1

    resposta1 = analisar_resposta(
        texto1
    )

    resposta2 = analisar_resposta(
        texto2
    )

    imprimir_resumo(
        "RESPOSTA 1",
        resposta1
    )

    imprimir_resumo(
        "RESPOSTA 2",
        resposta2
    )

    comparacao = comparar_respostas(
        resposta1,
        resposta2
    )

    imprimir_comparacao(
        comparacao
    )

    relatorio = gerar_relatorio(
        arquivo1,
        arquivo2,
        resposta1,
        resposta2,
        comparacao
    )

    print("\n" + "=" * 70)

    print("JSON DA COMPARAÇÃO")

    print("=" * 70)

    print(
        json.dumps(
            relatorio,
            indent=4,
            ensure_ascii=False
        )
    )

    nome_relatorio = (
        "relatorio_comparacao.json"
    )

    try:

        with open(
            nome_relatorio,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                relatorio,
                arquivo,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"\nRelatório salvo em: "
            f"{nome_relatorio}"
        )

    except OSError as erro:

        print(
            f"\nAviso: erro ao salvar "
            f"relatório: {erro}"
        )

    return 0


# ============================================================
# AJUDA
# ============================================================

def mostrar_ajuda():

    print("\n" + "=" * 70)

    print(
        "COMPARADOR UNIVERSAL DE RESPOSTAS HTTP"
    )

    print("=" * 70)

    print(
        "\nUso:"
    )

    print(
        "python3 comparador_respostas.py "
        "arquivo1.txt arquivo2.txt"
    )

    print(
        "\nExemplo:"
    )

    print(
        "python3 comparador_respostas.py "
        "exemplos/resposta1.txt "
        "exemplos/resposta2.txt"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 3:

        mostrar_ajuda()

        return 1

    arquivo1 = sys.argv[1]

    arquivo2 = sys.argv[2]

    return executar(
        arquivo1,
        arquivo2
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
