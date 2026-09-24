import re


_FRAMEWORKS = {
    "react": {
        "padroes": [
            (
                r'\bfrom\s*["\']react["\']',
                "import",
                95,
            ),
            (
                r'\brequire\s*\(\s*["\']react["\']\s*\)',
                "require",
                95,
            ),
            (
                r'\bReactDOM\b',
                "simbolo",
                80,
            ),
            (
                r'\bReact\b',
                "simbolo",
                70,
            ),
        ],
    },
    "vue": {
        "padroes": [
            (
                r'\bfrom\s*["\']vue["\']',
                "import",
                95,
            ),
            (
                r'\brequire\s*\(\s*["\']vue["\']\s*\)',
                "require",
                95,
            ),
            (
                r'\bVue\b',
                "simbolo",
                70,
            ),
        ],
    },
    "angular": {
        "padroes": [
            (
                r'\bfrom\s*["\']@angular/',
                "import",
                95,
            ),
            (
                r'\bNgModule\b',
                "simbolo",
                85,
            ),
            (
                r'\bComponent\b',
                "simbolo",
                75,
            ),
        ],
    },
    "next.js": {
        "padroes": [
            (
                r'\bfrom\s*["\']next/',
                "import",
                95,
            ),
            (
                r'\brequire\s*\(\s*["\']next/',
                "require",
                95,
            ),
            (
                r'\bNextJS\b',
                "simbolo",
                80,
            ),
        ],
    },
    "nuxt": {
        "padroes": [
            (
                r'\bfrom\s*["\']nuxt',
                "import",
                95,
            ),
            (
                r'\brequire\s*\(\s*["\']nuxt',
                "require",
                95,
            ),
        ],
    },
    "svelte": {
        "padroes": [
            (
                r'\bfrom\s*["\']svelte',
                "import",
                95,
            ),
            (
                r'\brequire\s*\(\s*["\']svelte',
                "require",
                95,
            ),
        ],
    },
    "jquery": {
        "padroes": [
            (
                r'\bfrom\s*["\']jquery["\']',
                "import",
                95,
            ),
            (
                r'\brequire\s*\(\s*["\']jquery["\']\s*\)',
                "require",
                95,
            ),
            (
                r'\bjQuery\b',
                "simbolo",
                75,
            ),
            (
                r'\$\s*\(',
                "chamada_dollar",
                60,
            ),
        ],
    },
}


def _normalizar_linguagem(linguagem: str) -> str:
    valor = str(linguagem or "").strip().lower()

    aliases = {
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
    }

    return aliases.get(valor, valor)


def _linguagem_suportada(linguagem: str) -> bool:
    return _normalizar_linguagem(
        linguagem
    ) in {
        "javascript",
        "typescript",
    }


def _mascarar_comentarios(codigo: str) -> str:
    caracteres = list(codigo)
    tamanho = len(codigo)
    i = 0

    while i < tamanho:
        if (
            i + 1 < tamanho
            and codigo[i] == "/"
            and codigo[i + 1] == "/"
        ):
            inicio = i
            i += 2

            while i < tamanho and codigo[i] not in "\r\n":
                i += 1

            for posicao in range(inicio, i):
                if caracteres[posicao] not in "\r\n":
                    caracteres[posicao] = " "

            continue

        if (
            i + 1 < tamanho
            and codigo[i] == "/"
            and codigo[i + 1] == "*"
        ):
            inicio = i
            i += 2

            while i + 1 < tamanho:
                if (
                    codigo[i] == "*"
                    and codigo[i + 1] == "/"
                ):
                    i += 2
                    break
                i += 1

            for posicao in range(inicio, i):
                if caracteres[posicao] not in "\r\n":
                    caracteres[posicao] = " "

            continue

        i += 1

    return "".join(caracteres)


def _mascarar_strings(
    codigo: str,
) -> str:
    caracteres = list(codigo)
    tamanho = len(codigo)
    i = 0

    while i < tamanho:
        if codigo[i] not in {"'", '"', "`"}:
            i += 1
            continue

        delimitador = codigo[i]
        inicio = i
        i += 1

        while i < tamanho:
            if codigo[i] == "\\":
                i += 2
                continue

            if codigo[i] == delimitador:
                i += 1
                break

            i += 1

        for posicao in range(inicio, i):
            if caracteres[posicao] not in "\r\n":
                caracteres[posicao] = " "

    return "".join(caracteres)


def _mascarar_codigo(
    codigo: str,
) -> str:
    return _mascarar_strings(
        _mascarar_comentarios(codigo)
    )


def _esta_em_importacao(
    codigo_mascarado: str,
    inicio: int,
) -> bool:
    inicio_linha = codigo_mascarado.rfind(
        "\n",
        0,
        inicio,
    ) + 1

    fim_linha = codigo_mascarado.find(
        "\n",
        inicio,
    )

    if fim_linha == -1:
        fim_linha = len(codigo_mascarado)

    linha = codigo_mascarado[
        inicio_linha:fim_linha
    ]

    return bool(
        re.match(
            r"\s*import\b.*\bfrom\b",
            linha,
            flags=re.IGNORECASE,
        )
        or re.match(
            r"\s*(?:const|let|var)\s+\w+\s*=\s*require\s*\(",
            linha,
            flags=re.IGNORECASE,
        )
    )


def _esta_em_string(
    codigo_mascarado: str,
    inicio: int,
) -> bool:
    if inicio >= len(codigo_mascarado):
        return False

    return codigo_mascarado[inicio] == " "


