from __future__ import annotations

import json
import re

from .modelos import (
    CookieObservado,
    Evidencia,
    HTTPResposta,
)


def _normalizar_nome(nome):
    return nome.strip().lower()


def _headers_dict(resposta):
    return {
        _normalizar_nome(header.nome): header.valor
        for header in resposta.headers
    }


def _detectar_json(resposta):
    content_type = resposta.content_type.lower()
    corpo = resposta.corpo.strip()

    if "application/json" in content_type:
        try:
            objeto = json.loads(corpo)
            return {
                "detectado": True,
                "valido": True,
                "tipo": type(objeto).__name__,
                "quantidade": 1,
            }
        except json.JSONDecodeError:
            return {
                "detectado": True,
                "valido": False,
                "tipo": None,
                "quantidade": 0,
            }

    if corpo.startswith("{") or corpo.startswith("["):
        try:
            objeto = json.loads(corpo)
            return {
                "detectado": True,
                "valido": True,
                "tipo": type(objeto).__name__,
                "quantidade": 1,
            }
        except json.JSONDecodeError:
            pass

    return {
        "detectado": False,
        "valido": False,
        "tipo": None,
        "quantidade": 0,
    }


def _detectar_html(resposta):
    content_type = resposta.content_type.lower()
    corpo = resposta.corpo.lower()

    detectado = (
        "text/html" in content_type
        or "<html" in corpo
        or "<!doctype html" in corpo
    )

    return {
        "detectado": detectado,
        "content_type": resposta.content_type,
    }


def _mascarar_valor_cookie(valor):
    """
    Produz uma representação segura do valor do cookie.

    O valor original permanece disponível para análise técnica,
    enquanto esta representação pode ser usada em relatórios.
    """
    if valor == "":
        return ""

    tamanho = len(valor)

    if tamanho <= 4:
        return "*" * tamanho

    if tamanho <= 8:
        return valor[:2] + ("*" * (tamanho - 4)) + valor[-2:]

    return valor[:3] + ("*" * (tamanho - 6)) + valor[-3:]


def _detectar_prefixo_cookie(nome):
    """
    Identifica prefixos especiais conhecidos em cookies.
    """
    if nome.startswith("__Host-Http-"):
        return "__Host-Http-"

    if nome.startswith("__Host-"):
        return "__Host-"

    if nome.startswith("__Secure-"):
        return "__Secure-"

    if nome.startswith("__Http-"):
        return "__Http-"

    return ""


def _converter_max_age(valor):
    """
    Converte Max-Age para inteiro quando possível.
    """
    try:
        return int(valor.strip())
    except (TypeError, ValueError):
        return None



def _detectar_formato_cookie(valor):
    """
    Identifica formatos aparentes do valor sem tentar decodificar
    ou quebrar segredos.
    """
    if not valor:
        return {
            "formato": "vazio",
            "caracteristicas": ["valor_vazio"],
        }

    caracteristicas = []

    if re.fullmatch(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
        r"[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-"
        r"[0-9a-fA-F]{12}",
        valor,
    ):
        return {
            "formato": "UUID",
            "caracteristicas": ["uuid"],
        }

    partes = valor.split(".")

    if len(partes) == 3 and all(partes):
        base64url = all(
            re.fullmatch(r"[A-Za-z0-9_-]+", parte) is not None
            for parte in partes
        )

        if base64url:
            caracteristicas.extend(
                ["tres_segmentos", "base64url_aparente"]
            )

            if partes[0] in {
                "eyJhbGciOiJIUzI1NiJ9",
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            } or valor.startswith("eyJ"):
                return {
                    "formato": "JWT",
                    "caracteristicas": caracteristicas
                    + ["jwt_aparente"],
                }

            return {
                "formato": "token_estruturado",
                "caracteristicas": caracteristicas,
            }

    if re.fullmatch(r"[0-9a-fA-F]+", valor):
        if len(valor) >= 8 and len(valor) % 2 == 0:
            return {
                "formato": "hexadecimal",
                "caracteristicas": ["hexadecimal"],
            }

    if re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", valor):
        if len(valor) >= 8:
            caracteristicas.append("base64_aparente")

    if caracteristicas:
        return {
            "formato": "base64_ou_base64url_aparente",
            "caracteristicas": caracteristicas,
        }

    if re.fullmatch(r"[A-Za-z0-9]+", valor):
        if len(valor) >= 16:
            return {
                "formato": "alfanumerico_aleatorio_aparente",
                "caracteristicas": [
                    "alfanumerico",
                    "alta_entropia_aparente",
                ],
            }

    if re.fullmatch(r"[A-Za-z0-9_-]+", valor):
        if len(valor) >= 16:
            return {
                "formato": "identificador_aleatorio_aparente",
                "caracteristicas": [
                    "identificador",
                    "alta_entropia_aparente",
                ],
            }

    if "=" in valor or "&" in valor or ":" in valor:
        return {
            "formato": "estruturado",
            "caracteristicas": ["estrutura_interna_aparente"],
        }

    return {
        "formato": "texto",
        "caracteristicas": [],
    }


