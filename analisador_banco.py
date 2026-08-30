#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs


NOME_PROJETO = "Analisador Acadêmico de Evidências HTTP"
RELATORIO_PADRAO = "relatorio_academico.json"

VALOR_OCULTADO = "[OCULTADO]"


# ============================================================
# LEITURA
# ============================================================

def ler_arquivo(caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    if not caminho.is_file():
        raise ValueError(
            f"O caminho não é um arquivo: {caminho}"
        )

    return caminho.read_text(
        encoding="utf-8",
        errors="replace",
    )


def analisar_arquivo(texto, caminho):
    caminho = Path(caminho)

    return {
        "arquivo": str(caminho),
        "nome": caminho.name,
        "tamanho_bytes": len(
            texto.encode("utf-8")
        ),
        "linhas": len(texto.splitlines()),
        "caracteres": len(texto),
    }


# ============================================================
# HTTP
# ============================================================

def detectar_http(texto):
    encontrados = []

    padrao = re.compile(
        r"HTTP/(?P<versao>\d+(?:\.\d+)?)\s+"
        r"(?P<codigo>\d{3})"
        r"(?:\s+(?P<descricao>[^\r\n]+))?",
        re.IGNORECASE,
    )

    for match in padrao.finditer(texto):
        encontrados.append(
            {
                "versao": match.group("versao"),
                "codigo": int(match.group("codigo")),
                "descricao": (
                    match.group("descricao") or ""
                ).strip(),
            }
        )

    codigos = {}

    for item in encontrados:
        codigo = str(item["codigo"])
        codigos[codigo] = (
            codigos.get(codigo, 0) + 1
        )

    return {
        "encontrados": encontrados,
        "codigos": codigos,
        "quantidade": len(encontrados),
    }


# ============================================================
# RESPOSTA HTTP
# ============================================================

def detectar_resposta_http(texto):
    respostas = []

    padrao = re.compile(
        r"(?im)^HTTP/(?P<versao>\d+(?:\.\d+)?)"
        r"\s+(?P<codigo>\d{3})"
        r"(?:\s+(?P<descricao>[^\r\n]+))?\s*$"
    )

    for match in padrao.finditer(texto):
        respostas.append(
            {
                "versao": match.group("versao"),
                "codigo": int(match.group("codigo")),
                "descricao": (
                    match.group("descricao") or ""
                ).strip(),
            }
        )

    return {
        "detectado": bool(respostas),
        "quantidade": len(respostas),
        "respostas": respostas,
    }


# ============================================================
# VALIDAÇÃO DE SINTAXE HTTP
# ============================================================

def validar_sintaxe_http(texto):
    """
    Valida passivamente linhas que aparentam ser
    requisições HTTP e fornece orientações quando
    a sintaxe não é reconhecida.

    Nenhuma requisição é enviada pela função.
    """

    linhas = texto.splitlines()

    erros = []
    avisos = []
    requisicoes_validas = 0

    padrao_requisicao = re.compile(
        r"^\s*([A-Z]+)\s+(\S+)\s+HTTP/"
        r"(\d+(?:\.\d+)?)\s*$",
        re.IGNORECASE,
    )

    metodos_comuns = {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
    }

    encontrou_candidato = False

    for numero, linha in enumerate(linhas, start=1):
        linha_limpa = linha.strip()

        if not linha_limpa:
            continue

        if (
            linha_limpa.upper().startswith(
                (
                    "GET ",
                    "POST ",
                    "PUT ",
                    "PATCH ",
                    "DELETE ",
                    "HEAD ",
                    "OPTIONS ",
                )
            )
        ):
            encontrou_candidato = True

            match = padrao_requisicao.match(linha)

            if not match:
                erros.append(
                    {
                        "linha": numero,
                        "problema": (
                            "Linha com aparência de "
                            "requisição HTTP, mas com "
                            "sintaxe inválida."
                        ),
                        "encontrado": linha_limpa,
                        "forma_correta": (
                            "MÉTODO URL HTTP/1.1"
                        ),
                        "exemplo": (
                            "GET https://exemplo.local/"
                            "v1/profile HTTP/1.1"
                        ),
                    }
                )
                continue

            metodo = match.group(1).upper()
            alvo = match.group(2)
            versao = match.group(3)

            if metodo not in metodos_comuns:
                avisos.append(
                    {
                        "linha": numero,
                        "problema": (
                            f"Método HTTP '{metodo}' "
                            "não está entre os métodos "
                            "comuns reconhecidos."
                        ),
                        "orientacao": (
                            "Verifique se o método utilizado "
                            "é intencional."
                        ),
                    }
                )

            if not alvo:
                erros.append(
                    {
                        "linha": numero,
                        "problema": "URL/alvo ausente.",
                        "encontrado": linha_limpa,
                        "forma_correta": (
                            "MÉTODO URL HTTP/1.1"
                        ),
                        "exemplo": (
                            "GET https://exemplo.local/"
                            "v1/profile HTTP/1.1"
                        ),
                    }
                )
                continue

            if versao not in {"1.0", "1.1", "2", "3"}:
                avisos.append(
                    {
                        "linha": numero,
                        "problema": (
                            f"Versão HTTP '{versao}' "
                            "não é uma versão comum "
                            "reconhecida pelo analisador."
                        ),
                        "orientacao": (
                            "Confirme a versão HTTP "
                            "presente no arquivo."
                        ),
                    }
                )

            requisicoes_validas += 1

    if not encontrou_candidato:
        avisos.append(
            {
                "linha": None,
                "problema": (
                    "Nenhuma linha de requisição HTTP "
                    "reconhecida no arquivo."
                ),
                "orientacao": (
                    "Formato esperado: "
                    "MÉTODO URL HTTP/1.1"
                ),
            }
        )

    return {
        "detectado": encontrou_candidato,
        "valido": (
            encontrou_candidato
            and not erros
        ),
        "requisicoes_validas": requisicoes_validas,
        "quantidade_erros": len(erros),
        "quantidade_avisos": len(avisos),
        "erros": erros,
        "avisos": avisos,
    }


# ============================================================
# TRANSAÇÕES HTTP
# ============================================================

def detectar_transacoes_http(texto):
    """
    Agrupa requisições e respostas HTTP encontradas
    em uma sequência de transações.

    A análise permanece totalmente passiva:
    nenhuma conexão de rede é realizada.
    """

    linhas = texto.splitlines()

    transacoes = []
    requisicao_atual = None
    resposta_atual = None

    padrao_requisicao = re.compile(
        r"^\s*([A-Z]+)\s+(\S+)\s+HTTP/"
        r"(\d+(?:\.\d+)?)\s*$",
        re.IGNORECASE,
    )

    padrao_resposta = re.compile(
        r"^\s*HTTP/"
        r"(?P<versao>\d+(?:\.\d+)?)"
        r"\s+(?P<codigo>\d{3})"
        r"(?:\s+(?P<descricao>[^\r\n]+))?\s*$",
        re.IGNORECASE,
    )

    def salvar_transacao():
        nonlocal requisicao_atual
        nonlocal resposta_atual

        if (
            requisicao_atual is not None
            or resposta_atual is not None
        ):
            transacoes.append(
                {
                    "requisicao": requisicao_atual,
                    "resposta": resposta_atual,
                }
            )

        requisicao_atual = None
        resposta_atual = None

    for linha in linhas:
        match_resposta = padrao_resposta.match(linha)

        if match_resposta:
            resposta_atual = {
                "versao": match_resposta.group("versao"),
                "codigo": int(
                    match_resposta.group("codigo")
                ),
                "descricao": (
                    match_resposta.group("descricao")
                    or ""
                ).strip(),
            }

            continue

        match_requisicao = padrao_requisicao.match(linha)

        if match_requisicao:
            if (
                requisicao_atual is not None
                or resposta_atual is not None
            ):
                salvar_transacao()

            alvo = match_requisicao.group(2)

            host = ""
            endpoint = ""

            try:
                parsed = urlparse(alvo)
                host = parsed.netloc
                endpoint = parsed.path or "/"
            except Exception:
                pass

            requisicao_atual = {
                "metodo": (
                    match_requisicao.group(1)
                    .upper()
                ),
                "alvo": alvo,
                "versao": match_requisicao.group(3),
                "host": host,
                "endpoint": endpoint,
            }

            continue

    salvar_transacao()

    return {
        "detectado": bool(transacoes),
        "quantidade": len(transacoes),
        "transacoes": transacoes,
    }


# ============================================================
# MÉTODO / ENDPOINT / URL
# ============================================================

def detectar_requisicao(texto):
    padrao = re.compile(
        r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)"
        r"\s+(\S+)"
        r"(?:\s+HTTP/(\d+(?:\.\d+)?))?",
        re.IGNORECASE | re.MULTILINE,
    )

    match = padrao.search(texto)

    if not match:
        return {
            "detectado": False,
            "metodo": None,
            "alvo": None,
            "versao": None,
            "protocolo": None,
            "host": None,
            "endpoint": None,
            "parametros": {},
        }

    metodo = match.group(1).upper()
    alvo = match.group(2)
    versao = match.group(3)

    parsed = urlparse(alvo)

    # --------------------------------------------------------
    # HOST
    # --------------------------------------------------------

    host = None

    host_match = re.search(
        r"(?im)^\s*Host\s*:\s*([^\s]+)",
        texto,
    )

    if host_match:
        host = host_match.group(1).strip()

    # --------------------------------------------------------
    # PROTOCOLO
    # --------------------------------------------------------

    protocolo = None

    if parsed.scheme:
        protocolo = parsed.scheme.upper()
    elif host:
        protocolo = "NÃO DETERMINADO"

    # --------------------------------------------------------
    # ENDPOINT
    # --------------------------------------------------------

    endpoint = parsed.path or "/"

    # --------------------------------------------------------
    # PARÂMETROS DA URL
    # --------------------------------------------------------

    parametros = {
        chave: valores
        for chave, valores in parse_qs(
            parsed.query,
            keep_blank_values=True,
        ).items()
    }

    return {
        "detectado": True,
        "metodo": metodo,
        "alvo": alvo,
        "versao": versao,
        "protocolo": protocolo,
        "host": host,
        "endpoint": endpoint,
        "parametros": parametros,
    }