def _localizacao(
    codigo: str,
    inicio: int,
) -> dict[str, int]:
    linha = codigo.count(
        "\n",
        0,
        inicio,
    ) + 1

    ultimo_quebra = codigo.rfind(
        "\n",
        0,
        inicio,
    )

    coluna = (
        inicio + 1
        if ultimo_quebra == -1
        else inicio - ultimo_quebra
    )

    return {
        "linha": linha,
        "coluna": coluna,
    }


def _evidencia(
    codigo: str,
    inicio: int,
    fim: int,
    padrao: str,
) -> str:
    inicio_linha = codigo.rfind(
        "\n",
        0,
        inicio,
    ) + 1

    fim_linha = codigo.find(
        "\n",
        fim,
    )

    if fim_linha == -1:
        fim_linha = len(codigo)

    linha = codigo[
        inicio_linha:fim_linha
    ].strip()

    if linha:
        return linha

    return padrao


def _confianca(
    pontuacao: int,
) -> str:
    if pontuacao >= 90:
        return "ALTA"

    if pontuacao >= 75:
        return "MEDIA"

    return "BAIXA"


def _criar_observacao(
    framework: str,
    tipo: str,
    pontuacao: int,
    codigo: str,
    inicio: int,
    fim: int,
    padrao: str,
    origem: str,
    arquivo: str,
    linguagem: str,
) -> dict:
    return {
        "framework": framework,
        "origem": origem,
        "arquivo": arquivo,
        "tipo": tipo,
        "localizacao": _localizacao(
            codigo,
            inicio,
        ),
        "evidencias": [
            {
                "tipo": tipo,
                "valor": _evidencia(
                    codigo,
                    inicio,
                    fim,
                    padrao,
                ),
            }
        ],
        "pontuacao": pontuacao,
        "confianca": _confianca(
            pontuacao
        ),
        "linguagem": _normalizar_linguagem(
            linguagem
        ),
    }


def detectar_frameworks_html(
    tecnologias,
    origem: str = "html",
    arquivo: str = "",
):
    """
    Converte tecnologias frontend já detectadas pelo analisador HTML
    em observações estruturadas de framework.

    Não executa novas detecções nem duplica as regras do analisador HTML.
    Apenas reaproveita as evidências existentes em HTMLAnalise.tecnologias.
    """
    resultado = []

    if not isinstance(tecnologias, list):
        return resultado

    frameworks_suportados = {
        "react",
        "vue",
        "angular",
        "next.js",
        "nuxt",
    }

    for tecnologia in tecnologias:
        if not isinstance(tecnologia, dict):
            continue

        if tecnologia.get("categoria") != "frontend_framework":
            continue

        framework = str(
            tecnologia.get("nome", "")
        ).strip().lower()

        if framework not in frameworks_suportados:
            continue

        confianca = str(
            tecnologia.get(
                "confianca",
                "BAIXA",
            )
        ).strip().upper()

        pontuacao = {
            "ALTA": 95,
            "MEDIA": 75,
            "BAIXA": 60,
        }.get(
            confianca,
            60,
        )

        resultado.append(
            {
                "framework": framework,
                "origem": origem,
                "arquivo": arquivo,
                "tipo": "html",
                "localizacao": {
                    "linha": 0,
                    "coluna": 0,
                },
                "evidencias": [
                    tecnologia.get(
                        "evidencia",
                        "texto_html",
                    )
                ],
                "pontuacao": pontuacao,
                "confianca": confianca,
                "linguagem": "html",
            }
        )

    return resultado

def detectar_frameworks(
    codigo: str,
    origem: str = "",
    arquivo: str = "",
    linguagem: str = "javascript",
) -> list[dict]:
    if not codigo:
        return []

    if not _linguagem_suportada(
        linguagem
    ):
        return []

    codigo_sem_comentarios = _mascarar_comentarios(
        codigo
    )

    codigo_mascarado = _mascarar_codigo(
        codigo
    )

    observacoes = []
    vistos = set()
    evidencias_fortes = set()

    for framework, dados in _FRAMEWORKS.items():
        for padrao, tipo, pontuacao in dados[
            "padroes"
        ]:
            codigo_para_busca = (
                codigo_sem_comentarios
                if tipo in {
                    "import",
                    "require",
                }
                else codigo_mascarado
            )

            for correspondencia in re.finditer(
                padrao,
                codigo_para_busca,
                flags=re.IGNORECASE,
            ):
                inicio = correspondencia.start()
                fim = correspondencia.end()

                if tipo in {
                    "import",
                    "require",
                } and _esta_em_string(
                    codigo_mascarado,
                    inicio,
                ):
                    continue

                if tipo in {
                    "simbolo",
                    "chamada_dollar",
                } and _esta_em_importacao(
                    codigo_mascarado,
                    inicio,
                ):
                    continue

                chave = (
                    framework,
                    tipo,
                    inicio,
                )

                if chave in vistos:
                    continue

                if (
                    tipo in {"simbolo", "chamada_dollar"}
                    and framework in evidencias_fortes
                ):
                    continue

                vistos.add(chave)

                observacao = _criar_observacao(
                    framework=framework,
                    tipo=tipo,
                    pontuacao=pontuacao,
                    codigo=codigo,
                    inicio=inicio,
                    fim=fim,
                    padrao=padrao,
                    origem=origem,
                    arquivo=arquivo,
                    linguagem=linguagem,
                )

                observacoes.append(observacao)

                if tipo in {"import", "require"}:
                    evidencias_fortes.add(framework)

    observacoes.sort(
        key=lambda item: (
            item["localizacao"]["linha"],
            item["localizacao"]["coluna"],
            item["framework"],
            item["tipo"],
        )
    )

    return observacoes