def _classificar_cookie(nome, atributos):
    """
    Classifica o cookie por finalidade provável.

    A classificação é heurística e não afirma a finalidade real
    do cookie.
    """
    nome_lower = nome.lower()

    indicadores = {
        "auth": (
            "auth",
            "token",
            "access_token",
            "refresh_token",
            "id_token",
            "jwt",
            "login",
            "credential",
        ),
        "session": (
            "session",
            "sess",
            "sid",
            "jsessionid",
            "phpsessid",
            "laravel_session",
            "connect.sid",
        ),
        "csrf": (
            "csrf",
            "xsrf",
            "anti_csrf",
            "antiforgery",
        ),
        "preference": (
            "pref",
            "preference",
            "settings",
            "locale",
            "language",
            "theme",
        ),
        "analytics": (
            "analytics",
            "ga",
            "_ga",
            "_gid",
            "amplitude",
            "mixpanel",
        ),
        "tracking": (
            "track",
            "tracking",
            "visitor",
            "fingerprint",
            "ad",
            "marketing",
        ),
    }

    if any(
        termo in nome_lower
        for termo in indicadores["auth"]
    ):
        return "autenticacao", "potencialmente_auth"

    if any(
        termo in nome_lower
        for termo in indicadores["session"]
    ):
        return "sessao", "potencialmente_sessao"

    if any(
        termo in nome_lower
        for termo in indicadores["csrf"]
    ):
        return "csrf", "anti_csrf"

    if any(
        termo in nome_lower
        for termo in indicadores["preference"]
    ):
        return "preferencia", "preferencia"

    if any(
        termo in nome_lower
        for termo in indicadores["analytics"]
    ):
        return "analytics", "analytics"

    if any(
        termo in nome_lower
        for termo in indicadores["tracking"]
    ):
        return "tracking", "tracking"

    if "max-age" in atributos or "expires" in atributos:
        return "persistente", "desconhecida"

    return "sessao", "desconhecida"


def _classificar_persistencia(expires, max_age):
    """
    Determina a persistência observável do cookie.
    """
    if max_age is not None:
        if max_age <= 0:
            return "expiracao_imediata"

        return "persistente"

    if expires:
        return "persistente"

    return "sessao"