# ============================================================
# HEADERS
# ============================================================

def detectar_headers(texto):
    """
    Detecta headers separando requisição e resposta HTTP.

    A análise permanece totalmente passiva.
    """

    def extrair_headers(bloco):
        headers = {}

        padrao = re.compile(
            r"(?im)^([A-Za-z0-9!#$%&'*+.\-^_`|~]+)"
            r"\s*:\s*([^\r\n]*)$"
        )

        for match in padrao.finditer(bloco):
            nome = match.group(1).strip().lower()

            headers[nome] = (
                headers.get(nome, 0) + 1
            )

        return headers

    linhas = texto.splitlines()

    requisicao_linhas = []
    resposta_linhas = []

    modo = "requisicao"

    for linha in linhas:
        if re.match(
            r"^\s*HTTP/\d+(?:\.\d+)?\s+\d{3}\b",
            linha,
            re.IGNORECASE,
        ):
            modo = "resposta"
            continue

        if modo == "requisicao":
            requisicao_linhas.append(linha)
        else:
            resposta_linhas.append(linha)

    requisicao_headers = extrair_headers(
        "\n".join(requisicao_linhas)
    )

    resposta_headers = extrair_headers(
        "\n".join(resposta_linhas)
    )

    return {
        "requisicao": {
            "quantidade": sum(requisicao_headers.values()),
            "nomes": sorted(requisicao_headers),
            "contagem": dict(sorted(requisicao_headers.items())),
        },
        "resposta": {
            "quantidade": sum(resposta_headers.values()),
            "nomes": sorted(resposta_headers),
            "contagem": dict(sorted(resposta_headers.items())),
        },
        "quantidade": (
            sum(requisicao_headers.values())
            + sum(resposta_headers.values())
        ),
        "nomes": sorted(
            set(requisicao_headers)
            | set(resposta_headers)
        ),
    }


