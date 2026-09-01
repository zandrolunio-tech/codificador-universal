#!/usr/bin/env python3

import base64
import binascii
import json
import re
from dataclasses import asdict
from urllib.parse import unquote

from online.inventario_superficie import serializar_inventario
from online.orquestrador import analisar_online



# ============================================================
# CODIFICAÇÃO
# ============================================================

def codificar(texto):
    dados = texto.encode("utf-8")

    return {
        "original": texto,
        "tamanho_caracteres": len(texto),
        "tamanho_bytes": len(dados),
        "hexadecimal": dados.hex(),
        "binario": " ".join(format(byte, "08b") for byte in dados),
        "octal": " ".join(format(byte, "03o") for byte in dados),
        "decimal": " ".join(str(byte) for byte in dados),
        "base64": base64.b64encode(dados).decode("ascii"),
    }


# ============================================================
# DESCODIFICAÇÃO
# ============================================================

def decodificar_hexadecimal(valor):
    try:
        valor = unquote(valor.strip())
        valor = valor.replace(" ", "")

        if not valor or len(valor) % 2 != 0:
            return None

        if not re.fullmatch(r"[0-9a-fA-F]+", valor):
            return None

        return bytes.fromhex(valor).decode("utf-8")

    except (ValueError, UnicodeDecodeError):
        return None


def decodificar_binario(valor):
    try:
        valor = unquote(valor.strip())
        partes = valor.split()

        if not partes:
            return None

        if any(
            len(parte) != 8
            or not re.fullmatch(r"[01]{8}", parte)
            for parte in partes
        ):
            return None

        dados = bytes(int(parte, 2) for parte in partes)

        return dados.decode("utf-8")

    except (ValueError, UnicodeDecodeError):
        return None


def decodificar_octal(valor):
    try:
        valor = unquote(valor.strip())
        partes = valor.split()

        if not partes:
            return None

        numeros = [int(parte, 8) for parte in partes]

        if any(numero < 0 or numero > 255 for numero in numeros):
            return None

        return bytes(numeros).decode("utf-8")

    except (ValueError, UnicodeDecodeError):
        return None


def decodificar_decimal(valor):
    try:
        valor = unquote(valor.strip())
        partes = valor.split()

        if not partes:
            return None

        numeros = [int(parte) for parte in partes]

        if any(numero < 0 or numero > 255 for numero in numeros):
            return None

        return bytes(numeros).decode("utf-8")

    except (ValueError, UnicodeDecodeError):
        return None


def decodificar_base64(valor):
    try:
        valor = valor.strip()

        if not valor:
            return None

        valor = unquote(valor)
        valor = "".join(valor.split())

        dados = base64.b64decode(
            valor,
            validate=True
        )

        return dados.decode("utf-8")

    except (
        ValueError,
        UnicodeDecodeError,
        binascii.Error
    ):
        return None


# ============================================================
# DETECÇÃO DE FORMATOS
# ============================================================

def detectar_formatos(valor):
    resultados = []

    valor = valor.strip()

    if not valor:
        return resultados

    resultado_base64 = decodificar_base64(valor)

    if resultado_base64 is not None:
        resultados.append({
            "formato": "Base64",
            "resultado": resultado_base64
        })

    resultado_hex = decodificar_hexadecimal(valor)

    if resultado_hex is not None:
        resultados.append({
            "formato": "Hexadecimal",
            "resultado": resultado_hex
        })

    resultado_binario = decodificar_binario(valor)

    if resultado_binario is not None:
        resultados.append({
            "formato": "Binário",
            "resultado": resultado_binario
        })

    resultado_octal = decodificar_octal(valor)

    if resultado_octal is not None:
        resultados.append({
            "formato": "Octal",
            "resultado": resultado_octal
        })

    resultado_decimal = decodificar_decimal(valor)

    if resultado_decimal is not None:
        resultados.append({
            "formato": "Decimal",
            "resultado": resultado_decimal
        })

    return resultados


