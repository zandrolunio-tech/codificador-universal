import re
from typing import Any

from online.configuracao import normalizar_configuracao


_NOMES_SENSIVEIS = {
    "api_key",
    "api-key",
    "apikey",
    "token",
    "secret",
    "password",
    "passwd",
    "authorization",
    "private_key",
    "private-key",
    "access_token",
    "refresh_token",
}


_PADROES_COMENTARIO = {
    "javascript": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
    "typescript": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
    "java": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
    "c": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
    "cpp": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
    "c++": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
    "csharp": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
    "c#": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
    "php": {
        "linha": ("//", "#"),
        "bloco": (("/*", "*/"),),
    },
    "css": {
        "linha": (),
        "bloco": (("/*", "*/"),),
    },
    "default": {
        "linha": ("//",),
        "bloco": (("/*", "*/"),),
    },
}


_PADROES_NOME = r"""
    api[_-]?key|
    apikey|
    access[_-]?token|
    refresh[_-]?token|
    private[_-]?key|
    authorization|
    password|
    passwd|
    secret|
    token|
    api[_-]?url|
    base[_-]?url
"""


_PADROES_VALOR = r"""
    "(?:\\.|[^"\\])*"
    |
    '(?:\\.|[^'\\])*'
    |
    `(?:\\.|[^`\\])*`
"""