# ============================================================
# JSON
# ============================================================

def extrair_blocos_json(texto):
    encontrados = []

    decoder = json.JSONDecoder()

    for match in re.finditer(r"[\{\[]", texto):
        inicio = match.start()

        try:
            objeto, fim = decoder.raw_decode(
                texto[inicio:]
            )

            encontrados.append(
                {
                    "inicio": inicio,
                    "fim": inicio + fim,
                    "objeto": objeto,
                }
            )

        except (json.JSONDecodeError, ValueError):
            continue

    unicos = []
    vistos = set()

    for item in encontrados:
        chave = (
            item["inicio"],
            item["fim"],
        )

        if chave not in vistos:
            vistos.add(chave)
            unicos.append(item)

    return unicos


def detectar_json(texto):
    blocos = extrair_blocos_json(texto)

    objetos = []

    for bloco in blocos:
        objeto = bloco["objeto"]

        objetos.append(
            {
                "tipo": (
                    "dict"
                    if isinstance(objeto, dict)
                    else "list"
                    if isinstance(objeto, list)
                    else type(objeto).__name__
                ),
                "valido": True,
            }
        )

    return {
        "detectado": bool(objetos),
        "quantidade": len(objetos),
        "objetos": objetos,
    }


# ============================================================
# URL ENCODING
# ============================================================

def detectar_url_encoding(texto):
    encontrados = re.findall(
        r"%[0-9A-Fa-f]{2}",
        texto,
    )

    exemplos = []

    for valor in encontrados:
        if valor.upper() not in exemplos:
            exemplos.append(valor.upper())

    return {
        "detectado": bool(encontrados),
        "quantidade": len(encontrados),
        "exemplos": exemplos[:10],
        "contagem": {
            valor: encontrados.count(valor)
            for valor in sorted(
                set(encontrados)
            )
        },
    }


# ============================================================
# COOKIES
# ============================================================

def detectar_cookies(texto):
    nomes = []

    padrao_header = re.compile(
        r"(?im)^Set-Cookie\s*:\s*"
        r"([^;\r\n]+)"
    )

    for match in padrao_header.finditer(texto):
        parte = match.group(1).strip()

        if "=" in parte:
            nome = parte.split("=", 1)[0].strip()

            if nome:
                nomes.append(nome)

    padrao_cookie = re.compile(
        r"(?im)^(?:Cookie)\s*:\s*"
        r"([^\r\n]+)"
    )

    for match in padrao_cookie.finditer(texto):
        conteudo = match.group(1)

        for item in conteudo.split(";"):
            if "=" in item:
                nome = item.split("=", 1)[0].strip()

                if nome:
                    nomes.append(nome)

    unicos = []

    for nome in nomes:
        if nome not in unicos:
            unicos.append(nome)

    return {
        "detectado": bool(unicos),
        "quantidade": len(unicos),
        "nomes": unicos,
    }


# ============================================================
# ATRIBUTOS DE COOKIE
# ============================================================

def detectar_atributos_cookie(texto):
    atributos = {
        "secure": r"(?i)\bSecure\b",
        "httponly": r"(?i)\bHttpOnly\b",
        "samesite": r"(?i)\bSameSite\b",
        "path": r"(?i)\bPath\s*=",
        "domain": r"(?i)\bDomain\s*=",
        "max_age": r"(?i)\bMax-Age\s*=",
        "expires": r"(?i)\bExpires\s*=",
    }

    resultado = {}

    for nome, padrao in atributos.items():
        resultado[nome] = len(
            re.findall(padrao, texto)
        )

    return resultado


