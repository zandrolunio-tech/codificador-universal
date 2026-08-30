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
    atributos: dict[str, Any] = field(default_factory=dict)


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
    tls: TLSResultado | None = None
    servicos: list[ServicoObservado] = field(default_factory=list)
    servidores: list[ServidorObservado] = field(default_factory=list)
    evidencias: list[Evidencia] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)
    metadados: dict[str, Any] = field(default_factory=dict)
