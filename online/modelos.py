from dataclasses import dataclass, field
from typing import Any


@dataclass
class HTTPHeader:
    nome: str
    valor: str


@dataclass
class HTTPResposta:
    url: str
    status_code: int
    reason: str
    http_version: str
    headers: list[HTTPHeader] = field(default_factory=list)
    content_type: str = ""
    tamanho: int = 0
    corpo: str = ""
    tempo_resposta_ms: float = 0.0
    redirecionamentos: list[str] = field(default_factory=list)


@dataclass
class CookieObservado:
    nome: str
    valor: str = ""
    atributos: dict[str, Any] = field(default_factory=dict)

    # Origem da observação
    url: str = ""
    header_original: str = ""

    # Informações do valor
    valor_mascarado: str = ""
    tamanho_valor: int = 0

    # Atributos normalizados
    dominio: str = ""
    path: str = ""
    expires: str = ""
    max_age: int | None = None
    secure: bool = False
    httponly: bool = False
    samesite: str = ""
    priority: str = ""
    partitioned: bool = False
    sameparty: bool = False
    outros_atributos: dict[str, Any] = field(default_factory=dict)

    # Classificação
    tipo: str = ""
    finalidade: str = ""
    sensibilidade: str = ""
    confianca: str = ""

    # Formato aparente do valor
    formato_valor: str = ""
    caracteristicas_valor: list[str] = field(default_factory=list)

    # Prefixos especiais
    prefixo: str = ""

    # Indicadores de segurança/análise
    indicadores: list[str] = field(default_factory=list)

    # Histórico da observação
    ocorrencias: list[dict[str, Any]] = field(default_factory=list)

    # Evidências técnicas
    evidencias: list[dict[str, Any]] = field(default_factory=list)



@dataclass
class JavaScriptExtraido:
    origem: str
    tipo: str
    url: str = ""
    conteudo: str = ""
    atributos: dict[str, str] = field(default_factory=dict)


@dataclass
class JavaScriptAnalise:
    detectado: bool = False
    tamanho: int = 0
    funcoes: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    endpoints: list[str] = field(default_factory=list)
    websockets: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    apis: dict[str, list[str]] = field(
        default_factory=dict
    )
    caracteristicas: dict[str, bool] = field(
        default_factory=dict
    )

@dataclass
class HTMLAnalise:
    url: str = ""
    content_type: str = ""
    tamanho: int = 0
    charset: str = ""
    detectado: bool = False
    valido: bool | None = None
    titulo: str = ""
    lang: str = ""
    doctype: str = ""
    profundidade: int = 0

    metas: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)
    scripts: list[dict[str, Any]] = field(default_factory=list)
    estilos: list[dict[str, Any]] = field(default_factory=list)
    imagens: list[dict[str, Any]] = field(default_factory=list)
    iframes: list[dict[str, Any]] = field(default_factory=list)
    formularios: list[dict[str, Any]] = field(default_factory=list)
    campos_formulario: list[dict[str, Any]] = field(default_factory=list)
    recursos: list[dict[str, Any]] = field(default_factory=list)
    elementos_importantes: list[dict[str, Any]] = field(default_factory=list)

    comentarios: list[str] = field(default_factory=list)
    elementos_ocultos: list[dict[str, Any]] = field(default_factory=list)

    indicadores: list[dict[str, Any]] = field(default_factory=list)
    tecnologias: list[dict[str, Any]] = field(default_factory=list)
    dados_potencialmente_sensiveis: list[dict[str, Any]] = field(
        default_factory=list
    )
    evidencias: list[dict[str, Any]] = field(default_factory=list)

    estatisticas: dict[str, int] = field(default_factory=dict)
    observacoes: list[str] = field(default_factory=list)


@dataclass
class TLSResultado:
    disponivel: bool = False
    protocolo: str = ""
    cipher: str = ""
    certificado_valido: bool | None = None
    emissor: str = ""
    sujeito: str = ""
    validade_inicio: str = ""
    validade_fim: str = ""
    hostname_compativel: bool | None = None


@dataclass
class ServicoObservado:
    porta: int
    transporte: str = "TCP"
    servico: str = ""
    protocolo: str = ""
    estado: str = "observado"
    origem: str = ""
    confianca: str = "MEDIA"
    detalhes: dict[str, Any] = field(default_factory=dict)



@dataclass
class ServidorObservado:
    produto: str = ""
    versao: str = ""
    familia: str = ""
    sistema_operacional: str = ""
    porta: int = 0
    protocolo: str = ""
    origem: str = ""
    estado: str = "observado"
    confianca: str = "MEDIA"
    detalhes: dict[str, Any] = field(default_factory=dict)



@dataclass
class Evidencia:
    identificador: str
    categoria: str
    titulo: str
    descricao: str
    origem: str
    confianca: str = "MEDIA"
    detalhes: dict[str, Any] = field(default_factory=dict)


@dataclass
class OnlineResultado:
    alvo: str
    sucesso: bool = False
    respostas: list[HTTPResposta] = field(default_factory=list)
    cookies: list[CookieObservado] = field(default_factory=list)
    cookies_info: dict = field(default_factory=dict)
    tls: TLSResultado | None = None
    servicos: list[ServicoObservado] = field(default_factory=list)
    servidores: list[ServidorObservado] = field(default_factory=list)
    evidencias: list[Evidencia] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)
    metadados: dict[str, Any] = field(default_factory=dict)
    http_bruto: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
