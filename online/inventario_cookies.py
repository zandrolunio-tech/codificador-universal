from __future__ import annotations

from dataclasses import asdict
from urllib.parse import urlparse


def _host_da_url(url: str) -> str:
    """Obtém o host observado na URL, sem realizar conexão."""
    if not url:
        return ""

    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def _dominio_efetivo(cookie) -> str:
    """
    Obtém o domínio usado para identidade do cookie.

    Quando Domain não foi informado, utiliza o host da URL
    onde o cookie foi observado.
    """
    dominio = str(getattr(cookie, "dominio", "") or "").strip()

    if dominio:
        return dominio.lower()

    return _host_da_url(
        str(getattr(cookie, "url", "") or "")
    )


def _chave_cookie(cookie) -> tuple[str, str, str]:
    """
    Identidade lógica do cookie:

        nome + domínio + path
    """
    nome = str(
        getattr(cookie, "nome", "") or ""
    ).strip().lower()

    dominio = _dominio_efetivo(cookie)

    path = str(
        getattr(cookie, "path", "") or "/"
    ).strip()

    return nome, dominio, path


def _ocorrencia_cookie(cookie, indice_resposta: int, resposta):
    """Converte uma observação em histórico técnico."""
    return {
        "indice_resposta": indice_resposta,
        "url": str(
            getattr(cookie, "url", "")
            or getattr(resposta, "url", "")
            or ""
        ),
        "status_code": getattr(
            resposta,
            "status_code",
            None,
        ),
        "header_original": str(
            getattr(cookie, "header_original", "")
            or ""
        ),
    }


def _item_cookie(cookie):
    """Serializa um CookieObservado sem perder informações."""
    item = asdict(cookie)

    # Ocorrências são mantidas separadamente no inventário.
    item.pop("ocorrencias", None)

    return item


def _adicionar_ocorrencia(
    ocorrencias: list[dict],
    ocorrencia: dict,
):
    """
    Adiciona uma ocorrência sem duplicar exatamente a mesma
    observação.
    """
    assinatura = (
        ocorrencia.get("indice_resposta"),
        ocorrencia.get("url"),
        ocorrencia.get("header_original"),
    )

    for existente in ocorrencias:
        assinatura_existente = (
            existente.get("indice_resposta"),
            existente.get("url"),
            existente.get("header_original"),
        )

        if assinatura_existente == assinatura:
            return

    ocorrencias.append(ocorrencia)


def construir_inventario_cookies(
    respostas: list,
    analises: list[dict],
) -> dict:
    """
    Consolida cookies observados nas respostas HTTP.

    Não realiza novas conexões nem modifica cookies.
    """
    itens_por_chave = {}
    ocorrencias = []

    for indice_resposta, (resposta, analise) in enumerate(
        zip(respostas, analises)
    ):
        cookies = analise.get("cookies", [])

        for cookie in cookies:
            chave = _chave_cookie(cookie)

            if chave not in itens_por_chave:
                item = _item_cookie(cookie)
                item["dominio_efetivo"] = _dominio_efetivo(
                    cookie
                )
                item["ocorrencias"] = []
                itens_por_chave[chave] = item

            ocorrencia = _ocorrencia_cookie(
                cookie,
                indice_resposta,
                resposta,
            )

            _adicionar_ocorrencia(
                itens_por_chave[chave]["ocorrencias"],
                ocorrencia,
            )

            ocorrencia_global = dict(ocorrencia)
            ocorrencia_global["cookie"] = (
                itens_por_chave[chave]["nome"]
            )
            ocorrencia_global["dominio"] = (
                itens_por_chave[chave]["dominio_efetivo"]
            )
            ocorrencia_global["path"] = (
                itens_por_chave[chave]["path"]
            )

            _adicionar_ocorrencia(
                ocorrencias,
                ocorrencia_global,
            )

    itens = list(itens_por_chave.values())

    resumo = {
        "total": sum(
            len(item["ocorrencias"])
            for item in itens
        ),
        "unicos": len(itens),
        "sessao": sum(
            1
            for item in itens
            if item.get("tipo") == "sessao"
        ),
        "persistentes": sum(
            1
            for item in itens
            if item.get("tipo") == "persistente"
        ),
        "secure": sum(
            1
            for item in itens
            if item.get("secure") is True
        ),
        "httponly": sum(
            1
            for item in itens
            if item.get("httponly") is True
        ),
        "samesite": sum(
            1
            for item in itens
            if item.get("samesite")
        ),
        "potencialmente_sensiveis": sum(
            1
            for item in itens
            if item.get("sensibilidade")
            == "potencialmente_sensivel"
        ),
        "riscos": sum(
            len(item.get("indicadores", []))
            for item in itens
        ),
    }

    return {
        "resumo": resumo,
        "itens": itens,
        "ocorrencias": ocorrencias,
    }