# ============================================================
# ANÁLISE DE TEXTO
# ============================================================

def analisar_texto(texto):
    return {
        "tamanho_caracteres": len(texto),
        "tamanho_bytes_utf8": len(texto.encode("utf-8")),
        "letras": sum(c.isalpha() for c in texto),
        "maiusculas": sum(c.isupper() for c in texto),
        "minusculas": sum(c.islower() for c in texto),
        "numeros": sum(c.isdigit() for c in texto),
        "espacos": sum(c.isspace() for c in texto),
        "caracteres_especiais": sum(
            not c.isalnum() and not c.isspace()
            for c in texto
        ),
    }


# ============================================================
# COMPARAÇÃO
# ============================================================

def comparar_strings(primeira, segunda):
    return {
        "iguais": primeira == segunda,
        "tamanho_1": len(primeira),
        "tamanho_2": len(segunda),
        "diferenca_tamanho": abs(
            len(primeira) - len(segunda)
        ),
    }


# ============================================================
# IDENTIFICAÇÃO DE BASE64 / URL ENCODING / JWT
# ============================================================

def identificar_valor(valor):
    valor = valor.strip()

    resultado = {
        "tamanho": len(valor),
        "url_encoded": bool(
            re.search(r"%[0-9A-Fa-f]{2}", valor)
        ),
        "parece_jwt": False,
        "parece_base64": False,
    }

    valor_limpo = unquote(valor)

    # JWT normalmente possui três partes separadas por pontos.
    partes_jwt = valor_limpo.split(".")

    if len(partes_jwt) == 3:
        padrao_jwt = all(
            re.fullmatch(
                r"[A-Za-z0-9_-]+",
                parte
            )
            for parte in partes_jwt
        )

        resultado["parece_jwt"] = padrao_jwt

    # Verificação conservadora de Base64.
    try:
        candidato = "".join(valor_limpo.split())

        if len(candidato) >= 8:
            base64.b64decode(
                candidato,
                validate=True
            )

            resultado["parece_base64"] = True

    except (ValueError, binascii.Error):
        pass

    return resultado
# ============================================================
# MENU DE ANÁLISE ONLINE
# ============================================================

