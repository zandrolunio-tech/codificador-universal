from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import re

from online.modelos import HTMLAnalise


_ELEMENTOS_IMPORTANTES = {
    "iframe",
    "object",
    "embed",
    "base",
    "form",
    "input",
    "script",
    "style",
    "link",
    "img",
    "video",
    "audio",
    "source",
    "template",
    "noscript",
}

_RECURSOS = {
    "script": "javascript",
    "link": "link",
    "img": "imagem",
    "video": "video",
    "audio": "audio",
    "source": "media",
    "iframe": "iframe",
    "object": "object",
    "embed": "embed",
}


def _atributos_dict(attrs):
    return {
        str(nome).lower(): (valor if valor is not None else "")
        for nome, valor in attrs
    }


def _url_absoluta(referencia: str, base_url: str) -> str:
    if not referencia:
        return ""

    try:
        return urljoin(base_url, referencia)
    except ValueError:
        return referencia


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except ValueError:
        return ""


def _eh_externa(url: str, base_url: str) -> bool:
    try:
        alvo = urlparse(url)
        base = urlparse(base_url)

        if not alvo.netloc or not base.netloc:
            return False

        return alvo.netloc.lower() != base.netloc.lower()
    except ValueError:
        return False


def _origem_recurso(url: str, base_url: str) -> str:
    """
    Classifica a origem observada de um recurso.

    A classificacao e estatica e nao realiza qualquer requisicao.
    """
    if not url:
        return "desconhecida"

    try:
        alvo = urlparse(url)
        base = urlparse(base_url)

        if alvo.scheme in {"data", "blob"}:
            return alvo.scheme

        if not alvo.netloc:
            return "relativa"

        if not base.netloc:
            return "externa"

        if alvo.netloc.lower() == base.netloc.lower():
            return "mesma_origem"

        return "externa"

    except ValueError:
        return "desconhecida"


def _recurso(
    tipo: str,
    elemento: str,
    referencia: str,
    base_url: str,
    atributos: dict[str, str] | None = None,
) -> dict:
    """
    Cria uma entrada padronizada no inventario de recursos.

    Nenhum recurso e acessado; somente a referencia presente no HTML
    e normalizada.
    """
    absoluto = _url_absoluta(referencia, base_url)

    return {
        "tipo": tipo,
        "elemento": elemento,
        "referencia": referencia,
        "url": absoluto,
        "host": _host(absoluto),
        "origem": _origem_recurso(absoluto, base_url),
        "externo": _eh_externa(absoluto, base_url),
        "atributos": dict(atributos or {}),
    }


def _extrair_charset(content_type: str, html: str) -> str:
    encontrado = re.search(
        r"charset\s*=\s*['\"]?([A-Za-z0-9._:-]+)",
        content_type,
        re.IGNORECASE,
    )

    if encontrado:
        return encontrado.group(1)

    encontrado = re.search(
        r"<meta\b[^>]*charset\s*=\s*['\"]?([^'\"\s/>]+)",
        html,
        re.IGNORECASE,
    )

    if encontrado:
        return encontrado.group(1)

    encontrado = re.search(
        r"<meta\b[^>]*content\s*=\s*['\"][^'\"]*charset\s*=\s*"
        r"([A-Za-z0-9._:-]+)",
        html,
        re.IGNORECASE,
    )

    if encontrado:
        return encontrado.group(1)

    return ""


def _detectar_doctype(html: str) -> str:
    encontrado = re.search(
        r"<!DOCTYPE\s+([^>]+)>",
        html,
        re.IGNORECASE,
    )

    if encontrado:
        return encontrado.group(1).strip()

    return ""