# ============================================================
# JWT
# ============================================================

def detectar_jwt(texto):
    padrao = re.compile(
        r"\b[A-Za-z0-9_-]+\."
        r"[A-Za-z0-9_-]+\."
        r"[A-Za-z0-9_-]+\b"
    )

    encontrados = padrao.findall(texto)

    return {
        "detectado": bool(encontrados),
        "quantidade": len(encontrados),
        "observacao": (
            "Padrão compatível com JWT identificado."
            if encontrados
            else None
        ),
    }


# ============================================================
# SESSÕES
# ============================================================

def detectar_sessoes(texto):
    padroes = {
        "session": r"\bsession\b",
        "laravel_session": r"\blaravel_session\b",
        "connect_sid": r"\bconnect\.sid\b",
        "phpsessid": r"\bPHPSESSID\b",
        "session_id": r"\bsession[_-]?id\b",
        "jsessionid": r"\bJSESSIONID\b",
        "aspnet_sessionid": r"\bASP\.NET_SessionId\b",
    }

    formatos = {}

    for nome, padrao in padroes.items():
        quantidade = len(
            re.findall(
                padrao,
                texto,
                re.IGNORECASE,
            )
        )

        if quantidade:
            formatos[nome] = quantidade

    return {
        "detectado": bool(formatos),
        "formatos": formatos,
    }


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def detectar_autenticacao(texto):
    formatos = {}

    padroes = {
        "Bearer": r"\bBearer\s+[A-Za-z0-9._~+/=-]+",
        "Basic": r"\bBasic\s+[A-Za-z0-9+/=]+",
        "Authorization": (
            r"(?im)^Authorization\s*:"
        ),
        "API-Key": (
            r"(?i)\b(?:api[-_ ]?key|x-api-key)\b"
        ),
        "OAuth": r"\bOAuth(?:2)?\b",
    }

    for nome, padrao in padroes.items():
        quantidade = len(
            re.findall(padrao, texto)
        )

        if quantidade:
            formatos[nome] = quantidade

    return {
        "detectado": bool(formatos),
        "formatos": formatos,
    }


# ============================================================
# CAMPOS DE AUTENTICAÇÃO
# ============================================================

def classificar_campo(nome):
    nome = nome.lower().strip()

    if nome in {
        "login",
        "username",
        "user",
        "usuario",
        "utilizador",
        "email",
        "e-mail",
    }:
        return "login"

    if nome in {
        "password",
        "passwd",
        "pass",
        "senha",
        "password_confirmation",
    }:
        return "password"

    if (
        "token" in nome
        or nome in {
            "access_token",
            "refresh_token",
            "id_token",
        }
    ):
        return "token"

    if (
        "api-key" in nome
        or "api_key" in nome
        or nome == "apikey"
        or nome == "x-api-key"
    ):
        return "api_key"

    if "session" in nome:
        return "session"

    if nome in {
        "authorization",
        "auth",
    }:
        return "authorization"

    return None


def calcular_sha256(valor):
    return hashlib.sha256(
        valor.encode("utf-8")
    ).hexdigest()


def criar_evidencia(
    campo,
    valor,
    origem,
    localizacao=None,
):
    valor = str(valor)

    return {
        "campo": campo,
        "categoria": classificar_campo(campo),
        "origem": origem,
        "localizacao": localizacao,
        "identificado": True,
        "valor_exibido": VALOR_OCULTADO,
        "comprimento": len(valor),
        "tipo": "texto",
        "sha256": calcular_sha256(valor),
    }


def extrair_campos_json(objeto, origem="JSON"):
    evidencias = []

    def percorrer(valor, caminho=""):
        if isinstance(valor, dict):
            for chave, conteudo in valor.items():
                novo_caminho = (
                    f"{caminho}.{chave}"
                    if caminho
                    else str(chave)
                )

                categoria = classificar_campo(
                    str(chave)
                )

                if categoria:
                    if isinstance(
                        conteudo,
                        (str, int, float, bool),
                    ):
                        evidencias.append(
                            criar_evidencia(
                                str(chave),
                                conteudo,
                                origem,
                                novo_caminho,
                            )
                        )

                percorrer(
                    conteudo,
                    novo_caminho,
                )

        elif isinstance(valor, list):
            for indice, item in enumerate(valor):
                novo_caminho = (
                    f"{caminho}[{indice}]"
                )

                percorrer(
                    item,
                    novo_caminho,
                )

    percorrer(objeto)

    return evidencias