def analisar_online_menu():
    print("\n" + "=" * 70)
    print("ANÁLISE ONLINE")
    print("=" * 70)

    print(
        "\nUse este recurso apenas em sistemas que você"
        "\npossui ou está autorizado a analisar."
    )

    alvo = input(
        "\nURL do alvo: "
    ).strip()

    if not alvo:
        print("\nURL não informada.")
        return

    timeout_texto = input(
        "Timeout em segundos [10]: "
    ).strip()

    if not timeout_texto:
        timeout = 10.0
    else:
        try:
            timeout = float(timeout_texto)

            if timeout <= 0:
                print("\nTimeout deve ser maior que zero.")
                return

        except ValueError:
            print("\nTimeout inválido.")
            return

    portas_texto = input(
        "Portas TCP específicas para verificar "
        "(ex.: 80,443) ou ENTER para nenhuma: "
    ).strip()

    portas = None

    if portas_texto:
        try:
            portas = []

            for item in portas_texto.split(","):
                porta = int(item.strip())

                if not 1 <= porta <= 65535:
                    raise ValueError

                portas.append(porta)

            portas = sorted(set(portas))

        except ValueError:
            print(
                "\nLista de portas inválida. "
                "Use valores entre 1 e 65535."
            )
            return

    print("\nAnalisando...")
    print("Aguarde.\n")

    try:
        resultado = analisar_online(
            alvo,
            timeout=timeout,
            analisar_certificado=True,
            portas=portas,
        )

    except Exception as erro:
        print("\nFalha durante a análise:")
        print(erro)
        return

    inventario = resultado.metadados.get(
        "inventario_superficie"
    )

    dados = {
        "alvo": resultado.alvo,
        "sucesso": resultado.sucesso,
        "respostas": [
            asdict(resposta)
            for resposta in resultado.respostas
        ],
        "cookies": [
            asdict(cookie)
            for cookie in resultado.cookies
        ],
        "tls": (
            asdict(resultado.tls)
            if resultado.tls is not None
            else None
        ),
        "servicos": [
            asdict(servico)
            for servico in resultado.servicos
        ],
        "servidores": [
            asdict(servidor)
            for servidor in resultado.servidores
        ],
        "evidencias": [
            asdict(evidencia)
            for evidencia in resultado.evidencias
        ],
        "observacoes": list(
            resultado.observacoes
        ),
        "erros": list(
            resultado.erros
        ),
        "metadados": {
            chave: (
                [
                    asdict(correlacao)
                    for correlacao in valor
                ]
                if chave == "correlacoes"
                else valor
            )
            for chave, valor in resultado.metadados.items()
            if chave != "inventario_superficie"
        },
    }

    if inventario is not None:
        dados["inventario_superficie"] = (
            serializar_inventario(inventario)
        )

    print("\n" + "=" * 70)
    print("RESUMO DA ANÁLISE ONLINE")
    print("=" * 70)

    print(f"\nAlvo: {resultado.alvo}")
    print(f"Sucesso: {resultado.sucesso}")
    print(
        f"Respostas HTTP: "
        f"{len(resultado.respostas)}"
    )
    print(
        f"Cookies: "
        f"{len(resultado.cookies)}"
    )
    print(
        f"Serviços: "
        f"{len(resultado.servicos)}"
    )
    print(
        f"Servidores: "
        f"{len(resultado.servidores)}"
    )
    print(
        f"Evidências: "
        f"{len(resultado.evidencias)}"
    )

    if resultado.tls is not None:
        print(
            "\nTLS:"
        )
        print(
            f"  Protocolo: "
            f"{resultado.tls.protocolo}"
        )
        print(
            f"  Cipher: "
            f"{resultado.tls.cipher}"
        )
        print(
            f"  Certificado válido: "
            f"{resultado.tls.certificado_valido}"
        )
        print(
            f"  Hostname compatível: "
            f"{resultado.tls.hostname_compativel}"
        )

    if resultado.respostas:
        print("\nRespostas HTTP:")

        for resposta in resultado.respostas:
            print(
                f"  {resposta.status_code} "
                f"{resposta.reason} "
                f"{resposta.url}"
            )

    if resultado.servicos:
        print("\nServiços observados:")

        for servico in resultado.servicos:
            print(
                f"  {servico.porta}/"
                f"{servico.transporte}: "
                f"{servico.servico}"
            )

    if resultado.servidores:
        print("\nServidores observados:")

        for servidor in resultado.servidores:
            produto = servidor.produto or "desconhecido"
            versao = servidor.versao or "sem versão"

            print(
                f"  {produto} "
                f"{versao}"
            )

    if resultado.evidencias:
        print("\nEvidências:")

        for evidencia in resultado.evidencias:
            print(
                f"  [{evidencia.confianca}] "
                f"{evidencia.identificador}: "
                f"{evidencia.titulo}"
            )

    if resultado.erros:
        print("\nErros:")

        for erro in resultado.erros:
            print(
                f"  - {erro}"
            )

    imprimir_json(dados)

# ============================================================
# ANÁLISE DE HTTP
# ============================================================