def _classificar_campo(attrs: dict[str, str]) -> str:
    valores = " ".join(
        [
            attrs.get("name", ""),
            attrs.get("id", ""),
            attrs.get("type", ""),
            attrs.get("autocomplete", ""),
            attrs.get("placeholder", ""),
        ]
    ).lower()

    if any(
        termo in valores
        for termo in (
            "password",
            "senha",
        )
    ):
        return "login"

    if any(
        termo in valores
        for termo in (
            "email",
            "username",
            "user",
            "login",
        )
    ):
        return "login"

    if any(
        termo in valores
        for termo in (
            "search",
            "pesquisa",
        )
    ):
        return "pesquisa"

    if any(
        termo in valores
        for termo in (
            "upload",
            "file",
        )
    ):
        return "upload"

    if any(
        termo in valores
        for termo in (
            "card",
            "payment",
            "pagamento",
            "billing",
        )
    ):
        return "pagamento"

    if any(
        termo in valores
        for termo in (
            "register",
            "signup",
            "registro",
        )
    ):
        return "registro"

    if any(
        termo in valores
        for termo in (
            "contact",
            "contato",
        )
    ):
        return "contato"

    return "desconhecido"


def _criar_evidencia(
    tipo: str,
    origem: str,
    url: str,
    indicador: str,
    descricao: str,
    confianca: str = "MEDIA",
) -> dict:
    return {
        "tipo": tipo,
        "origem": origem,
        "url": url,
        "indicador": indicador,
        "descricao": descricao,
        "confianca": confianca,
    }


