#!/usr/bin/env python3

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote


# ============================================================
# CONFIGURAÇÃO
# ============================================================

NOME_PROJETO = "Análise Passiva de Respostas e Evidências Técnicas"
RELATORIO_PADRAO = "relatorio_academico.json"


# ============================================================
# LEITURA DO ARQUIVO
# ============================================================

def ler_arquivo(caminho):
    """Lê um arquivo externo sem modificá-lo."""

    caminho = Path(caminho)

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if not caminho.is_file():
        raise ValueError(f"O caminho não é um arquivo: {caminho}")

    return caminho.read_text(
        encoding="utf-8",
        errors="replace"
    )


# ============================================================
# INFORMAÇÕES BÁSICAS
# ============================================================

def analisar_arquivo(texto, caminho):
    caminho = Path(caminho)

    return {
        "arquivo": str(caminho),
        "nome": caminho.name,
        "tamanho_bytes": len(texto.encode("utf-8")),
        "linhas": len(texto.splitlines()),
        "caracteres": len(texto),
    }


# ============================================================
# HTTP
# ============================================================

def detectar_http(texto):
    encontrados = []

    padrao = re.compile(
        r"HTTP/(\d(?:\.\d)?)\s+(\d{3})\s+([^\r\n]+)",
        re.IGNORECASE
    )

    for resultado in padrao.finditer(texto):
        encontrados.append({
            "versao": resultado.group(1),
            "codigo": int(resultado.group(2)),
            "descricao": resultado.group(3).strip(),
        })

    contagem = Counter(
        item["codigo"]
        for item in encontrados
    )

    return {
        "encontrados": encontrados,
        "codigos": dict(sorted(contagem.items())),
        "quantidade": len(encontrados),
    }


# ============================================================
# HEADERS
# ============================================================

def detectar_headers(texto):
    headers = []

    padrao = re.compile(
        r"^([A-Za-z0-9!#$%&'*+\-.^_`|~]+):[ \t]*(.*)$",
        re.MULTILINE
    )

    for resultado in padrao.finditer(texto):
        nome = resultado.group(1)
        valor = resultado.group(2).strip()

        headers.append({
            "nome": nome,
            "valor": valor,
        })

    contagem = Counter(
        item["nome"].lower()
        for item in headers
    )

    return {
        "quantidade": len(headers),
        "nomes": sorted(contagem.keys()),
        "contagem": dict(sorted(contagem.items())),
    }


# ============================================================
# JSON
# ============================================================

def detectar_json(texto):
    objetos = []

    candidatos = []

    for linha in texto.splitlines():
        linha = linha.strip()

        if linha.startswith("{") and linha.endswith("}"):
            candidatos.append(linha)

        elif linha.startswith("[") and linha.endswith("]"):
            candidatos.append(linha)

    for candidato in candidatos:
        try:
            dados = json.loads(candidato)

            objetos.append({
                "tipo": type(dados).__name__,
                "valido": True,
            })

        except json.JSONDecodeError:
            pass

    return {
        "detectado": bool(objetos),
        "quantidade": len(objetos),
        "objetos": objetos,
    }


# ============================================================
# URL ENCODING
# ============================================================

def detectar_url_encoding(texto):
    """
    Detecta sequências percent-encoded, como:

    %20
    %3D
    %2F
    %3A
    """

    encontrados = re.findall(
        r"%[0-9A-Fa-f]{2}",
        texto
    )

    contagem = Counter(
        item.upper()
        for item in encontrados
    )

    exemplos = sorted(contagem.keys())[:20]

    return {
        "detectado": bool(encontrados),
        "quantidade": len(encontrados),
        "exemplos": exemplos,
        "contagem": dict(sorted(contagem.items())),
    }


# ============================================================
# COOKIES
# ============================================================

def detectar_cookies(texto):
    cookies = []

    padrao = re.compile(
        r"(?im)^Set-Cookie:\s*([^;\r\n]+)"
    )

    for resultado in padrao.finditer(texto):
        valor = resultado.group(1).strip()

        if "=" in valor:
            nome = valor.split("=", 1)[0].strip()

            cookies.append({
                "nome": nome,
                "valor_presente": True,
            })

    nomes = sorted(
        set(item["nome"] for item in cookies)
    )

    return {
        "detectado": bool(cookies),
        "quantidade": len(cookies),
        "nomes": nomes,
    }


# ============================================================
# ATRIBUTOS DE COOKIE
# ============================================================