def detectar_campos_autenticacao(texto):
    evidencias = []

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    for bloco in extrair_blocos_json(texto):
        evidencias.extend(
            extrair_campos_json(
                bloco["objeto"]
            )
        )

    # --------------------------------------------------------
    # Query string da requisição
    # --------------------------------------------------------

    requisicao = detectar_requisicao(texto)

    if requisicao["detectado"]:
        for nome, valores in (
            requisicao["parametros"].items()
        ):
            categoria = classificar_campo(nome)

            if categoria:
                for valor in valores:
                    evidencias.append(
                        criar_evidencia(
                            nome,
                            valor,
                            "URL",
                            f"query.{nome}",
                        )
                    )

    # --------------------------------------------------------
    # Headers sensíveis
    # --------------------------------------------------------

    linhas = texto.splitlines()

    for numero, linha in enumerate(
        linhas,
        start=1,
    ):
        match = re.match(
            r"^\s*([A-Za-z0-9!#$%&'*+\-.^_`|~]+)"
            r"\s*:\s*(.*?)\s*$",
            linha,
        )

        if not match:
            continue

        nome = match.group(1).strip()
        valor = match.group(2).strip()

        categoria = classificar_campo(nome)

        if categoria:
            evidencias.append(
                criar_evidencia(
                    nome,
                    valor,
                    "Header",
                    f"linha {numero}",
                )
            )

    # --------------------------------------------------------
    # Formato campo=valor em texto
    # --------------------------------------------------------

    for numero, linha in enumerate(
        linhas,
        start=1,
    ):
        match = re.match(
            r"^\s*([A-Za-z_][A-Za-z0-9_.-]*)"
            r"\s*=\s*(.*?)\s*$",
            linha,
        )

        if not match:
            continue

        nome = match.group(1)
        valor = match.group(2)

        categoria = classificar_campo(nome)

        if categoria:
            evidencias.append(
                criar_evidencia(
                    nome,
                    valor,
                    "Campo",
                    f"linha {numero}",
                )
            )

    # --------------------------------------------------------
    # Remover duplicatas
    # --------------------------------------------------------

    unicas = []
    vistos = set()

    for evidencia in evidencias:
        chave = (
            evidencia["campo"],
            evidencia["categoria"],
            evidencia["origem"],
            evidencia["localizacao"],
            evidencia["sha256"],
        )

        if chave not in vistos:
            vistos.add(chave)
            unicas.append(evidencia)

    return unicas


# ============================================================
# FORMATOS
# ============================================================

def detectar_formatos(texto):
    formatos = {
        "JSON": r"application/json",
        "HTML": r"text/html",
        "XML": r"(?:application|text)/xml",
        "Form URL Encoded": (
            r"application/x-www-form-urlencoded"
        ),
        "Multipart": r"multipart/form-data",
        "WebSocket": (
            r"(?:websocket|Upgrade:\s*websocket)"
        ),
        "GraphQL": r"\bgraphql\b",
    }

    encontrados = []

    for nome, padrao in formatos.items():
        if re.search(
            padrao,
            texto,
            re.IGNORECASE,
        ):
            encontrados.append(nome)

    if detectar_json(texto)["detectado"]:
        if "JSON" not in encontrados:
            encontrados.append("JSON")

    return sorted(encontrados)


# ============================================================
# TECNOLOGIAS
# ============================================================

def detectar_tecnologias(texto):
    tecnologias = {
        "Nginx": r"\bnginx\b",
        "Apache": r"\bapache\b",
        "Laravel": r"\blaravel\b",
        "Django": r"\bdjango\b",
        "Express": r"\bexpress(?:\.js)?\b",
        "Flask": r"\bflask\b",
        "Node.js": r"\bnode(?:\.js)?\b",
        "PHP": r"\bphp\b",
        "ASP.NET": r"\basp\.net\b",
        "Spring": r"\bspring\b",
    }

    encontrados = []

    for nome, padrao in tecnologias.items():
        if re.search(
            padrao,
            texto,
            re.IGNORECASE,
        ):
            encontrados.append(nome)

    return sorted(encontrados)


# ============================================================
# BANCOS INDICADOS
# ============================================================

def detectar_bancos(texto):
    bancos = {
        "MySQL": r"\bmysql\b",
        "PostgreSQL": r"\bpostgres(?:ql)?\b",
        "SQLite": r"\bsqlite\b",
        "MongoDB": r"\bmongodb\b",
        "Redis": r"\bredis\b",
        "MariaDB": r"\bmariadb\b",
        "Oracle": r"\boracle\b",
        "SQL Server": r"\bsql\s*server\b",
    }

    encontrados = []

    for nome, padrao in bancos.items():
        if re.search(
            padrao,
            texto,
            re.IGNORECASE,
        ):
            encontrados.append(nome)

    return sorted(encontrados)


# ============================================================
# INFORMAÇÕES SENSÍVEIS
# ============================================================

def detectar_informacoes_sensiveis(texto):
    indicadores = {}

    padroes = {
        "cookie": (
            r"(?im)\b(?:cookie|set-cookie)\s*:"
        ),
        "authorization": (
            r"(?im)\bauthorization\s*:"
        ),
        "token": r"\btoken\b",
        "password": (
            r"\b(?:password|passwd|senha)\b"
        ),
        "api_key": (
            r"\b(?:api[_-]?key|x-api-key)\b"
        ),
        "session": (
            r"\b(?:session|sessid|sessionid)\b"
        ),
        "login": (
            r"\b(?:login|username|usuario|email)\b"
        ),
    }

    for nome, padrao in padroes.items():
        quantidade = len(
            re.findall(
                padrao,
                texto,
                re.IGNORECASE,
            )
        )

        if quantidade:
            indicadores[nome] = quantidade

    return indicadores