class _HTMLParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)

        self.base_url = base_url
        self.resultado = HTMLAnalise(url=base_url)

        self._profundidade = 0
        self._profundidade_maxima = 0
        self._stack = []

        self._em_title = False
        self._titulo_partes = []

        self._formulario_atual = None
        self._script_atual = None
        self._style_atual = None

        self._texto_acumulado = []

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype"):
            self.resultado.doctype = decl[7:].strip()

    def handle_comment(self, data):
        self.resultado.comentarios.append(data)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        atributos = _atributos_dict(attrs)

        self.resultado.estatisticas["elementos"] = (
            self.resultado.estatisticas.get("elementos", 0) + 1
        )

        if tag in _ELEMENTOS_IMPORTANTES:
            self.resultado.elementos_importantes.append(
                {
                    "elemento": tag,
                    "atributos": atributos,
                }
            )

        self._profundidade += 1
        self._profundidade_maxima = max(
            self._profundidade_maxima,
            self._profundidade,
        )

        self._stack.append(tag)

        if tag == "html":
            self.resultado.lang = atributos.get("lang", "")

        if tag == "title":
            self._em_title = True
            self._titulo_partes = []

        if tag == "meta":
            meta = {
                "atributos": atributos,
            }

            if "charset" in atributos:
                meta["charset"] = atributos["charset"]

            if "name" in atributos:
                meta["name"] = atributos["name"]

            if "content" in atributos:
                meta["content"] = atributos["content"]

            self.resultado.metas.append(meta)

        if tag == "link":
            referencia = atributos.get("href", "")
            absoluto = _url_absoluta(referencia, self.base_url)

            item = {
                "tipo": "link",
                "href": referencia,
                "url": absoluto,
                "host": _host(absoluto),
                "externo": _eh_externa(absoluto, self.base_url),
                "atributos": atributos,
            }

            rel = atributos.get("rel", "").lower()

            if "stylesheet" in rel:
                self.resultado.estilos.append(item)
                self.resultado.recursos.append(
                    _recurso(
                        "css",
                        "link",
                        referencia,
                        self.base_url,
                        atributos,
                    )
                )
            elif "icon" in rel or "shortcut icon" in rel:
                item["tipo"] = "favicon"
            elif "manifest" in rel:
                item["tipo"] = "manifest"
                self.resultado.recursos.append(
                    _recurso(
                        "manifest",
                        "link",
                        referencia,
                        self.base_url,
                        atributos,
                    )
                )
            elif "canonical" in rel:
                item["tipo"] = "canonical"
            elif "alternate" in rel:
                item["tipo"] = "alternate"

            self.resultado.links.append(item)

            rel_tokens = {
                token.strip().lower()
                for token in rel.split()
            }

            tipo_recurso = (
                atributos.get("type", "").lower()
            )

            if (
                atributos.get("as", "").lower() == "font"
                or "font/" in tipo_recurso
                or "font" in rel_tokens
            ):
                self.resultado.recursos.append(
                    _recurso(
                        "fonte",
                        "link",
                        referencia,
                        self.base_url,
                        atributos,
                    )
                )

            if "preload" in rel_tokens:
                tipo_preload = (
                    atributos.get("as", "").lower()
                    or tipo_recurso
                    or "preload"
                )

                if tipo_preload == "font":
                    pass
                else:
                    self.resultado.recursos.append(
                        _recurso(
                            tipo_preload,
                            "link",
                            referencia,
                            self.base_url,
                            atributos,
                        )
                    )

        if tag == "a":
            referencia = atributos.get("href", "")
            absoluto = _url_absoluta(
                referencia,
                self.base_url,
            )

            self.resultado.links.append(
                {
                    "tipo": "navegacao",
                    "href": referencia,
                    "url": absoluto,
                    "host": _host(absoluto),
                    "externo": _eh_externa(
                        absoluto,
                        self.base_url,
                    ),
                    "protocolo": (
                        absoluto.split(":", 1)[0]
                        if ":" in absoluto
                        else ""
                    ),
                    "atributos": atributos,
                }
            )

        if tag == "script":
            referencia = atributos.get("src", "")
            absoluto = _url_absoluta(referencia, self.base_url)

            item = {
                "tipo": "externo" if referencia else "inline",
                "src": referencia,
                "url": absoluto,
                "host": _host(absoluto),
                "externo": _eh_externa(absoluto, self.base_url),
                "atributos": atributos,
                "tamanho_inline": 0,
            }

            self.resultado.scripts.append(item)

            if referencia:
                self.resultado.recursos.append(
                    _recurso(
                        "javascript",
                        "script",
                        referencia,
                        self.base_url,
                        atributos,
                    )
                )

            self._script_atual = {
                "item": item,
                "partes": [],
            }

        if tag == "style":
            self._style_atual = {
                "partes": [],
                "atributos": atributos,
            }

        if tag == "img":
            referencia = atributos.get("src", "")
            absoluto = _url_absoluta(referencia, self.base_url)

            self.resultado.imagens.append(
                {
                    "src": referencia,
                    "url": absoluto,
                    "host": _host(absoluto),
                    "externo": _eh_externa(absoluto, self.base_url),
                    "atributos": atributos,
                }
            )

            self.resultado.recursos.append(
                _recurso(
                    "imagem",
                    "img",
                    referencia,
                    self.base_url,
                    atributos,
                )
            )

        if tag == "iframe":
            referencia = atributos.get("src", "")
            absoluto = _url_absoluta(referencia, self.base_url)

            self.resultado.iframes.append(
                {
                    "src": referencia,
                    "url": absoluto,
                    "host": _host(absoluto),
                    "externo": _eh_externa(absoluto, self.base_url),
                    "atributos": atributos,
                }
            )

            self.resultado.recursos.append(
                _recurso(
                    "iframe",
                    "iframe",
                    referencia,
                    self.base_url,
                    atributos,
                )
            )

        if tag in {"video", "audio", "source", "object", "embed"}:
            referencia = (
                atributos.get("src", "")
                or atributos.get("data", "")
            )

            self.resultado.recursos.append(
                _recurso(
                    _RECURSOS.get(tag, tag),
                    tag,
                    referencia,
                    self.base_url,
                    atributos,
                )
            )

        if tag == "form":
            referencia = atributos.get("action", "")
            absoluto = _url_absoluta(referencia, self.base_url)

            formulario = {
                "action": referencia,
                "url": absoluto,
                "method": atributos.get("method", ""),
                "enctype": atributos.get("enctype", ""),
                "target": atributos.get("target", ""),
                "autocomplete": atributos.get("autocomplete", ""),
                "externo": _eh_externa(absoluto, self.base_url),
                "atributos": atributos,
                "campos": [],
                "classificacao": "desconhecido",
            }

            self.resultado.formularios.append(formulario)
            self._formulario_atual = formulario

        if tag in {"input", "textarea", "select", "button"}:
            campo = {
                "elemento": tag,
                "name": atributos.get("name", ""),
                "id": atributos.get("id", ""),
                "type": atributos.get("type", ""),
                "value": atributos.get("value", ""),
                "placeholder": atributos.get("placeholder", ""),
                "required": "required" in atributos,
                "autocomplete": atributos.get("autocomplete", ""),
                "atributos": atributos,
                "classificacao": _classificar_campo(atributos),
            }

            self.resultado.campos_formulario.append(campo)

            if self._formulario_atual is not None:
                self._formulario_atual["campos"].append(campo)

        if tag == "base":
            referencia = atributos.get("href", "")
            self.resultado.indicadores.append(
                {
                    "tipo": "base",
                    "valor": referencia,
                    "confianca": "ALTA",
                }
            )

        if "hidden" in atributos or atributos.get("type", "").lower() == "hidden":
            self.resultado.elementos_ocultos.append(
                {
                    "elemento": tag,
                    "atributos": atributos,
                }
            )

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self._stack:
            self._stack.pop()
        self._profundidade = max(0, self._profundidade - 1)

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag == "title":
            self._em_title = False
            self.resultado.titulo = "".join(
                self._titulo_partes
            ).strip()

        if tag == "script" and self._script_atual is not None:
            conteudo = "".join(self._script_atual["partes"])
            self._script_atual["item"]["tamanho_inline"] = len(
                conteudo
            )
            self._script_atual = None

        if tag == "style" and self._style_atual is not None:
            conteudo = "".join(self._style_atual["partes"])

            self.resultado.estilos.append(
                {
                    "tipo": "inline",
                    "tamanho": len(conteudo),
                    "atributos": self._style_atual["atributos"],
                }
            )

            self._style_atual = None

        if tag == "form":
            self._formulario_atual = None

        if self._stack:
            if self._stack[-1] == tag:
                self._stack.pop()
            elif tag in self._stack:
                while self._stack:
                    ultimo = self._stack.pop()
                    if ultimo == tag:
                        break

        self._profundidade = max(0, self._profundidade - 1)

    def handle_data(self, data):
        if self._em_title:
            self._titulo_partes.append(data)

        if self._script_atual is not None:
            self._script_atual["partes"].append(data)

        if self._style_atual is not None:
            self._style_atual["partes"].append(data)

    def finalizar(self):
        self.resultado.profundidade = self._profundidade_maxima