def detectar_atributos_cookie(texto):
    atributos = {
        "secure": len(re.findall(r";\s*Secure\b", texto, re.I)),
        "httponly": len(re.findall(r";\s*HttpOnly\b", texto, re.I)),
        "samesite": len(re.findall(r";\s*SameSite\s*=", texto, re.I)),
        "path": len(re.findall(r";\s*Path\s*=", texto, re.I)),
        "domain": len(re.findall(r";\s*Domain\s*=", texto, re.I)),
        "max_age": len(re.findall(r";\s*Max-Age\s*=", texto, re.I)),
        "expires": len(re.findall(r";\s*Expires\s*=", texto, re.I)),
    }

    return atributos


# ============================================================
# JWT
# ============================================================

def detectar_jwt(texto):
    padrao = re.compile(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
    )

    encontrados = padrao.findall(texto)

    return {
        "detectado": bool(encontrados),
        "quantidade": len(encontrados),
        "observacao": (
            "Padrão compatível com JWT encontrado. "
            "O conteúdo não é decodificado nem validado."
            if encontrados
            else None
        ),
    }


# ============================================================
# SESSÕES
# ============================================================

def detectar_sessoes(texto):
    padroes = {
        "session": r"\b(?:session|sess|sid)[_-]?(?:id|token)?\b",
        "laravel_session": r"\blaravel_session\b",
        "connect_sid": r"\bconnect\.sid\b",
        "phpsessid": r"\bPHPSESSID\b",
        "jsessionid": r"\bJSESSIONID\b",
        "aspnet_session": r"\bASP\.NET_SessionId\b",
        "csrf": r"\b(?:csrf|xsrf)[_-]?(?:token)?\b",
    }

    encontrados = {}

    for nome, padrao in padroes.items():
        quantidade = len(
            re.findall(padrao, texto, re.IGNORECASE)
        )

        if quantidade:
            encontrados[nome] = quantidade

    return {
        "detectado": bool(encontrados),
        "formatos": encontrados,
    }


# ============================================================
# TECNOLOGIAS / FRAMEWORKS
# ============================================================

def detectar_tecnologias(texto):
    tecnologias = {
        "Nginx": r"\bnginx\b",
        "Apache": r"\bapache\b",
        "Cloudflare": r"\bcloudflare\b",
        "Laravel": r"\blaravel\b",
        "PHP": r"\bPHP(?:/\d+(?:\.\d+)*)?\b",
        "Node.js": r"\bnode(?:\.js)?\b",
        "Express": r"\bexpress\b",
        "Django": r"\bdjango\b",
        "Flask": r"\bflask\b",
        "FastAPI": r"\bfastapi\b",
        "Spring": r"\bspring\b",
        "ASP.NET": r"\bASP\.NET\b",
        "IIS": r"\bIIS\b",
        "Next.js": r"\bnext\.js\b",
        "React": r"\breact\b",
        "Vue.js": r"\bvue(?:\.js)?\b",
        "Angular": r"\bangular\b",
        "WordPress": r"\bwordpress\b",
        "OpenResty": r"\bopenresty\b",
        "Gunicorn": r"\bgunicorn\b",
        "uWSGI": r"\buwsgi\b",
    }

    encontrados = []

    for nome, padrao in tecnologias.items():
        if re.search(padrao, texto, re.IGNORECASE):
            encontrados.append(nome)

    return sorted(encontrados)


# ============================================================
# BANCOS DE DADOS
# ============================================================

def detectar_bancos(texto):
    bancos = {
        "MySQL": r"\bmysql\b",
        "MariaDB": r"\bmariadb\b",
        "PostgreSQL": r"\bpostgres(?:ql)?\b",
        "SQLite": r"\bsqlite\b",
        "Microsoft SQL Server": r"\b(?:mssql|sql\s*server)\b",
        "Oracle Database": r"\boracle(?:\s+database)?\b",
        "MongoDB": r"\bmongodb\b",
        "Redis": r"\bredis\b",
        "Cassandra": r"\bcassandra\b",
        "DynamoDB": r"\bdynamodb\b",
        "Elasticsearch": r"\belasticsearch\b",
    }

    encontrados = []

    for nome, padrao in bancos.items():
        if re.search(padrao, texto, re.IGNORECASE):
            encontrados.append(nome)

    return sorted(encontrados)


# ============================================================
# FORMATOS DE AUTENTICAÇÃO
# ============================================================