def analisar_http(texto):
    linhas = texto.splitlines()

    resultado = {
        "tipo": "HTTP",
        "status": None,
        "versao_http": None,
        "headers": [],
        "cookies": [],
        "valores_codificados": []
    }

    for linha in linhas:
        linha = linha.strip()

        if not linha:
            continue

        # ----------------------------------------------------
        # Linha de status
        # ----------------------------------------------------

        match_status = re.match(
            r"^(HTTP/\d(?:\.\d)?)\s+(\d{3})\s*(.*)$",
            linha,
            re.IGNORECASE
        )

        if match_status:
            resultado["versao_http"] = match_status.group(1)
            resultado["status"] = {
                "codigo": int(match_status.group(2)),
                "descricao": match_status.group(3).strip()
            }
            continue

        # ----------------------------------------------------
        # Header HTTP
        # ----------------------------------------------------

        if ":" in linha:
            nome, valor = linha.split(":", 1)

            nome = nome.strip()
            valor = valor.strip()

            resultado["headers"].append({
                "nome": nome,
                "valor": valor
            })

            # ------------------------------------------------
            # Set-Cookie
            # ------------------------------------------------

            if nome.lower() == "set-cookie":
                partes = valor.split(";")

                if partes:
                    primeira = partes[0].strip()

                    if "=" in primeira:
                        cookie_nome, cookie_valor = primeira.split(
                            "=",
                            1
                        )

                        cookie_info = {
                            "nome": cookie_nome.strip(),
                            "valor_tamanho": len(
                                cookie_valor.strip()
                            ),
                            "atributos": []
                        }

                        for atributo in partes[1:]:
                            atributo = atributo.strip()

                            if atributo:
                                atributo_nome = atributo.split(
                                    "=",
                                    1
                                )[0].strip()

                                cookie_info["atributos"].append(
                                    atributo_nome
                                )

                        resultado["cookies"].append(
                            cookie_info
                        )

                        info = identificar_valor(
                            cookie_valor
                        )

                        if (
                            info["url_encoded"]
                            or info["parece_base64"]
                            or info["parece_jwt"]
                        ):
                            resultado[
                                "valores_codificados"
                            ].append({
                                "origem": "cookie",
                                "nome": cookie_nome.strip(),
                                "analise": info
                            })

    return resultado


# ============================================================
# JSON
# ============================================================

def imprimir_json(resultado):
    print("\n" + "=" * 70)
    print("JSON")
    print("=" * 70)

    print(
        json.dumps(
            resultado,
            indent=4,
            ensure_ascii=False
        )
    )


# ============================================================
# MENUS
# ============================================================

def codificar_menu():
    texto = input("\nDigite o texto: ")

    resultado = codificar(texto)

    print("\n" + "=" * 70)
    print("RESULTADOS")
    print("=" * 70)

    for chave, valor in resultado.items():
        print(f"\n{chave}:")
        print(valor)

    imprimir_json(resultado)


def decodificar_menu(tipo):
    valor = input(
        f"\nDigite o valor {tipo}: "
    )

    if tipo == "hexadecimal":
        resultado = decodificar_hexadecimal(valor)

    elif tipo == "binário":
        resultado = decodificar_binario(valor)

    elif tipo == "octal":
        resultado = decodificar_octal(valor)

    elif tipo == "decimal":
        resultado = decodificar_decimal(valor)

    elif tipo == "Base64":
        resultado = decodificar_base64(valor)

    else:
        resultado = None

    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)

    if resultado is None:
        print(
            "Valor inválido ou não foi possível descodificar."
        )
    else:
        print(resultado)


def detectar_menu():
    valor = input(
        "\nCole a string para analisar: "
    )

    formatos = detectar_formatos(valor)

    print("\n" + "=" * 70)
    print("DETECÇÃO AUTOMÁTICA")
    print("=" * 70)

    if not formatos:
        print(
            "\nNenhum formato codificado reconhecido."
        )
        return

    for item in formatos:
        print(
            f"\nFormato: {item['formato']}"
        )
        print(
            f"Resultado: {item['resultado']}"
        )

    imprimir_json({
        "entrada": valor,
        "formatos_detectados": formatos
    })


def analisar_menu():
    texto = input(
        "\nDigite o texto para analisar: "
    )

    resultado = analisar_texto(texto)

    print("\n" + "=" * 70)
    print("ANÁLISE")
    print("=" * 70)

    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")

    imprimir_json(resultado)


def comparar_menu():
    print("\n" + "=" * 70)
    print("COMPARAÇÃO DE STRINGS")
    print("=" * 70)

    primeira = input(
        "\nPrimeira string: "
    )

    segunda = input(
        "Segunda string: "
    )

    resultado = comparar_strings(
        primeira,
        segunda
    )

    print("\n" + "=" * 70)
    print("RESULTADO")
    print("=" * 70)

    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")

    imprimir_json(resultado)