def analisar_html(
    html: str,
    url: str = "",
    content_type: str = "",
) -> HTMLAnalise:
    resultado = HTMLAnalise(
        url=url,
        content_type=content_type,
        tamanho=len(html),
        detectado=bool(
            "<html" in html.lower()
            or "<!doctype html" in html.lower()
            or "text/html" in content_type.lower()
        ),
    )

    if not resultado.detectado:
        resultado.valido = False
        return resultado

    resultado.charset = _extrair_charset(content_type, html)
    resultado.doctype = _detectar_doctype(html)

    parser = _HTMLParser(url)

    try:
        parser.feed(html)
        parser.close()
        parser.finalizar()

        resultado = parser.resultado
        resultado.content_type = content_type
        resultado.tamanho = len(html)
        resultado.detectado = True
        resultado.charset = (
            resultado.charset
            or _extrair_charset(content_type, html)
        )
        resultado.doctype = (
            resultado.doctype
            or _detectar_doctype(html)
        )
        resultado.valido = True

    except Exception as exc:
        resultado.valido = False
        resultado.observacoes.append(
            f"Falha durante análise estática do HTML: {exc}"
        )

    _finalizar_estatisticas(resultado)
    _detectar_indicadores(resultado)
    _detectar_seguranca(resultado)
    _detectar_dados_potencialmente_sensiveis(
        resultado,
        html,
    )

    return resultado