def detectar_autenticacao(texto):
    formatos = {}

    padroes = {
        "Bearer": r"\bBearer\s+[A-Za-z0-9._~+/=-]+",
        "Basic": r"\bBasic\s+[A-Za-z0-9+/=]+",
        "Authorization": r"(?im)^Authorization\s*:",
        "API-Key": r"(?i)\b(?:api[-_ ]?key|x-api-key)\b",
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
# CONTENT-TYPE / FORMATOS
# ============================================================

def detectar_formatos(texto):
    formatos = {
        "JSON": r"application/json",
        "HTML": r"text/html",
        "XML": r"(?:application|text)/xml",
        "Form URL Encoded": r"application/x-www-form-urlencoded",
        "Multipart": r"multipart/form-data",
        "WebSocket": r"(?:websocket|Upgrade:\s*websocket)",
        "GraphQL": r"\bgraphql\b",
    }

    encontrados = []

    for nome, padrao in formatos.items():
        if re.search(padrao, texto, re.IGNORECASE):
            encontrados.append(nome)

    return sorted(encontrados)


# ============================================================
# INFORMAÇÕES SENSÍVEIS
# ============================================================

def detectar_informacoes_sensiveis(texto):
    indicadores = {}

    padroes = {
        "cookie": r"(?im)\b(?:cookie|set-cookie)\s*:",
        "authorization": r"(?im)\bauthorization\s*:",
        "token": r"\btoken\b",
        "password": r"\b(?:password|passwd|senha)\b",
        "api_key": r"\b(?:api[_-]?key|x-api-key)\b",
        "session": r"\b(?:session|sessid|sessionid)\b",
    }

    for nome, padrao in padroes.items():
        quantidade = len(
            re.findall(padrao, texto, re.IGNORECASE)
        )

        if quantidade:
            indicadores[nome] = quantidade

    return indicadores


# ============================================================
# CLASSIFICAÇÃO ACADÊMICA
# ============================================================

def avaliar(texto, http, cookies, jwt, sessoes):
    indicadores = []

    if cookies["detectado"]:
        indicadores.append("presenca_de_cookie")

    if jwt["detectado"]:
        indicadores.append("padrao_compativel_com_jwt")

    if sessoes["detectado"]:
        indicadores.append("indicadores_de_sessao")

    if any(
        codigo >= 500
        for codigo in http["codigos"]
    ):
        indicadores.append("erro_de_servidor_indicado")

    if any(
        400 <= codigo < 500
        for codigo in http["codigos"]
    ):
        indicadores.append("erro_de_cliente_indicado")

    if jwt["detectado"] or cookies["detectado"]:
        nivel = "MODERADO"

    elif indicadores:
        nivel = "BAIXO"

    else:
        nivel = "BAIXO"

    return {
        "nivel": nivel,
        "indicadores": indicadores,
        "observacao": (
            "Classificação baseada somente em padrões "
            "encontrados no arquivo. Não representa "
            "confirmação de vulnerabilidade."
        ),
    }


# ============================================================
# RELATÓRIO COMPLETO
# ============================================================

def gerar_relatorio(texto, caminho):
    http = detectar_http(texto)
    cookies = detectar_cookies(texto)
    jwt = detectar_jwt(texto)
    sessoes = detectar_sessoes(texto)

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
            "alteracao_banco": False,
            "alteracao_arquivo_original": False,
            "exploracao": False,
        },
        "arquivo": analisar_arquivo(
            texto,
            caminho
        ),
        "http": http,
        "headers": detectar_headers(texto),
        "json": detectar_json(texto),
        "url_encoding": detectar_url_encoding(texto),
        "cookies": cookies,
        "atributos_cookie": detectar_atributos_cookie(texto),
        "jwt": jwt,
        "sessoes": sessoes,
        "autenticacao": detectar_autenticacao(texto),
        "formatos": detectar_formatos(texto),
        "tecnologias": detectar_tecnologias(texto),
        "bancos_indicados": detectar_bancos(texto),
        "informacoes_sensiveis_indicadas": (
            detectar_informacoes_sensiveis(texto)
        ),
        "avaliacao": avaliar(
            texto,
            http,
            cookies,
            jwt,
            sessoes,
        ),
    }


# ============================================================
# IMPRESSÃO
# ============================================================