# ============================================================
# MENU HTTP
# ============================================================

def analisar_http_menu():
    print("\n" + "=" * 70)
    print("ANALISADOR HTTP")
    print("=" * 70)

    print(
        "\nCole os headers HTTP."
    )

    print(
        "Digite FIM em uma linha separada para terminar."
    )

    linhas = []

    while True:
        linha = input()

        if linha.strip().upper() == "FIM":
            break

        linhas.append(linha)

    texto = "\n".join(linhas)

    resultado = analisar_http(texto)

    print("\n" + "=" * 70)
    print("RESULTADO HTTP")
    print("=" * 70)

    print(
        f"\nVersão HTTP: "
        f"{resultado['versao_http']}"
    )

    if resultado["status"]:
        print(
            f"Código: "
            f"{resultado['status']['codigo']}"
        )

        print(
            f"Descrição: "
            f"{resultado['status']['descricao']}"
        )

    print("\nHeaders encontrados:")

    for header in resultado["headers"]:
        print(
            f"  {header['nome']}: "
            f"{header['valor']}"
        )

    print("\nCookies encontrados:")

    if not resultado["cookies"]:
        print("  Nenhum cookie encontrado.")

    else:
        for cookie in resultado["cookies"]:
            print(
                f"  {cookie['nome']} "
                f"(valor com "
                f"{cookie['valor_tamanho']} caracteres)"
            )

            if cookie["atributos"]:
                print(
                    "    atributos: "
                    + ", ".join(
                        cookie["atributos"]
                    )
                )

    print(
        "\nValores com características de "
        "codificação:"
    )

    if not resultado["valores_codificados"]:
        print("  Nenhum identificado.")

    else:
        for item in resultado[
            "valores_codificados"
        ]:
            print(
                f"  {item['origem']}: "
                f"{item['nome']}"
            )

            print(
                f"    URL encoded: "
                f"{item['analise']['url_encoded']}"
            )

            print(
                f"    Parece Base64: "
                f"{item['analise']['parece_base64']}"
            )

            print(
                f"    Parece JWT: "
                f"{item['analise']['parece_jwt']}"
            )

    imprimir_json(resultado)


# ============================================================
# MENU PRINCIPAL
# ============================================================

def menu():
    while True:
        print("\n" + "=" * 70)
        print("             CODIFICADOR UNIVERSAL")
        print("=" * 70)

        print("\n1 - Codificar texto")
        print("2 - Descodificar hexadecimal")
        print("3 - Descodificar binário")
        print("4 - Descodificar octal")
        print("5 - Descodificar decimal")
        print("6 - Descodificar Base64")
        print("7 - Detectar formato automaticamente")
        print("8 - Analisar texto")
        print("9 - Comparar duas strings")
        print("10 - Analisar headers HTTP")
        print("11 - Análise online")
        print("0 - Sair")

        opcao = input(
            "\nEscolha: "
        ).strip()

        if opcao == "1":
            codificar_menu()

        elif opcao == "2":
            decodificar_menu("hexadecimal")

        elif opcao == "3":
            decodificar_menu("binário")

        elif opcao == "4":
            decodificar_menu("octal")

        elif opcao == "5":
            decodificar_menu("decimal")

        elif opcao == "6":
            decodificar_menu("Base64")

        elif opcao == "7":
            detectar_menu()

        elif opcao == "8":
            analisar_menu()

        elif opcao == "9":
            comparar_menu()

        elif opcao == "10":
            analisar_http_menu()
        elif opcao == "11":
            analisar_online_menu()

        elif opcao == "0":
            print("\nPrograma encerrado.")
            break

        else:
            print("\nOpção inválida.")


# ============================================================
# INÍCIO
# ============================================================

if __name__ == "__main__":
    menu()