_PADRAO_PROPRIEDADE = re.compile(
    rf"""
    (?P<nome>
        {_PADROES_NOME}
    )
    \s*
    :
    \s*
    (?P<valor>
        {_PADROES_VALOR}
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


_PADRAO_PROPRIEDADE_INDEXADA = re.compile(
    rf"""
    \[
    \s*
    (?P<aspas>["'])
    (?P<nome>
        {_PADROES_NOME}
    )
    (?P=aspas)
    \s*
    \]
    \s*
    =
    \s*
    (?P<valor>
        {_PADROES_VALOR}
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


_PADRAO_ATRIBUICAO = re.compile(
    rf"""
    (?P<prefixo>\$)?
    (?P<nome>
        {_PADROES_NOME}
    )
    \s*
    =
    \s*
    (?P<valor>
        {_PADROES_VALOR}
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)



def _mascarar_para_propriedade_indexada(
    codigo: str,
    linguagem: str | None = None,
) -> str:
    """
    Mascara comentários e strings comuns, preservando o conteúdo textual
    de strings que funcionam como chaves de propriedades indexadas.

    Exemplo preservado:
        config["token"] = "abc123"

    Mas strings comuns continuam mascaradas:
        const mensagem = "token = 'abc123'";
    """
    if not isinstance(codigo, str) or not codigo:
        return codigo

    base = _mascarar_comentarios_e_strings(
        codigo,
        linguagem=linguagem,
    )

    padrao = re.compile(
        rf"""
        (?P<prefixo>
            (?:\b[A-Za-z_$][A-Za-z0-9_$]*\s*)?
        )
        \[
        \s*
        (?P<aspas>["'])
        (?P<nome>
            {_PADROES_NOME}
        )
        (?P=aspas)
        \s*
        \]
        \s*
        =
        \s*
        (?P<valor>
            {_PADROES_VALOR}
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    resultado = list(base)

    for correspondencia in padrao.finditer(codigo):
        inicio = correspondencia.start("nome")
        fim = correspondencia.end("nome")

        if inicio < 0 or fim < 0:
            continue

        trecho_base = base[inicio:fim]

        if trecho_base.strip():
            continue

        original = codigo[inicio:fim]

        if not original:
            continue

        resultado[inicio:fim] = original

    return "".join(resultado)

def _normalizar_linguagem(linguagem: str | None) -> str:
    if not isinstance(linguagem, str):
        return "default"

    valor = linguagem.strip().lower()

    aliases = {
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "cxx": "cpp",
        "cc": "cpp",
        "h": "c",
        "hpp": "cpp",
        "cs": "csharp",
    }

    return aliases.get(valor, valor or "default")


def _mascarar_comentarios(
    codigo: str,
    *,
    linguagem: str = "javascript",
) -> str:
    """
    Mascara comentários sem alterar o tamanho do conteúdo original.

    Caracteres de comentário são substituídos por espaços.
    Quebras de linha são preservadas para manter linha/coluna.

    Strings são preservadas e analisadas antes dos delimitadores
    de comentário, evitando confundir conteúdos como "//" dentro
    de uma string com comentário.
    """
    regras = _PADROES_COMENTARIO.get(
        _normalizar_linguagem(linguagem),
        _PADROES_COMENTARIO["default"],
    )

    resultado = list(codigo)
    i = 0
    estado = "normal"

    while i < len(codigo):
        if estado == "normal":
            encontrou_comentario = False

            for delimitador in regras["linha"]:
                if codigo.startswith(delimitador, i):
                    for posicao in range(
                        i,
                        min(i + len(delimitador), len(codigo)),
                    ):
                        resultado[posicao] = " "

                    i += len(delimitador)
                    estado = "comentario_linha"
                    encontrou_comentario = True
                    break

            if encontrou_comentario:
                continue

            for abertura, fechamento in regras["bloco"]:
                if codigo.startswith(abertura, i):
                    for posicao in range(
                        i,
                        min(i + len(abertura), len(codigo)),
                    ):
                        resultado[posicao] = " "

                    i += len(abertura)
                    estado = "comentario_bloco"
                    encontrou_comentario = True
                    break

            if encontrou_comentario:
                continue

            if codigo[i] == '"':
                estado = "string_dupla"
            elif codigo[i] == "'":
                estado = "string_simples"
            elif codigo[i] == "`":
                estado = "template"

            i += 1
            continue

        if estado == "comentario_linha":
            if codigo[i] == "\n":
                estado = "normal"
            else:
                resultado[i] = " "

            i += 1
            continue

        if estado == "comentario_bloco":
            terminou = False

            for _, fechamento in regras["bloco"]:
                if codigo.startswith(fechamento, i):
                    for posicao in range(
                        i,
                        min(i + len(fechamento), len(codigo)),
                    ):
                        resultado[posicao] = " "

                    i += len(fechamento)
                    estado = "normal"
                    terminou = True
                    break

            if terminou:
                continue

            if codigo[i] != "\n":
                resultado[i] = " "

            i += 1
            continue

        if estado == "string_dupla":
            if codigo[i] == "\\":
                i += min(2, len(codigo) - i)
                continue

            if codigo[i] == '"':
                estado = "normal"

            i += 1
            continue

        if estado == "string_simples":
            if codigo[i] == "\\":
                i += min(2, len(codigo) - i)
                continue

            if codigo[i] == "'":
                estado = "normal"

            i += 1
            continue

        if estado == "template":
            if codigo[i] == "\\":
                i += min(2, len(codigo) - i)
                continue

            if codigo[i] == "`":
                estado = "normal"

            i += 1
            continue

    return "".join(resultado)



def _mascarar_comentarios_e_strings(
    codigo: str,
    *,
    linguagem: str = "javascript",
) -> str:
    """
    Cria uma representação lexical para detectar atribuições reais.

    Comentários e conteúdo de strings são mascarados.
    Os delimitadores das strings são preservados.

    Quebras de linha e tamanho total do texto são preservados.
    O conteúdo original nunca é alterado.
    """
    regras = _PADROES_COMENTARIO.get(
        _normalizar_linguagem(linguagem),
        _PADROES_COMENTARIO["default"],
    )

    resultado = list(codigo)
    i = 0
    estado = "normal"

    while i < len(codigo):
        if estado == "normal":
            encontrou = False

            for delimitador in regras["linha"]:
                if codigo.startswith(delimitador, i):
                    for posicao in range(
                        i,
                        min(i + len(delimitador), len(codigo)),
                    ):
                        resultado[posicao] = " "

                    i += len(delimitador)
                    estado = "comentario_linha"
                    encontrou = True
                    break

            if encontrou:
                continue

            for abertura, fechamento in regras["bloco"]:
                if codigo.startswith(abertura, i):
                    for posicao in range(
                        i,
                        min(i + len(abertura), len(codigo)),
                    ):
                        resultado[posicao] = " "

                    i += len(abertura)
                    estado = "comentario_bloco"
                    encontrou = True
                    break

            if encontrou:
                continue

            if codigo[i] == '"':
                estado = "string_dupla"
                i += 1
                continue

            if codigo[i] == "'":
                estado = "string_simples"
                i += 1
                continue

            if codigo[i] == "`":
                estado = "template"
                i += 1
                continue

            i += 1
            continue

        if estado == "comentario_linha":
            if codigo[i] == "\n":
                estado = "normal"
            else:
                resultado[i] = " "

            i += 1
            continue

        if estado == "comentario_bloco":
            terminou = False

            for _, fechamento in regras["bloco"]:
                if codigo.startswith(fechamento, i):
                    for posicao in range(
                        i,
                        min(i + len(fechamento), len(codigo)),
                    ):
                        resultado[posicao] = " "

                    i += len(fechamento)
                    estado = "normal"
                    terminou = True
                    break

            if terminou:
                continue

            if codigo[i] != "\n":
                resultado[i] = " "

            i += 1
            continue

        if estado == "string_dupla":
            if codigo[i] == "\\":
                if i + 1 < len(codigo):
                    if codigo[i + 1] != "\n":
                        resultado[i + 1] = " "
                    i += 2
                else:
                    i += 1

                continue

            if codigo[i] == '"':
                estado = "normal"
                i += 1
                continue

            if codigo[i] != "\n":
                resultado[i] = " "

            i += 1
            continue

        if estado == "string_simples":
            if codigo[i] == "\\":
                if i + 1 < len(codigo):
                    if codigo[i + 1] != "\n":
                        resultado[i + 1] = " "
                    i += 2
                else:
                    i += 1

                continue

            if codigo[i] == "'":
                estado = "normal"
                i += 1
                continue

            if codigo[i] != "\n":
                resultado[i] = " "

            i += 1
            continue

        if estado == "template":
            if codigo[i] == "\\":
                if i + 1 < len(codigo):
                    if codigo[i + 1] != "\n":
                        resultado[i + 1] = " "
                    i += 2
                else:
                    i += 1

                continue

            if codigo[i] == "`":
                estado = "normal"
                i += 1
                continue

            if codigo[i] != "\n":
                resultado[i] = " "

            i += 1
            continue

    return "".join(resultado)

def _desempacotar_valor(valor: str) -> str:
    if len(valor) >= 2 and valor[0] == valor[-1]:
        return valor[1:-1]

    return valor


def _nome_normalizado(nome: str) -> str:
    nome = nome.strip().lower()

    aliases = {
        "api-key": "api_key",
        "apikey": "api_key",
        "access-token": "access_token",
        "refresh-token": "refresh_token",
        "private-key": "private_key",
        "api-url": "api_url",
        "base-url": "base_url",
    }

    return aliases.get(nome, nome)


def _tem_contexto_configuracao(codigo: str, inicio: int) -> bool:
    inicio_contexto = max(0, inicio - 160)
    contexto = codigo[inicio_contexto:inicio].lower()

    marcadores = (
        "config",
        "settings",
        "environment",
        "env",
        "credentials",
        "credential",
    )

    return any(marcador in contexto for marcador in marcadores)


def _e_valor_sensivel(nome: str) -> bool:
    return nome in {
        "api_key",
        "token",
        "secret",
        "password",
        "passwd",
        "authorization",
        "private_key",
        "access_token",
        "refresh_token",
    }


def _classificar(
    nome: str,
    valor: str,
    contexto_configuracao: bool,
) -> tuple[str, int]:
    del valor

    if nome in {
        "api_key",
        "access_token",
        "refresh_token",
        "secret",
    }:
        return "provavel", 90 if contexto_configuracao else 80

    if nome in {"password", "passwd"}:
        return "provavel", 90 if contexto_configuracao else 80

    if nome == "token":
        return "provavel", 85 if contexto_configuracao else 75

    if nome == "authorization":
        return "provavel", 90 if contexto_configuracao else 80

    if nome == "private_key":
        return "provavel", 90 if contexto_configuracao else 80

    if nome in {"api_url", "base_url"}:
        return "provavel", 90

    return "possivel", 60


def _localizacao(
    codigo: str,
    inicio: int,
    *,
    arquivo: str | None,
) -> dict[str, Any]:
    linha = codigo.count("\n", 0, inicio) + 1
    ultima_quebra = codigo.rfind("\n", 0, inicio)
    coluna = inicio - ultima_quebra

    return {
        "arquivo": arquivo,
        "linha": linha,
        "coluna": coluna,
    }


def _criar_configuracao(
    *,
    codigo: str,
    correspondencia: re.Match[str],
    origem: str,
    arquivo: str | None,
    caminho: str | None,
    tipo_deteccao: str,
) -> dict[str, Any]:
    nome_original = correspondencia.group("nome")

    inicio_valor, fim_valor = correspondencia.span("valor")
    valor_bruto = codigo[inicio_valor:fim_valor]

    nome = _nome_normalizado(nome_original)
    valor = _desempacotar_valor(valor_bruto)

    contexto_configuracao = _tem_contexto_configuracao(
        codigo,
        correspondencia.start(),
    )

    classificacao, pontuacao = _classificar(
        nome,
        valor,
        contexto_configuracao,
    )

    if pontuacao >= 85:
        confianca = "alta"
    elif pontuacao >= 70:
        confianca = "media"
    else:
        confianca = "baixa"

    evidencias = [
        f"nome de configuração compatível: {nome}",
        "valor associado encontrado no conteúdo observado",
        f"forma de detecção: {tipo_deteccao}",
    ]

    if contexto_configuracao:
        evidencias.append(
            "encontrado em contexto relacionado a configuração"
        )

    if _e_valor_sensivel(nome):
        evidencias.append(
            "nome classificado como potencialmente sensível"
        )

    return normalizar_configuracao(
        nome=nome,
        valor=valor,
        origem=origem,
        fonte=arquivo or "",
        localizacao=_localizacao(
            codigo,
            correspondencia.start(),
            arquivo=arquivo,
        ),
        caminho=caminho or "",
        contexto="configuração observada em código",
        tipo=(
            "segredo potencial"
            if _e_valor_sensivel(nome)
            else "configuração"
        ),
        sensivel=_e_valor_sensivel(nome),
        classificacao=classificacao,
        pontuacao=pontuacao,
        confianca=confianca,
        evidencias=evidencias,
    )


def detectar_configuracoes(
    codigo: str,
    *,
    origem: str = "desconhecida",
    arquivo: str | None = None,
    caminho: str | None = None,
    linguagem: str = "javascript",
) -> list[dict[str, Any]]:
    """
    Detecta configurações observadas em conteúdo já coletado.

    A análise é passiva:
    - não realiza requests;
    - não lê arquivos;
    - não tenta autenticação;
    - não usa valores encontrados.

    Comentários e conteúdos de strings são mascarados para a detecção,
    preservando posições, delimitadores de string e quebras de linha.
    O conteúdo original permanece intacto para recuperar os valores
    observados através das posições dos grupos encontrados.

    São reconhecidas duas formas principais:
    - propriedades: token: "valor"
    - atribuições: token = "valor"

    Valores sensíveis são protegidos por normalizar_configuracao().
    """
    if not isinstance(codigo, str) or not codigo:
        return []

    codigo_analisavel = _mascarar_para_propriedade_indexada(
        codigo,
        linguagem=linguagem,
    )

    encontrados: set[tuple[str, int]] = set()
    ocorrencias: list[tuple[int, str, re.Match[str]]] = []

    for correspondencia in _PADRAO_PROPRIEDADE.finditer(
        codigo_analisavel
    ):
        ocorrencias.append(
            (
                correspondencia.start(),
                "propriedade",
                correspondencia,
            )
        )

    for correspondencia in _PADRAO_PROPRIEDADE_INDEXADA.finditer(
        codigo_analisavel
    ):
        ocorrencias.append(
            (
                correspondencia.start(),
                "propriedade_indexada",
                correspondencia,
            )
        )

    for correspondencia in _PADRAO_ATRIBUICAO.finditer(
        codigo_analisavel
    ):
        ocorrencias.append(
            (
                correspondencia.start(),
                "atribuicao",
                correspondencia,
            )
        )

    ocorrencias.sort(key=lambda item: item[0])

    resultado: list[dict[str, Any]] = []

    for _, tipo_deteccao, correspondencia in ocorrencias:
        nome = _nome_normalizado(
            correspondencia.group("nome")
        )

        chave = (
            nome,
            correspondencia.start(),
        )

        if chave in encontrados:
            continue

        encontrados.add(chave)

        resultado.append(
            _criar_configuracao(
                codigo=codigo,
                correspondencia=correspondencia,
                origem=origem,
                arquivo=arquivo,
                caminho=caminho,
                tipo_deteccao=tipo_deteccao,
            )
        )

    return resultado