# ============================================================
# AVALIAÇÃO
# ============================================================

def avaliar(
    texto,
    http,
    cookies,
    jwt,
    sessoes,
    evidencias,
):
    indicadores = []

    if cookies["detectado"]:
        indicadores.append(
            "presenca_de_cookie"
        )

    if jwt["detectado"]:
        indicadores.append(
            "padrao_compativel_com_jwt"
        )

    if sessoes["detectado"]:
        indicadores.append(
            "indicadores_de_sessao"
        )

    if evidencias:
        indicadores.append(
            "campos_de_autenticacao_identificados"
        )

    codigos_erro = [
        codigo
        for codigo in http["codigos"]
        if int(codigo) >= 400
    ]

    if codigos_erro:
        indicadores.append(
            "erro_http_indicado"
        )

    if not indicadores:
        nivel = "BAIXO"
    elif (
        len(indicadores) <= 2
    ):
        nivel = "MODERADO"
    else:
        nivel = "ELEVADO"

    return {
        "nivel": nivel,
        "indicadores": indicadores,
        "observacao": (
            "Classificação baseada somente em "
            "padrões encontrados no arquivo. "
            "Não representa confirmação de "
            "vulnerabilidade."
        ),
    }


# ============================================================
# RELATÓRIO
# ============================================================

def gerar_relatorio(texto, caminho):
    http = detectar_http(texto)
    resposta_http = detectar_resposta_http(texto)
    cookies = detectar_cookies(texto)
    jwt = detectar_jwt(texto)
    sessoes = detectar_sessoes(texto)
    evidencias = detectar_campos_autenticacao(
        texto
    )

    requisicao = detectar_requisicao(texto)
    transacoes_http = detectar_transacoes_http(texto)
    validacao_http = validar_sintaxe_http(texto)

    return {
        "projeto": NOME_PROJETO,
        "finalidade": (
            "Pesquisa acadêmica de último ano. "
            "Análise passiva de arquivos fornecidos "
            "pelo pesquisador."
        ),
        "data_analise": datetime.now().isoformat(
            timespec="seconds"
        ),
        "escopo": {
            "modo": "arquivo_externo",
            "acesso_rede": False,
            "envio_de_requisicoes": False,
            "captura_de_credenciais": False,
            "alteracao_banco": False,
            "alteracao_arquivo_original": False,
            "exploracao": False,
        },
        "arquivo": analisar_arquivo(
            texto,
            caminho,
        ),
        "requisicao": requisicao,
        "transacoes_http": transacoes_http,
        "validacao_http": validacao_http,
        "http": http,
        "resposta_http": resposta_http,
        "headers": detectar_headers(texto),
        "json": detectar_json(texto),
        "url_encoding": detectar_url_encoding(texto),
        "cookies": cookies,
        "atributos_cookie": (
            detectar_atributos_cookie(texto)
        ),
        "jwt": jwt,
        "sessoes": sessoes,
        "autenticacao": detectar_autenticacao(
            texto
        ),
        "credenciais_evidencias": {
            "detectado": bool(evidencias),
            "quantidade": len(evidencias),
            "valores_exibidos": False,
            "metodo_verificacao": "SHA-256",
            "evidencias": evidencias,
        },
        "formatos": detectar_formatos(texto),
        "tecnologias": detectar_tecnologias(
            texto
        ),
        "bancos_indicados": detectar_bancos(
            texto
        ),
        "informacoes_sensiveis_indicadas": (
            detectar_informacoes_sensiveis(texto)
        ),
        "avaliacao": avaliar(
            texto,
            http,
            cookies,
            jwt,
            sessoes,
            evidencias,
        ),
    }


# ============================================================
# IMPRESSÃO
# ============================================================