def _analisar_seguranca_cookie(
    nome,
    secure,
    httponly,
    samesite,
    dominio,
    path,
    prefixo,
    finalidade,
    max_age,
):
    """
    Gera indicadores passivos de segurança.
    """
    indicadores = []

    nome_lower = nome.lower()
    samesite_normalizado = samesite.strip().lower()

    sensivel = finalidade in {
        "potencialmente_auth",
        "potencialmente_sessao",
        "anti_csrf",
    }

    if sensivel and not httponly:
        indicadores.append(
            "cookie_potencialmente_sensivel_sem_httponly"
        )

    if sensivel and not secure:
        indicadores.append(
            "cookie_potencialmente_sensivel_sem_secure"
        )

    if samesite_normalizado == "none" and not secure:
        indicadores.append(
            "samesite_none_sem_secure"
        )

    if not samesite_normalizado:
        indicadores.append(
            "samesite_nao_informado"
        )

    if dominio:
        dominio_normalizado = dominio.lower().strip()

        if dominio_normalizado.startswith("."):
            indicadores.append(
                "dominio_explicitamente_amplo"
            )

    if prefixo == "__Host-":
        if dominio:
            indicadores.append(
                "prefixo_host_com_domain"
            )

        if path and path != "/":
            indicadores.append(
                "prefixo_host_com_path_invalido"
            )

        if not secure:
            indicadores.append(
                "prefixo_host_sem_secure"
            )

    elif prefixo == "__Secure-" and not secure:
        indicadores.append(
            "prefixo_secure_sem_secure"
        )

    if max_age is not None and max_age < 0:
        indicadores.append(
            "max_age_negativo"
        )

    if (
        "session" in nome_lower
        and not httponly
    ):
        indicadores.append(
            "nome_indica_sessao_sem_httponly"
        )

    return indicadores


def _analisar_cookie(cookie):
    """
    Completa a análise de um CookieObservado.
    """
    formato = _detectar_formato_cookie(cookie.valor)

    tipo, finalidade = _classificar_cookie(
        cookie.nome,
        cookie.atributos,
    )

    persistencia = _classificar_persistencia(
        cookie.expires,
        cookie.max_age,
    )

    if persistencia == "persistente":
        tipo = "persistente"

    elif persistencia == "sessao":
        tipo = "sessao"

    indicadores = _analisar_seguranca_cookie(
        nome=cookie.nome,
        secure=cookie.secure,
        httponly=cookie.httponly,
        samesite=cookie.samesite,
        dominio=cookie.dominio,
        path=cookie.path,
        prefixo=cookie.prefixo,
        finalidade=finalidade,
        max_age=cookie.max_age,
    )

    if (
        finalidade in {
            "potencialmente_auth",
            "potencialmente_sessao",
        }
        or formato["formato"] in {
            "JWT",
            "token_estruturado",
            "alfanumerico_aleatorio_aparente",
            "identificador_aleatorio_aparente",
        }
    ):
        sensibilidade = "potencialmente_sensivel"
    else:
        sensibilidade = "normal"

    cookie.tipo = tipo
    cookie.finalidade = finalidade
    cookie.sensibilidade = sensibilidade
    cookie.formato_valor = formato["formato"]
    cookie.caracteristicas_valor = formato["caracteristicas"]
    cookie.indicadores = indicadores

    if indicadores:
        cookie.confianca = "MEDIA"
    else:
        cookie.confianca = "ALTA"

    return cookie

def _detectar_cookies(resposta):
    """
    Extrai cookies Set-Cookie de uma resposta HTTP.

    O parser preserva:
    - nome;
    - valor completo;
    - header original;
    - URL da resposta;
    - atributos conhecidos;
    - atributos desconhecidos;
    - características básicas de segurança;
    - prefixos especiais.

    Não modifica nem tenta validar ou explorar o valor do cookie.
    """
    cookies = []

    for header in resposta.headers:
        if _normalizar_nome(header.nome) != "set-cookie":
            continue

        valor_header = header.valor.strip()

        if not valor_header:
            continue

        partes = [
            parte.strip()
            for parte in valor_header.split(";")
        ]

        if not partes:
            continue

        primeira_parte = partes[0]

        if "=" not in primeira_parte:
            continue

        nome, valor = primeira_parte.split("=", 1)

        nome = nome.strip()
        valor = valor.strip()

        if not nome:
            continue

        atributos = {}
        dominio = ""
        path = ""
        expires = ""
        max_age = None
        secure = False
        httponly = False
        samesite = ""
        priority = ""
        partitioned = False
        sameparty = False
        outros_atributos = {}

        for atributo in partes[1:]:
            atributo = atributo.strip()

            if not atributo:
                continue

            if "=" in atributo:
                chave, valor_atributo = atributo.split("=", 1)
                chave = _normalizar_nome(chave)
                valor_atributo = valor_atributo.strip()
            else:
                chave = _normalizar_nome(atributo)
                valor_atributo = True

            if not chave:
                continue

            atributos[chave] = valor_atributo

            if chave == "domain":
                dominio = str(valor_atributo)

            elif chave == "path":
                path = str(valor_atributo)

            elif chave == "expires":
                expires = str(valor_atributo)

            elif chave == "max-age":
                max_age = _converter_max_age(valor_atributo)

            elif chave == "secure":
                secure = True

            elif chave == "httponly":
                httponly = True

            elif chave == "samesite":
                samesite = str(valor_atributo)

            elif chave == "priority":
                priority = str(valor_atributo)

            elif chave == "partitioned":
                partitioned = True

            elif chave == "sameparty":
                sameparty = True

            else:
                outros_atributos[chave] = valor_atributo

        prefixo = _detectar_prefixo_cookie(nome)

        cookie = CookieObservado(
            nome=nome,
            valor=valor,
            atributos=atributos,
            url=getattr(resposta, "url", ""),
            header_original=valor_header,
            valor_mascarado=_mascarar_valor_cookie(valor),
            tamanho_valor=len(valor),
            dominio=dominio,
            path=path,
            expires=expires,
            max_age=max_age,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
            priority=priority,
            partitioned=partitioned,
            sameparty=sameparty,
            outros_atributos=outros_atributos,
            prefixo=prefixo,
        )

        _analisar_cookie(cookie)

        cookies.append(cookie)

    return cookies