def _finalizar_estatisticas(resultado: HTMLAnalise):
    resultado.estatisticas = {
        "elementos": resultado.estatisticas.get(
            "elementos",
            0,
        ),
        "scripts": len(resultado.scripts),
        "scripts_inline": sum(
            1
            for item in resultado.scripts
            if item.get("tipo") == "inline"
        ),
        "scripts_externos": sum(
            1
            for item in resultado.scripts
            if item.get("tipo") == "externo"
        ),
        "links": len(resultado.links),
        "links_externos": sum(
            1
            for item in resultado.links
            if item.get("externo")
        ),
        "imagens": len(resultado.imagens),
        "iframes": len(resultado.iframes),
        "formularios": len(resultado.formularios),
        "campos_formulario": len(
            resultado.campos_formulario
        ),
        "metas": len(resultado.metas),
        "recursos": len(resultado.recursos),
        "comentarios": len(resultado.comentarios),
        "indicadores": len(resultado.indicadores),
    }


def _adicionar_indicador(
    resultado: HTMLAnalise,
    tipo: str,
    valor: str,
    confianca: str = "MEDIA",
):
    resultado.indicadores.append(
        {
            "tipo": tipo,
            "valor": valor,
            "confianca": confianca,
        }
    )


def _detectar_indicadores(resultado: HTMLAnalise):
    for item in resultado.metas:
        nome = item.get("name", "").lower()
        content = item.get("content", "")

        if nome in {
            "description",
            "keywords",
            "robots",
            "author",
            "viewport",
        }:
            _adicionar_indicador(
                resultado,
                f"meta:{nome}",
                content,
                "ALTA",
            )

        propriedade = item.get(
            "atributos",
            {},
        ).get("property", "").lower()

        if propriedade.startswith("og:"):
            _adicionar_indicador(
                resultado,
                "open_graph",
                propriedade,
                "ALTA",
            )

        if propriedade.startswith("twitter:"):
            _adicionar_indicador(
                resultado,
                "twitter_card",
                propriedade,
                "ALTA",
            )

    for item in resultado.links:
        tipo = item.get("tipo", "")

        if tipo in {
            "canonical",
            "manifest",
            "favicon",
            "alternate",
        }:
            _adicionar_indicador(
                resultado,
                tipo,
                item.get("url", ""),
                "ALTA",
            )

        rel = item.get(
            "atributos",
            {},
        ).get("rel", "").lower()

        if "preconnect" in rel:
            _adicionar_indicador(
                resultado,
                "preconnect",
                item.get("url", ""),
                "ALTA",
            )

        if "dns-prefetch" in rel:
            _adicionar_indicador(
                resultado,
                "dns-prefetch",
                item.get("url", ""),
                "ALTA",
            )

        if "preload" in rel:
            _adicionar_indicador(
                resultado,
                "preload",
                item.get("url", ""),
                "ALTA",
            )

    for script in resultado.scripts:
        attrs = script.get("atributos", {})
        texto = " ".join(
            [
                attrs.get("type", ""),
                attrs.get("src", ""),
            ]
        ).lower()

        if "module" in texto:
            _adicionar_indicador(
                resultado,
                "javascript_module",
                script.get("url", ""),
                "ALTA",
            )

        src = attrs.get("src", "").lower()

        if any(
            termo in src
            for termo in (
                "google-analytics",
                "googletagmanager",
                "gtag",
                "facebook.net",
                "hotjar",
            )
        ):
            _adicionar_indicador(
                resultado,
                "analytics",
                script.get("url", ""),
                "MEDIA",
            )

    html_recursos = resultado.recursos

    for recurso in html_recursos:
        url = recurso.get("url", "").lower()

        if any(
            termo in url
            for termo in (
                "cloudfront",
                "cloudflare",
                "akamai",
                "fastly",
            )
        ):
            _adicionar_indicador(
                resultado,
                "cdn",
                recurso.get("url", ""),
                "MEDIA",
            )

    texto_indicadores = " ".join(
        [
            resultado.titulo,
            resultado.lang,
            " ".join(
                str(item)
                for item in resultado.comentarios
            ),
        ]
    ).lower()

    tecnologias = {
        "react": "frontend_framework",
        "vue": "frontend_framework",
        "angular": "frontend_framework",
        "next.js": "frontend_framework",
        "nuxt": "frontend_framework",
        "wordpress": "cms",
        "drupal": "cms",
        "joomla": "cms",
    }

    for termo, categoria in tecnologias.items():
        if termo in texto_indicadores:
            resultado.tecnologias.append(
                {
                    "nome": termo,
                    "categoria": categoria,
                    "evidencia": "texto_html",
                    "confianca": "BAIXA",
                }
            )


