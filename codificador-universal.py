#!/usr/bin/env python3

import base64
import json


def codificar(texto):
    dados = texto.encode("utf-8")

    return {
        "original": texto,
        "hexadecimal": dados.hex(),
        "binario": " ".join(format(byte, "08b") for byte in dados),
        "octal": " ".join(format(byte, "03o") for byte in dados),
        "decimal": " ".join(str(byte) for byte in dados),
        "base64": base64.b64encode(dados).decode("ascii"),
    }


def decodificar_hexadecimal(valor):
    try:
        return bytes.fromhex(valor).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def decodificar_binario(valor):
    try:
        partes = valor.split()

        if not partes:
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

        dados = bytes(int(parte, 8) for parte in partes)

        return dados.decode("utf-8")

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

        dados = bytes(numeros)

        return dados.decode("utf-8")

    except (ValueError, UnicodeDecodeError):
        return None


def decodificar_base64(valor):
    try:
        dados = base64.b64decode(
            valor,
            validate=True
        )

        return dados.decode("utf-8")

    except (ValueError, UnicodeDecodeError):
        return None


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


def codificar_menu():
    texto = input("\nDigite o texto: ")

    resultado = codificar(texto)

    print("\n" + "=" * 70)
    print("RESULTADOS")
    print("=" * 70)

    print(f"\nOriginal:\n{resultado['original']}")

    print(f"\nHexadecimal:\n{resultado['hexadecimal']}")

    print(f"\nBinário:\n{resultado['binario']}")

    print(f"\nOctal:\n{resultado['octal']}")

    print(f"\nDecimal:\n{resultado['decimal']}")

    print(f"\nBase64:\n{resultado['base64']}")

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


def menu():
    while True:
        print("\n" + "=" * 70)
        print("       CODIFICADOR UNIVERSAL")
        print("=" * 70)

        print("\n1 - Codificar texto")
        print("2 - Descodificar hexadecimal")
        print("3 - Descodificar binário")
        print("4 - Descodificar octal")
        print("5 - Descodificar decimal")
        print("6 - Descodificar Base64")
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

        elif opcao == "0":
            print("\nPrograma encerrado.")
            break

        else:
            print("\nOpção inválida.")


if __name__ == "__main__":
    menu()