def _detectar_autenticacao(headers):
    encontrados = []

    authorization = headers.get("authorization")

    if authorization:
        encontrados.append(
            {
                "tipo": "Authorization",
                "esquema": (
                    authorization.split(None, 1)[0]
                    if authorization
                    else ""
                ),
            }
        )

    www_authenticate = headers.get(
        "www-authenticate"
    )

    if www_authenticate:
        encontrados.append(
            {
                "tipo": "WWW-Authenticate",
                "valor_observado": True,
            }
        )

    return encontrados


def _detectar_tecnologias(headers):
    tecnologias = []

    servidor = headers.get("server", "")
    powered = headers.get(
        "x-powered-by",
        "",
    )

    texto = (
        f"{servidor} {powered}"
    ).lower()

    padroes = {
        "nginx": r"\bnginx\b",
        "apache": r"\bapache\b",
        "cloudflare": r"\bcloudflare\b",
        "express": r"\bexpress\b",
        "php": r"\bphp\b",
        "iis": r"\biis\b",
    }

    for nome, padrao in padroes.items():
        if re.search(padrao, texto):
            tecnologias.append(nome)

    return sorted(set(tecnologias))


def _analisar_http_bruto(resposta, headers):
    """
    Extrai metadados observáveis diretamente da resposta HTTP.

    Esta função não realiza novas requisições.
    Trabalha exclusivamente sobre a resposta já coletada.
    """

    nomes_headers = sorted(headers.keys())

    headers_x = {
        nome: valor
        for nome, valor in headers.items()
        if nome.startswith("x-")
    }

    resultado = {
        "url_final": resposta.url,
        "status_code": resposta.status_code,
        "reason": resposta.reason,
        "http_version": resposta.http_version,
        "content_type": resposta.content_type,
        "tamanho": resposta.tamanho,
        "tempo_resposta_ms": resposta.tempo_resposta_ms,
        "quantidade_headers": len(nomes_headers),
        "headers": nomes_headers,
        "headers_x": headers_x,
        "redirecionamentos": list(
            resposta.redirecionamentos
        ),
        "quantidade_redirecionamentos": len(
            resposta.redirecionamentos
        ),
        "content_length": headers.get(
            "content-length",
            "",
        ),
        "etag": headers.get(
            "etag",
            "",
        ),
        "last_modified": headers.get(
            "last-modified",
            "",
        ),
        "cache_control": headers.get(
            "cache-control",
            "",
        ),
        "age": headers.get(
            "age",
            "",
        ),
        "via": headers.get(
            "via",
            "",
        ),
        "server": headers.get(
            "server",
            "",
        ),
        "location": headers.get(
            "location",
            "",
        ),
    }

    return resultado


