#!/usr/bin/env python3

import base64
import binascii
import json
import re


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
        partes = valor.split()

        if not partes:
            return None

        if any(
            len(parte) != 8 or
            not re.fullmatch(r"[01]{8}", parte)
            for parte in partes
        ):
            return None

        dados = bytes(int(parte, 2) for parte in partes)

        return dados.decode("utf-8")

    except (ValueError, UnicodeDecodeError):
        return None


def decodificar_octal(valor):
    try:
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

        dados = base64.b64decode(
            valor,
            validate=True
        )

        return dados.decode("utf-8")

    except (ValueError, UnicodeDecodeError, binascii.Error):
        return None


# ============================================================
# DETECÇÃO AUTOMÁTICA
# ============================================================

def detectar_formatos(valor):
    resultados = []

    valor = valor.strip()

    if not valor:
        return resultados

    # Hexadecimal
    hexadecimal = decodificar_hexadecimal(valor)

    if hexadecimal is not None:
        resultados.append({
            "formato": "hexadecimal",
            "resultado": hexadecimal
        })

    # Binário
    binario = decodificar_binario(valor)

    if binario is not None:
        resultados.append({
            "formato": "binário",
            "resultado": binario
        })

    # Octal
    octal = decodificar_octal(valor)

    if octal is not None:
        resultados.append({
            "formato": "octal",
            "resultado": octal
        })

    # Decimal
    decimal = decodificar_decimal(valor)

    if decimal is not None:
        resultados.append({
            "formato": "decimal",
            "resultado": decimal
        })

    # Base64
    base64_resultado = decodificar_base64(valor)

    if base64_resultado is not None:
        resultados.append({
            "formato": "Base64",
            "resultado": base64_resultado
        })

    return resultados


# ============================================================
# ANÁLISE DE TEXTO
# ============================================================

def analisar_texto(texto):
    caracteres = len(texto)
    bytes_tamanho = len(texto.encode("utf-8"))

    letras = sum(char.isalpha() for char in texto)
    numeros = sum(char.isdigit() for char in texto)
    espacos = sum(char.isspace() for char in texto)
    especiais = sum(
        not char.isalnum() and not char.isspace()
        for char in texto
    )

    maiusculas = sum(char.isupper() for char in texto)
    minusculas = sum(char.islower() for char in texto)

    return {
        "tamanho_caracteres": caracteres,
        "tamanho_bytes_utf8": bytes_tamanho,
        "letras": letras,
        "maiusculas": maiusculas,
        "minusculas": minusculas,
        "numeros": numeros,
        "espacos": espacos,
        "caracteres_especiais": especiais,
    }


# ============================================================
# COMPARAÇÃO
# ============================================================

def comparar_strings(a, b):
    return {
        "iguais": a == b,
        "tamanho_1": len(a),
        "tamanho_2": len(b),
        "diferenca_tamanho": abs(len(a) - len(b)),
    }


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
    valor = input(f"\nDigite o valor {tipo}: ")

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
        print("Valor inválido ou não foi possível descodificar.")
    else:
        print(resultado)


def detectar_menu():
    valor = input("\nCole a string para analisar: ")

    formatos = detectar_formatos(valor)

    print("\n" + "=" * 70)
    print("DETECÇÃO AUTOMÁTICA")
    print("=" * 70)

    if not formatos:
        print("\nNenhum formato codificado reconhecido.")
        return

    for item in formatos:
        print(f"\nFormato: {item['formato']}")
        print(f"Resultado: {item['resultado']}")

    imprimir_json({
        "entrada": valor,
        "formatos_detectados": formatos
    })


def analisar_menu():
    texto = input("\nDigite o texto para analisar: ")

    resultado = analisar_texto(texto)

    print("\n" + "=" * 70)
    print("ANÁLISE")
    print("=" * 70)

    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")

    imprimir_json(resultado)


def comparar_menu():
    print("\n" + "=" * 70)
    print("COMPARAÇÃO")
    print("=" * 70)

    primeira = input("\nPrimeira string: ")
    segunda = input("Segunda string: ")

    resultado = comparar_strings(primeira, segunda)

    print("\nResultado:")

    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")

    imprimir_json(resultado)


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
        print("0 - Sair")

        opcao = input("\nEscolha: ").strip()

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

        elif opcao == "0":
            print("\nPrograma encerrado.")
            break

        else:
            print("\nOpção inválida.")


if __name__ == "__main__":
    menu()