def imprimir_relatorio(relatorio):
    arquivo = relatorio["arquivo"]
    requisicao = relatorio["requisicao"]

    print()
    print("=" * 70)
    print(
        "       ANALISADOR ACADÊMICO DE EVIDÊNCIAS HTTP"
    )
    print("=" * 70)

    print()
    print("ARQUIVO")
    print(f"Nome: {arquivo['nome']}")
    print(
        f"Tamanho: {arquivo['tamanho_bytes']} bytes"
    )
    print(f"Linhas: {arquivo['linhas']}")
    print(f"Caracteres: {arquivo['caracteres']}")

    print()
    print("ESCOPO")
    print("Modo: ANÁLISE PASSIVA DE ARQUIVO")
    print("Acesso à rede: NÃO")
    print("Envio de requisições: NÃO")
    print("Captura de credenciais: NÃO")
    print("Alteração de banco: NÃO")
    print(
        "Alteração do arquivo original: NÃO"
    )
    print("Exploração: NÃO")

    print()
    print("REQUISIÇÃO HTTP")

    if requisicao["detectado"]:
        print(
            f"Método: {requisicao['metodo']}"
        )

        print(
            f"Protocolo: "
            f"{requisicao.get('protocolo') or 'NÃO DETERMINADO'}"
        )

        print(
            f"Host: "
            f"{requisicao.get('host') or 'NÃO IDENTIFICADO'}"
        )

        print(
            f"Versão HTTP: "
            f"{requisicao.get('versao') or 'NÃO IDENTIFICADA'}"
        )

        print(
            f"URL/Alvo: "
            f"{requisicao['alvo']}"
        )

        print(
            f"Endpoint: "
            f"{requisicao['endpoint']}"
        )

        if requisicao["parametros"]:
            print("Parâmetros da URL:")

            for nome, valores in (
                requisicao["parametros"].items()
            ):
                print(
                    f"- {nome}: "
                    f"{len(valores)} valor(es)"
                )
        else:
            print(
                "Parâmetros da URL: nenhum"
            )
    else:
        print(
            "Nenhuma requisição HTTP identificada."
        )

    print()
    print("RESPOSTA HTTP")

    resposta_http = relatorio.get("resposta_http", {})

    if resposta_http.get("detectado"):
        print(
            f"Detectada: SIM "
            f"({resposta_http.get('quantidade', 0)} resposta(s))"
        )

        for resposta in resposta_http.get(
            "respostas", []
        ):
            print(
                f"- Versão HTTP: "
                f"{resposta.get('versao') or 'NÃO IDENTIFICADA'}"
            )
            print(
                f"  Código: "
                f"{resposta.get('codigo')}"
            )
            print(
                f"  Descrição: "
                f"{resposta.get('descricao') or 'NÃO INFORMADA'}"
            )
    else:
        print("Detectada: NÃO")

    print()
    print("CÓDIGOS HTTP")

    codigos = relatorio["http"]["codigos"]

    if codigos:
        for codigo, quantidade in (
            codigos.items()
        ):
            print(
                f"HTTP {codigo}: "
                f"{quantidade} ocorrência(s)"
            )
    else:
        print(
            "Nenhum código HTTP identificado."
        )

    print()
    print("HEADERS")

    headers = relatorio["headers"]

    print()
    print("Requisição:")

    requisicao_headers = headers["requisicao"]

    print(
        f"Quantidade: "
        f"{requisicao_headers['quantidade']}"
    )

    if requisicao_headers["nomes"]:
        for nome in requisicao_headers["nomes"]:
            print(f"- {nome}")
    else:
        print("- Nenhum header identificado.")

    print()
    print("Resposta:")

    resposta_headers = headers["resposta"]

    print(
        f"Quantidade: "
        f"{resposta_headers['quantidade']}"
    )

    if resposta_headers["nomes"]:
        for nome in resposta_headers["nomes"]:
            print(f"- {nome}")
    else:
        print("- Nenhum header identificado.")

    print()
    print("JSON")

    json_info = relatorio["json"]

    if json_info["detectado"]:
        print(
            f"Detectado: SIM "
            f"({json_info['quantidade']} objeto(s))"
        )
    else:
        print("Detectado: NÃO")

    print()
    print("URL ENCODING")

    url_info = relatorio["url_encoding"]

    if url_info["detectado"]:
        print(
            f"Detectado: SIM "
            f"({url_info['quantidade']} ocorrência(s))"
        )
        print(
            "Exemplos:",
            ", ".join(url_info["exemplos"])
        )
    else:
        print("Detectado: NÃO")

    print()
    print("COOKIES")

    cookie_info = relatorio["cookies"]

    if cookie_info["detectado"]:
        print(
            f"Detectados: "
            f"{cookie_info['quantidade']}"
        )
        print(
            "Nomes:",
            ", ".join(cookie_info["nomes"])
        )
    else:
        print(
            "Nenhum cookie identificado."
        )

    print()
    print("ATRIBUTOS DE COOKIE")

    for nome, quantidade in (
        relatorio["atributos_cookie"].items()
    ):
        if quantidade:
            print(
                f"- {nome}: {quantidade}"
            )

    print()
    print("JWT")

    if relatorio["jwt"]["detectado"]:
        print(
            "Padrão compatível com JWT identificado."
        )
        print(
            "Quantidade:",
            relatorio["jwt"]["quantidade"],
        )
    else:
        print(
            "Nenhum padrão JWT identificado."
        )

    print()
    print("SESSÕES")

    sessoes_info = relatorio["sessoes"]

    if sessoes_info["detectado"]:
        for nome, quantidade in (
            sessoes_info["formatos"].items()
        ):
            print(
                f"- {nome}: {quantidade}"
            )
    else:
        print(
            "Nenhum formato de sessão identificado."
        )

    print()
    print("AUTENTICAÇÃO")

    auth = relatorio["autenticacao"]

    if auth["detectado"]:
        for nome, quantidade in (
            auth["formatos"].items()
        ):
            print(
                f"- {nome}: {quantidade}"
            )
    else:
        print(
            "Nenhum padrão de autenticação identificado."
        )

    print()
    print("CREDENCIAIS / EVIDÊNCIAS")

    credenciais = (
        relatorio[
            "credenciais_evidencias"
        ]
    )

    if credenciais["detectado"]:
        print(
            f"Campos identificados: "
            f"{credenciais['quantidade']}"
        )
        print(
            "Valores reais exibidos: NÃO"
        )
        print(
            "Método de verificação: SHA-256"
        )

        for evidencia in (
            credenciais["evidencias"]
        ):
            print()
            print(
                f"- Campo: "
                f"{evidencia['campo']}"
            )
            print(
                f"  Categoria: "
                f"{evidencia['categoria']}"
            )
            print(
                f"  Origem: "
                f"{evidencia['origem']}"
            )
            print(
                f"  Localização: "
                f"{evidencia['localizacao']}"
            )
            print(
                f"  Valor: "
                f"{evidencia['valor_exibido']}"
            )
            print(
                f"  Comprimento: "
                f"{evidencia['comprimento']}"
            )
            print(
                f"  SHA-256: "
                f"{evidencia['sha256']}"
            )
    else:
        print(
            "Nenhum campo de autenticação identificado."
        )

    print()
    print("FORMATOS")

    if relatorio["formatos"]:
        for formato in relatorio["formatos"]:
            print(f"- {formato}")
    else:
        print(
            "Nenhum formato identificado."
        )

    print()
    print("TECNOLOGIAS / FRAMEWORKS")

    if relatorio["tecnologias"]:
        for tecnologia in (
            relatorio["tecnologias"]
        ):
            print(f"- {tecnologia}")
    else:
        print(
            "Nenhuma tecnologia identificada."
        )

    print()
    print("BANCO DE DADOS INDICADO")

    if relatorio["bancos_indicados"]:
        for banco in (
            relatorio["bancos_indicados"]
        ):
            print(f"- {banco}")
    else:
        print(
            "Nenhuma referência textual identificada."
        )

    print()
    print("INFORMAÇÕES SENSÍVEIS INDICADAS")

    sensiveis = (
        relatorio[
            "informacoes_sensiveis_indicadas"
        ]
    )

    if sensiveis:
        for nome, quantidade in (
            sensiveis.items()
        ):
            print(
                f"- {nome}: {quantidade}"
            )

        print(
            "Observação: valores sensíveis "
            "não são exibidos."
        )
    else:
        print(
            "Nenhum padrão identificado."
        )

    print()
    print("VALIDAÇÃO HTTP")

    validacao_http = relatorio.get(
        "validacao_http",
        {},
    )

    if validacao_http.get("detectado"):
        print(
            "Detectado: "
            + ("SIM" if validacao_http.get("detectado") else "NÃO")
        )

        print(
            "Válido: "
            + ("SIM" if validacao_http.get("valido") else "NÃO")
        )

        print(
            "Requisições válidas: "
            f"{validacao_http.get('requisicoes_validas', 0)}"
        )

        print(
            "Erros: "
            f"{validacao_http.get('quantidade_erros', 0)}"
        )

        print(
            "Avisos: "
            f"{validacao_http.get('quantidade_avisos', 0)}"
        )

        for numero, erro in enumerate(
            validacao_http.get("erros", []),
            start=1,
        ):
            print()
            print(f"ERRO {numero}")

            print(
                f"Linha: "
                f"{erro.get('linha', 'NÃO IDENTIFICADA')}"
            )

            print(
                f"Problema: "
                f"{erro.get('problema', 'NÃO INFORMADO')}"
            )

            print(
                f"Encontrado: "
                f"{erro.get('encontrado', 'NÃO INFORMADO')}"
            )

            print(
                f"Forma correta: "
                f"{erro.get('forma_correta', 'NÃO INFORMADA')}"
            )

            print(
                f"Exemplo: "
                f"{erro.get('exemplo', 'NÃO INFORMADO')}"
            )

        for numero, aviso in enumerate(
            validacao_http.get("avisos", []),
            start=1,
        ):
            print()
            print(f"AVISO {numero}")

            print(
                f"Linha: "
                f"{aviso.get('linha', 'NÃO IDENTIFICADA')}"
            )

            print(
                f"Mensagem: "
                f"{aviso.get('mensagem', 'NÃO INFORMADA')}"
            )

    else:
        print("Detectado: NÃO")
        print("Nenhuma estrutura de requisição HTTP identificada.")

    print()
    print("AVALIAÇÃO ACADÊMICA")

    avaliacao = relatorio["avaliacao"]

    print(
        f"Nível indicativo: "
        f"{avaliacao['nivel']}"
    )

    for indicador in (
        avaliacao["indicadores"]
    ):
        print(f"- {indicador}")

    print()
    print("=" * 70)
    print(
        "ATENÇÃO: indicadores não significam "
        "vulnerabilidades confirmadas."
    )
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Analisador acadêmico passivo "
            "de arquivos HTTP externos."
        )
    )

    parser.add_argument(
        "arquivo",
        help=(
            "Arquivo externo que será analisado."
        ),
    )

    parser.add_argument(
        "-o",
        "--saida",
        default=RELATORIO_PADRAO,
        help=(
            "Nome do relatório JSON. "
            "Padrão: relatorio_academico.json"
        ),
    )

    args = parser.parse_args()

    try:
        texto = ler_arquivo(
            args.arquivo
        )

        relatorio = gerar_relatorio(
            texto,
            args.arquivo,
        )

        imprimir_relatorio(
            relatorio
        )

        Path(args.saida).write_text(
            json.dumps(
                relatorio,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print()
        print(
            f"Relatório salvo em: "
            f"{args.saida}"
        )

    except Exception as erro:
        print()
        print(f"ERRO: {erro}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