def _detectar_seguranca(resultado: HTMLAnalise):
    for formulario in resultado.formularios:
        method = formulario.get("method", "").strip().lower()
        action = formulario.get("url", "")
        attrs = formulario.get("atributos", {})

        if not method:
            resultado.indicadores.append(
                {
                    "tipo": "formulario_sem_method_explicito",
                    "valor": action,
                    "confianca": "ALTA",
                }
            )

        if action.lower().startswith("http://"):
            resultado.indicadores.append(
                {
                    "tipo": "formulario_http",
                    "valor": action,
                    "confianca": "ALTA",
                }
            )

        if "autocomplete" in attrs:
            resultado.indicadores.append(
                {
                    "tipo": "autocomplete",
                    "valor": attrs.get("autocomplete", ""),
                    "confianca": "ALTA",
                }
            )

    for item in (
        resultado.scripts
        + resultado.links
        + resultado.imagens
        + resultado.iframes
        + resultado.recursos
    ):
        url = item.get("url", "")

        if url.lower().startswith("http://"):
            resultado.indicadores.append(
                {
                    "tipo": "recurso_http",
                    "valor": url,
                    "confianca": "ALTA",
                }
            )

        attrs = item.get("atributos", {})

        for atributo in (
            "integrity",
            "sandbox",
            "referrerpolicy",
            "crossorigin",
        ):
            if atributo in attrs:
                resultado.indicadores.append(
                    {
                        "tipo": atributo,
                        "valor": attrs.get(atributo, ""),
                        "confianca": "ALTA",
                    }
                )


def _detectar_dados_potencialmente_sensiveis(
    resultado: HTMLAnalise,
    html: str,
):
    padroes = {
        "email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "jwt_aparente": (
            r"\beyJ[A-Za-z0-9_-]+\."
            r"[A-Za-z0-9_-]+\."
            r"[A-Za-z0-9_-]+\b"
        ),
    }

    for tipo, padrao in padroes.items():
        encontrados = re.findall(
            padrao,
            html,
            re.IGNORECASE,
        )

        vistos = set()

        for valor in encontrados:
            if valor in vistos:
                continue

            vistos.add(valor)

            mascarado = valor

            if tipo == "email":
                partes = valor.split("@", 1)
                if len(partes) == 2:
                    usuario, dominio = partes
                    mascarado = (
                        (usuario[:1] + "***")
                        + "@"
                        + dominio
                    )

            elif tipo == "jwt_aparente":
                mascarado = "[JWT_APARENTE_MASCARADO]"

            resultado.dados_potencialmente_sensiveis.append(
                {
                    "tipo": tipo,
                    "valor": mascarado,
                    "origem": "html",
                    "mascarado": True,
                }
            )

            resultado.evidencias.append(
                _criar_evidencia(
                    tipo="dado_potencialmente_sensivel",
                    origem="html",
                    url=resultado.url,
                    indicador=tipo,
                    descricao=(
                        "Estrutura potencialmente sensível "
                        "identificada no HTML."
                    ),
                    confianca="MEDIA",
                )
            )