def _analisar_headers(headers):
    nomes = sorted(headers.keys())

    seguranca = {
        "strict_transport_security": (
            "strict-transport-security" in headers
        ),
        "content_security_policy": (
            "content-security-policy" in headers
        ),
        "x_content_type_options": (
            "x-content-type-options" in headers
        ),
        "x_frame_options": (
            "x-frame-options" in headers
        ),
        "referrer_policy": (
            "referrer-policy" in headers
        ),
    }

    ausentes = [
        nome
        for nome, presente in seguranca.items()
        if not presente
    ]

    return {
        "quantidade": len(nomes),
        "nomes": nomes,
        "cabecalhos_seguranca": seguranca,
        "indicadores_ausentes": ausentes,
    }


def _criar_evidencias(
    resposta,
    headers,
    cookies,
    json_info,
    autenticacao,
    tecnologias,
):
    evidencias = []

    if resposta.status_code >= 400:
        evidencias.append(
            Evidencia(
                identificador="HTTP-001",
                categoria="http",
                titulo="Resposta HTTP de erro",
                descricao=(
                    "Foi observada uma resposta "
                    "HTTP com código igual ou superior "
                    "a 400."
                ),
                origem="HTTP status",
                confianca="ALTA",
                detalhes={
                    "status_code": resposta.status_code
                },
            )
        )

    if json_info["detectado"]:
        evidencias.append(
            Evidencia(
                identificador="FMT-001",
                categoria="formato",
                titulo="JSON observado",
                descricao=(
                    "A resposta apresenta "
                    "indicadores compatíveis com JSON."
                ),
                origem="Content-Type/corpo",
                confianca=(
                    "ALTA"
                    if json_info["valido"]
                    else "MEDIA"
                ),
            )
        )

    if cookies:
        evidencias.append(
            Evidencia(
                identificador="SES-001",
                categoria="sessao",
                titulo="Cookie de resposta observado",
                descricao=(
                    "A resposta contém um ou mais "
                    "cookies enviados pelo servidor."
                ),
                origem="Set-Cookie",
                confianca="ALTA",
                detalhes={
                    "quantidade": len(cookies)
                },
            )
        )

    if autenticacao:
        evidencias.append(
            Evidencia(
                identificador="AUTH-001",
                categoria="autenticacao",
                titulo="Indicador de autenticação HTTP",
                descricao=(
                    "Foram observados headers associados "
                    "a mecanismos de autenticação."
                ),
                origem="Headers HTTP",
                confianca="ALTA",
            )
        )

    for tecnologia in tecnologias:
        evidencias.append(
            Evidencia(
                identificador=f"TECH-{len(evidencias)+1:03d}",
                categoria="tecnologia",
                titulo="Tecnologia indicada",
                descricao=(
                    "Um header da resposta apresenta "
                    "um indicador textual compatível "
                    f"com {tecnologia}."
                ),
                origem="Headers HTTP",
                confianca="MEDIA",
                detalhes={
                    "tecnologia": tecnologia
                },
            )
        )

    return evidencias


def analisar_resposta(resposta):
    """
    Analisa uma resposta HTTP já coletada.

    Não realiza novas conexões nem novas requisições.
    """

    headers = _headers_dict(resposta)

    json_info = _detectar_json(resposta)
    html_info = _detectar_html(resposta)
    cookies = _detectar_cookies(resposta)
    autenticacao = _detectar_autenticacao(headers)
    tecnologias = _detectar_tecnologias(headers)

    http_bruto = _analisar_http_bruto(
        resposta,
        headers,
    )

    headers_info = _analisar_headers(headers)

    evidencias = _criar_evidencias(
        resposta,
        headers,
        cookies,
        json_info,
        autenticacao,
        tecnologias,
    )

    return {
        "http": http_bruto,
        "status_code": resposta.status_code,
        "reason": resposta.reason,
        "http_version": resposta.http_version,
        "headers": headers_info,
        "html": html_info,
        "json": json_info,
        "cookies": cookies,
        "autenticacao": autenticacao,
        "tecnologias": tecnologias,
        "evidencias": evidencias,
    }