def imprimir_relatorio(relatorio):
    arquivo = relatorio["arquivo"]

    print()
    print("=" * 70)
    print("       ANALISADOR ACADÊMICO DE ARQUIVO EXTERNO")
    print("=" * 70)

    print()
    print("ARQUIVO")
    print(f"Nome: {arquivo['nome']}")
    print(f"Tamanho: {arquivo['tamanho_bytes']} bytes")
    print(f"Linhas: {arquivo['linhas']}")
    print(f"Caracteres: {arquivo['caracteres']}")

    print()
    print("ESCOPO")
    print("Acesso à rede: NÃO")
    print("Alteração de banco: NÃO")
    print("Alteração do arquivo original: NÃO")
    print("Exploração: NÃO")

    print()
    print("CÓDIGOS HTTP")

    codigos = relatorio["http"]["codigos"]

    if codigos:
        for codigo, quantidade in codigos.items():
            print(
                f"HTTP {codigo}: "
                f"{quantidade} ocorrência(s)"
            )
    else:
        print("Nenhum código HTTP identificado.")

    print()
    print("HEADERS")
    print(
        f"Quantidade: "
        f"{relatorio['headers']['quantidade']}"
    )

    if relatorio["headers"]["nomes"]:
        for nome in relatorio["headers"]["nomes"]:
            print(f"- {nome}")

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
            f"Detectados: {cookie_info['quantidade']}"
        )
        print(
            "Nomes:",
            ", ".join(cookie_info["nomes"])
        )
    else:
        print("Nenhum cookie identificado.")

    print()
    print("ATRIBUTOS DE COOKIE")

    for nome, quantidade in (
        relatorio["atributos_cookie"].items()
    ):
        if quantidade:
            print(f"- {nome}: {quantidade}")

    print()
    print("JWT")

    if relatorio["jwt"]["detectado"]:
        print(
            "Padrão compatível com JWT identificado."
        )
        print(
            "Quantidade:",
            relatorio["jwt"]["quantidade"]
        )
    else:
        print("Nenhum padrão JWT identificado.")

    print()
    print("SESSÕES")

    sessoes_info = relatorio["sessoes"]

    if sessoes_info["detectado"]:
        for nome, quantidade in (
            sessoes_info["formatos"].items()
        ):
            print(f"- {nome}: {quantidade}")
    else:
        print("Nenhum formato de sessão identificado.")

    print()
    print("AUTENTICAÇÃO")

    auth = relatorio["autenticacao"]

    if auth["detectado"]:
        for nome, quantidade in auth["formatos"].items():
            print(f"- {nome}: {quantidade}")
    else:
        print("Nenhum padrão de autenticação identificado.")

    print()
    print("FORMATOS")

    if relatorio["formatos"]:
        for formato in relatorio["formatos"]:
            print(f"- {formato}")
    else:
        print("Nenhum formato identificado.")

    print()
    print("TECNOLOGIAS / FRAMEWORKS")

    if relatorio["tecnologias"]:
        for tecnologia in relatorio["tecnologias"]:
            print(f"- {tecnologia}")
    else:
        print("Nenhuma tecnologia identificada.")

    print()
    print("BANCO DE DADOS INDICADO")

    if relatorio["bancos_indicados"]:
        for banco in relatorio["bancos_indicados"]:
            print(f"- {banco}")
    else:
        print("Nenhuma referência textual identificada.")

    print()
    print("INFORMAÇÕES SENSÍVEIS INDICADAS")

    sensiveis = (
        relatorio[
            "informacoes_sensiveis_indicadas"
        ]
    )

    if sensiveis:
        for nome, quantidade in sensiveis.items():
            print(f"- {nome}: {quantidade}")

        print(
            "Observação: os valores reais não "
            "foram copiados para o relatório."
        )
    else:
        print("Nenhum padrão identificado.")

    print()
    print("AVALIAÇÃO ACADÊMICA")

    avaliacao = relatorio["avaliacao"]

    print(
        f"Nível indicativo: "
        f"{avaliacao['nivel']}"
    )

    for indicador in avaliacao["indicadores"]:
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
            "de arquivos externos."
        )
    )

    parser.add_argument(
        "arquivo",
        help="Arquivo externo que será analisado."
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
        texto = ler_arquivo(args.arquivo)

        relatorio = gerar_relatorio(
            texto,
            args.arquivo
        )

        imprimir_relatorio(relatorio)

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
            f"Relatório salvo em: {args.saida}"
        )

    except Exception as erro:
        print()
        print(f"ERRO: {erro}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
