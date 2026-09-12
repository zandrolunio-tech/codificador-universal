import unittest
from unittest.mock import patch

from online.modelos import (
    HTTPHeader,
    HTTPResposta,
    OnlineResultado,
    ServicoObservado,
    ServidorObservado,
)
from online.orquestrador import analisar_online, _consolidar_javascript


class TestOrquestrador(unittest.TestCase):

    def criar_resposta(self):
        return HTTPResposta(
            url="https://exemplo.test/",
            status_code=200,
            reason="OK",
            http_version="HTTP/1.1",
            headers=[
                HTTPHeader(
                    nome="Server",
                    valor="nginx/1.24.0",
                ),
                HTTPHeader(
                    nome="Content-Type",
                    valor="text/html",
                ),
            ],
            content_type="text/html",
            tamanho=20,
            corpo="<html>teste</html>",
            tempo_resposta_ms=12.5,
        )

    def test_inventario_urls_html_e_javascript(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        resultado.urls = [
            {
                "url": "https://exemplo.test/api/login",
                "esquema": "https",
                "host": "exemplo.test",
                "porta": 443,
                "caminho": "/api/login",
                "query": "",
                "fragmento": "",
                "origens": ["html", "javascript"],
                "interna": True,
                "tipo": "http",
            },
            {
                "url": "wss://exemplo.test/socket",
                "esquema": "wss",
                "host": "exemplo.test",
                "porta": 443,
                "caminho": "/socket",
                "query": "",
                "fragmento": "",
                "origens": ["javascript"],
                "interna": True,
                "tipo": "websocket",
            },
        ]

        self.assertEqual(len(resultado.urls), 2)

        urls = {
            item["url"]: item
            for item in resultado.urls
        }

        self.assertIn(
            "https://exemplo.test/api/login",
            urls,
        )

        self.assertEqual(
            urls["https://exemplo.test/api/login"]["origens"],
            ["html", "javascript"],
        )

        self.assertEqual(
            urls["wss://exemplo.test/socket"]["tipo"],
            "websocket",
        )

    def test_consolidacao_urls_deduplica_e_agrega_origens(self):
        from online.orquestrador import _consolidar_urls

        resultado = _consolidar_urls(
            alvo="https://exemplo.test/",
            respostas=[],
            analises_respostas=[
                {
                    "http": {
                        "url_final": "https://exemplo.test/",
                        "location": "",
                        "redirecionamentos": [],
                    },
                    "html": {
                        "recursos": [
                            {
                                "url": (
                                    "https://exemplo.test/api/clientes"
                                    "?id=10#dados"
                                ),
                            }
                        ],
                        "links": [],
                        "formularios": [],
                    },
                }
            ],
            javascript_info={
                "urls": [
                    (
                        "https://exemplo.test/api/clientes"
                        "?id=10#dados"
                    )
                ],
                "endpoints": [],
                "websockets": [],
                "requisicoes_http": [],
                "websockets_info": [],
            },
        )

        urls = {
            item["url"]: item
            for item in resultado
        }

        url = (
            "https://exemplo.test/api/clientes"
            "?id=10#dados"
        )

        self.assertEqual(
            len([
                item for item in resultado
                if item["url"] == url
            ]),
            1,
        )

        self.assertEqual(
            urls[url]["origens"],
            ["html", "javascript"],
        )

        self.assertEqual(
            urls[url]["query"],
            "id=10",
        )

        self.assertEqual(
            urls[url]["fragmento"],
            "dados",
        )

    def test_consolidacao_urls_classifica_websocket_e_externa(self):
        from online.orquestrador import _consolidar_urls

        resultado = _consolidar_urls(
            alvo="https://exemplo.test/",
            respostas=[],
            analises_respostas=[
                {
                    "http": {
                        "url_final": "https://exemplo.test/",
                        "location": "",
                        "redirecionamentos": [],
                    },
                    "html": {
                        "recursos": [
                            {
                                "url": (
                                    "https://cdn.externo.test/logo.png"
                                ),
                            }
                        ],
                        "links": [],
                        "formularios": [],
                    },
                }
            ],
            javascript_info={
                "urls": [],
                "endpoints": [],
                "websockets": [
                    "wss://exemplo.test/socket",
                ],
                "requisicoes_http": [],
                "websockets_info": [],
            },
        )

        urls = {
            item["url"]: item
            for item in resultado
        }

        websocket = urls["wss://exemplo.test/socket"]
        externa = urls["https://cdn.externo.test/logo.png"]

        self.assertEqual(
            websocket["tipo"],
            "websocket",
        )

        self.assertEqual(
            websocket["esquema"],
            "wss",
        )

        self.assertEqual(
            websocket["porta"],
            443,
        )

        self.assertFalse(
            websocket["interna"],
        )

        self.assertFalse(
            externa["interna"],
        )

        self.assertEqual(
            externa["tipo"],
            "http",
        )

    def test_consolidacao_rotas_deduplica_parametros_e_agrega_origens(self):
        from online.orquestrador import _consolidar_rotas

        resultado = _consolidar_rotas(
            alvo="https://exemplo.test/",
            respostas=[],
            analises_respostas=[
                {
                    "http": {
                        "url_final": "https://exemplo.test/",
                    },
                    "html": {
                        "recursos": [],
                        "links": [
                            {
                                "url": (
                                    "/api/clientes?id=10"
                                ),
                            },
                            {
                                "url": (
                                    "/api/clientes?id=20"
                                ),
                            },
                        ],
                        "formularios": [],
                    },
                }
            ],
            javascript_info={
                "urls": [],
                "endpoints": [
                    "/api/clientes?ativo=true",
                ],
                "websockets": [],
                "requisicoes_http": [],
                "websockets_info": [],
            },
        )

        self.assertEqual(
            len(resultado),
            1,
        )

        rota = resultado[0]

        self.assertEqual(
            rota["rota"],
            "/api/clientes",
        )

        self.assertEqual(
            rota["url_base"],
            "https://exemplo.test",
        )

        self.assertEqual(
            rota["parametros"],
            ["id", "ativo"],
        )

        self.assertIn(
            "html",
            rota["origens"],
        )

        self.assertIn(
            "javascript",
            rota["origens"],
        )

    def test_consolidacao_rotas_separa_metodos_http(self):
        from online.orquestrador import _consolidar_rotas

        resultado = _consolidar_rotas(
            alvo="https://exemplo.test/",
            respostas=[],
            analises_respostas=[],
            javascript_info={
                "urls": [],
                "endpoints": [],
                "websockets": [],
                "requisicoes_http": [
                    {
                        "tipo": "fetch",
                        "metodo": "GET",
                        "url": "/api/clientes",
                        "url_resposta": "https://exemplo.test/",
                    },
                    {
                        "tipo": "fetch",
                        "metodo": "POST",
                        "url": "/api/clientes",
                        "url_resposta": "https://exemplo.test/",
                    },
                ],
                "websockets_info": [],
            },
        )

        self.assertEqual(
            len(resultado),
            2,
        )

        metodos = {
            item["metodo"]
            for item in resultado
        }

        self.assertEqual(
            metodos,
            {"GET", "POST"},
        )

    def test_consolidacao_rotas_preserva_websocket(self):
        from online.orquestrador import _consolidar_rotas

        resultado = _consolidar_rotas(
            alvo="https://exemplo.test/",
            respostas=[],
            analises_respostas=[],
            javascript_info={
                "urls": [],
                "endpoints": [],
                "websockets": [
                    "wss://exemplo.test/socket?canal=chat",
                ],
                "requisicoes_http": [],
                "websockets_info": [],
            },
        )

        self.assertEqual(
            len(resultado),
            1,
        )

        rota = resultado[0]

        self.assertEqual(
            rota["rota"],
            "/socket",
        )

        self.assertEqual(
            rota["tipo"],
            "websocket",
        )

        self.assertEqual(
            rota["parametros"],
            ["canal"],
        )

        self.assertEqual(
            rota["metodo"],
            "",
        )

    def test_consolidacao_rotas_rejeita_fontes_invalidas(self):
        from online.orquestrador import _consolidar_rotas

        resultado = _consolidar_rotas(
            alvo="https://exemplo.test/",
            respostas=[],
            analises_respostas=[
                {
                    "http": {
                        "url_final": "https://exemplo.test/",
                    },
                    "html": {
                        "recursos": [
                            {
                                "url": "mailto:teste@exemplo.test",
                            },
                        ],
                        "links": [],
                        "formularios": [],
                    },
                }
            ],
            javascript_info={
                "urls": [
                    "mailto:outro@exemplo.test",
                ],
                "endpoints": [],
                "websockets": [],
                "requisicoes_http": [],
                "websockets_info": [],
            },
        )

        self.assertEqual(
            resultado,
            [],
        )

    def test_consolidacao_rotas_nao_realiza_requisicoes(self):
        from online.orquestrador import _consolidar_rotas

        resultado = _consolidar_rotas(
            alvo="https://exemplo.test/",
            respostas=[],
            analises_respostas=[],
            javascript_info={
                "urls": [
                    "/api/clientes",
                ],
                "endpoints": [
                    "/api/login",
                ],
                "websockets": [],
                "requisicoes_http": [],
                "websockets_info": [],
            },
        )

        self.assertEqual(
            len(resultado),
            2,
        )

    def test_inventario_rotas_integrado_na_analise_online(self):
        from unittest.mock import patch

        with patch("online.orquestrador.coletar") as mock_coletar,              patch("online.orquestrador.analisar_tls") as mock_tls,              patch("online.orquestrador.construir_inventario") as mock_inventario:

            coleta = OnlineResultado(
                alvo="https://exemplo.test/",
                sucesso=True,
            )

            coleta.respostas = [
                HTTPResposta(
                    url="https://exemplo.test/",
                    status_code=200,
                    reason="OK",
                    http_version="HTTP/1.1",
                    headers=[],
                    content_type="text/html",
                    tamanho=100,
                    corpo=(
                        "<a href='/api/clientes?id=10'>"
                        "Clientes"
                        "</a>"
                    ),
                    tempo_resposta_ms=10,
                    redirecionamentos=[],
                )
            ]

            mock_coletar.return_value = coleta

            mock_tls.return_value = {}
            mock_inventario.return_value = []

            resultado = analisar_online(
                "https://exemplo.test/",
                timeout=10,
            )

        self.assertEqual(
            len(resultado.rotas),
            1,
        )

        rota = resultado.rotas[0]

        self.assertEqual(
            rota["rota"],
            "/api/clientes",
        )

        self.assertEqual(
            rota["url_base"],
            "https://exemplo.test",
        )

        self.assertEqual(
            rota["parametros"],
            ["id"],
        )

        self.assertIn(
            "html",
            rota["origens"],
        )

        self.assertEqual(
            resultado.metadados["rotas"],
            resultado.rotas,
        )

    @patch("online.orquestrador.construir_inventario")
    @patch("online.orquestrador.analisar_tls")
    @patch("online.orquestrador.coletar")
    def test_inventario_urls_integrado_na_analise_online(
        self,
        mock_coletar,
        mock_tls,
        mock_inventario,
    ):
        resposta = self.criar_resposta()

        resposta.corpo = """
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="/css/app.css">
            <script>
                const api = "/api/clientes";
                const socket = new WebSocket(
                    "wss://exemplo.test/socket"
                );
            </script>
        </head>
        <body>
            <img src="https://cdn.externo.test/logo.png">
        </body>
        </html>
        """

        mock_coletar.return_value.sucesso = True
        mock_coletar.return_value.respostas = [resposta]
        mock_coletar.return_value.cookies = []
        mock_coletar.return_value.erros = []

        mock_tls.return_value = {
            "detectado": False,
            "sucesso": False,
            "url": "https://exemplo.test/",
            "erros": [],
        }

        mock_inventario.return_value = {
            "alvo": "https://exemplo.test/",
        }

        resultado = analisar_online(
            "https://exemplo.test/",
            timeout=5,
            analisar_certificado=True,
        )

        self.assertTrue(
            isinstance(resultado.urls, list)
        )

        urls = {
            item["url"]: item
            for item in resultado.urls
        }

        self.assertIn(
            "https://exemplo.test/css/app.css",
            urls,
        )

        self.assertIn(
            "https://exemplo.test/api/clientes",
            urls,
        )

        self.assertIn(
            "wss://exemplo.test/socket",
            urls,
        )

        self.assertIn(
            "https://cdn.externo.test/logo.png",
            urls,
        )

        self.assertTrue(
            urls[
                "https://exemplo.test/css/app.css"
            ]["interna"]
        )

        self.assertFalse(
            urls[
                "https://cdn.externo.test/logo.png"
            ]["interna"]
        )

        self.assertEqual(
            urls[
                "wss://exemplo.test/socket"
            ]["tipo"],
            "websocket",
        )

    @patch("online.orquestrador.construir_inventario")
    @patch("online.orquestrador.analisar_portas")
    @patch("online.orquestrador.analisar_tls")
    @patch("online.orquestrador.coletar")
    def test_headers_http_sao_integrados_ao_resultado(
        self,
        mock_coletar,
        mock_tls,
        mock_portas,
        mock_inventario,
    ):
        resposta = self.criar_resposta()

        mock_coletar.return_value.sucesso = True
        mock_coletar.return_value.respostas = [resposta]
        mock_coletar.return_value.cookies = []
        mock_coletar.return_value.erros = []

        mock_tls.return_value = {
            "detectado": False,
            "sucesso": False,
            "url": "https://exemplo.test/",
            "erros": [],
        }

        mock_portas.return_value = []

        mock_inventario.return_value = {
            "alvo": "https://exemplo.test/",
        }

        resultado = analisar_online(
            "https://exemplo.test/",
            timeout=5,
            analisar_certificado=True,
        )

        self.assertIn(
            "respostas",
            resultado.headers,
        )

        self.assertEqual(
            len(resultado.headers["respostas"]),
            1,
        )

        resposta_headers = resultado.headers["respostas"][0]

        self.assertEqual(
            resposta_headers["url"],
            "https://exemplo.test/",
        )

        self.assertEqual(
            resposta_headers["headers"]["server"],
            "nginx/1.24.0",
        )

        self.assertEqual(
            resposta_headers["headers"]["content-type"],
            "text/html",
        )


    @patch("online.orquestrador.construir_inventario")
    @patch("online.orquestrador.analisar_portas")
    @patch("online.orquestrador.analisar_tls")
    @patch("online.orquestrador.coletar")
    def test_fluxo_principal(
        self,
        mock_coletar,
        mock_tls,
        mock_portas,
        mock_inventario,
    ):
        resposta = self.criar_resposta()

        mock_coletar.return_value.sucesso = True
        mock_coletar.return_value.respostas = [resposta]
        mock_coletar.return_value.cookies = []
        mock_coletar.return_value.erros = []

        mock_tls.return_value = {
            "detectado": True,
            "sucesso": True,
            "url": "https://exemplo.test/",
            "host": "exemplo.test",
            "porta": 443,
            "versao_tls": "TLSv1.3",
            "cipher": {
                "nome": "TLS_AES_256_GCM_SHA384",
                "protocolo": "TLSv1.3",
                "bits": 256,
            },
            "alpn": "http/1.1",
            "certificado": {
                "not_after": "Jan 01 00:00:00 2030 GMT",
                "dias_para_expirar": 1000,
                "subject_alt_names": [
                    "exemplo.test",
                ],
            },
            "erros": [],
        }

        mock_portas.return_value = []

        mock_inventario.return_value = {
            "alvo": "https://exemplo.test/",
        }

        resultado = analisar_online(
            "https://exemplo.test/",
            timeout=5,
            analisar_certificado=True,
        )

        self.assertTrue(resultado.sucesso)

        self.assertEqual(
            len(resultado.respostas),
            1,
        )

        self.assertIsNotNone(
            resultado.tls
        )

        self.assertEqual(
            resultado.tls.protocolo,
            "TLSv1.3",
        )

        self.assertTrue(
            any(
                evidencia.identificador == "HTTP-STATUS"
                for evidencia in resultado.evidencias
            )
        )

        self.assertTrue(
            any(
                evidencia.identificador == "TLS-CONEXAO"
                for evidencia in resultado.evidencias
            )
        )

        self.assertTrue(
            any(
                servidor.produto.lower() == "nginx"
                for servidor in resultado.servidores
            )
        )

        self.assertIn(
            "correlacoes",
            resultado.metadados,
        )

        self.assertIn(
            "inventario_superficie",
            resultado.metadados,
        )

        mock_coletar.assert_called_once()
        mock_tls.assert_called_once()
        mock_inventario.assert_called_once()

    @patch("online.orquestrador.analisar_portas")
    @patch("online.orquestrador.analisar_tls")
    @patch("online.orquestrador.coletar")
    def test_portas_sao_verificadas_somente_quando_fornecidas(
        self,
        mock_coletar,
        mock_tls,
        mock_portas,
    ):
        resposta = self.criar_resposta()

        mock_coletar.return_value.sucesso = True
        mock_coletar.return_value.respostas = [resposta]
        mock_coletar.return_value.cookies = []
        mock_coletar.return_value.erros = []

        mock_tls.return_value = {
            "detectado": False,
            "sucesso": False,
            "url": "https://exemplo.test/",
            "erros": [],
        }

        mock_portas.return_value = []

        with patch(
            "online.orquestrador.construir_inventario"
        ) as mock_inventario:
            mock_inventario.return_value = {
                "alvo": "https://exemplo.test/",
            }

            analisar_online(
                "https://exemplo.test/",
                portas=[80, 443],
            )

        mock_portas.assert_called_once_with(
            host="exemplo.test",
            portas=[80, 443],
            timeout=10.0,
        )

    @patch("online.orquestrador.construir_inventario")
    @patch("online.orquestrador.analisar_portas")
    @patch("online.orquestrador.analisar_tls")
    @patch("online.orquestrador.coletar")
    def test_integracao_javascript_na_analise_online(
        self,
        mock_coletar,
        mock_tls,
        mock_portas,
        mock_inventario,
    ):
        resposta = self.criar_resposta()

        resposta.corpo = """
        <!DOCTYPE html>
        <html>
        <head>
            <script>
                function iniciar() {
                    return fetch("/api/login");
                }

                const socket = new WebSocket(
                    "wss://exemplo.test/socket"
                );

                const xhr = new XMLHttpRequest();
                element.innerHTML = xhr.response;

                const mensagem = "aHR0cHM6Ly9leGVtcGxvLnRlc3Q=";
            </script>
        </head>
        <body>
            <h1>Teste</h1>
        </body>
        </html>
        """

        mock_coletar.return_value.sucesso = True
        mock_coletar.return_value.respostas = [resposta]
        mock_coletar.return_value.cookies = []
        mock_coletar.return_value.erros = []

        mock_tls.return_value = {
            "detectado": False,
            "sucesso": False,
            "url": "https://exemplo.test/",
            "erros": [],
        }

        mock_portas.return_value = []

        mock_inventario.return_value = {
            "alvo": "https://exemplo.test/",
        }

        resultado = analisar_online(
            "https://exemplo.test/",
            timeout=5,
            analisar_certificado=True,
        )

        self.assertIn(
            "javascript",
            resultado.metadados,
        )

        javascript = resultado.metadados["javascript"]

        self.assertEqual(
            resultado.javascript,
            javascript,
        )

        self.assertEqual(
            len(javascript),
            1,
        )

        self.assertEqual(
            javascript[0]["url"],
            "https://exemplo.test/",
        )

        self.assertEqual(
            len(javascript[0]["scripts"]),
            1,
        )

        self.assertEqual(
            javascript[0]["scripts"][0]["origem"],
            "script_inline",
        )

        self.assertEqual(
            len(javascript[0]["analises"]),
            1,
        )

        javascript_info = resultado.javascript_info

        self.assertEqual(
            javascript_info["total_scripts"],
            1,
        )
        self.assertEqual(
            javascript_info["scripts_analisados"],
            1,
        )
        self.assertEqual(
            javascript_info["scripts_inline"],
            1,
        )
        self.assertIn(
            "/api/login",
            javascript_info["endpoints"],
        )
        self.assertIn(
            "wss://exemplo.test/socket",
            javascript_info["websockets"],
        )
        self.assertTrue(
            javascript_info["caracteristicas"].get(
                "usa_fetch",
                False,
            )
        )
        self.assertTrue(
            any(
                sink.get("tipo") == "innerHTML"
                for sink in javascript_info["dom_sinks"]
            )
        )
        self.assertEqual(
            len(javascript_info["inspecoes_profunda"]),
            1,
        )

        analise = javascript[0]["analises"][0]["analise"]

        self.assertTrue(
            analise["detectado"]
        )

        self.assertTrue(
            any(
                "iniciar" in funcao
                for funcao in analise["funcoes"]
            )
        )

        self.assertIn(
            "/api/login",
            analise["endpoints"],
        )

        self.assertIn(
            "wss://exemplo.test/socket",
            analise["websockets"],
        )

        self.assertTrue(
            analise["caracteristicas"]["usa_fetch"]
        )

        self.assertTrue(
            analise["caracteristicas"]["usa_websocket"]
        )

        strings = javascript[0]["analises"][0]["strings"]

        self.assertTrue(
            any(
                item["original"]
                == "aHR0cHM6Ly9leGVtcGxvLnRlc3Q="
                for item in strings
            )
        )

        correlacoes = resultado.metadados["correlacoes"]

        self.assertTrue(
            any(
                correlacao.identificador
                == "CORR-JS-DOM-SOURCE-SINK"
                for correlacao in correlacoes
            )
        )

    def test_consolidar_javascript(self):
        from online.orquestrador import _consolidar_javascript

        javascript = [
            {
                "url": "https://exemplo.test/",
                "scripts": [
                    {
                        "origem": "script_inline",
                        "tipo": "module",
                        "url": "https://exemplo.test/",
                        "conteudo": "const x = 1;",
                        "atributos": {},
                    },
                    {
                        "origem": "script_src",
                        "tipo": "externo",
                        "url": "https://cdn.exemplo.test/app.js",
                        "conteudo": "",
                        "atributos": {
                            "defer": "defer",
                        },
                    },
                ],
                "analises": [
                    {
                        "origem": "script_inline",
                        "tipo": "module",
                        "url": "https://exemplo.test/",
                        "analise": {
                            "detectado": True,
                            "funcoes": ["iniciar"],
                            "imports": ["./modulo.js"],
                            "exports": ["iniciar"],
                            "urls": [
                                "https://exemplo.test/api"
                            ],
                            "endpoints": ["/api/login"],
                            "websockets": [
                                "wss://exemplo.test/socket"
                            ],
                            "apis": {
                                "fetch": ["fetch"]
                            },
                            "frameworks": ["React"],
                            "caracteristicas": {
                                "fetch": True,
                                "modules": True,
                            },
                            "fontes_dados": [
                                "fetch"
                            ],
                            "dom_sinks": [
                                "innerHTML"
                            ],
                            "padroes_sensiveis": {
                                "document_cookie": [
                                    "document.cookie"
                                ]
                            },
                            "inspecao_profunda": {
                                "tamanho_bytes": 12,
                                "urls_http": [
                                    "https://exemplo.test/api"
                                ],
                                "urls_websocket": [
                                    "wss://exemplo.test/socket"
                                ],
                                "metodos_http": {
                                    "GET": 1
                                },
                                "indicadores_sensiveis": {
                                    "cookie": 1
                                },
                            },
                        },
                        "strings": [
                            "https://exemplo.test/api"
                        ],
                    }
                ],
            }
        ]

        resultado = _consolidar_javascript(
            javascript
        )

        self.assertEqual(
            resultado["total_scripts"],
            2,
        )
        self.assertEqual(
            resultado["scripts_analisados"],
            1,
        )
        self.assertEqual(
            resultado["scripts_inline"],
            1,
        )
        self.assertEqual(
            resultado["scripts_externos"],
            1,
        )
        self.assertEqual(
            resultado["modulos"],
            1,
        )
        self.assertIn(
            "iniciar",
            resultado["funcoes"],
        )
        self.assertIn(
            "/api/login",
            resultado["endpoints"],
        )
        self.assertIn(
            "wss://exemplo.test/socket",
            resultado["websockets"],
        )
        self.assertIn(
            "React",
            resultado["frameworks"],
        )
        self.assertIn(
            "innerHTML",
            resultado["dom_sinks"],
        )
        self.assertIn(
            "fetch",
            resultado["fontes_dados"],
        )
        self.assertIn(
            "document_cookie",
            resultado["padroes_sensiveis"],
        )
        self.assertEqual(
            len(resultado["inspecoes_profunda"]),
            1,
        )


    def test_consolidar_javascript_integra_websocket_info(self):
        javascript_resultados = [
            {
                "url": "https://exemplo.test/",
                "scripts": [
                    {
                        "origem": "script_inline",
                        "tipo": "classic",
                        "url": "",
                        "conteudo": "new WebSocket('wss://exemplo.test/socket')",
                        "atributos": {},
                    }
                ],
                "analises": [
                    {
                        "origem": "script_inline",
                        "tipo": "classic",
                        "url": "",
                        "atributos": {},
                        "conteudo": "new WebSocket('wss://exemplo.test/socket')",
                        "analise": {
                            "detectado": True,
                            "websockets": [
                                "wss://exemplo.test/socket"
                            ],
                            "websockets_info": [
                                {
                                    "tipo": "websocket",
                                    "url": "wss://exemplo.test/socket",
                                    "eventos": [
                                        "open",
                                        "message",
                                        "close",
                                        "error",
                                    ],
                                    "envio": True,
                                    "recepcao": True,
                                    "linha": 1,
                                }
                            ],
                        },
                        "strings": [],
                    }
                ],
            }
        ]

        resultado = _consolidar_javascript(
            javascript_resultados
        )

        self.assertIn(
            "websockets_info",
            resultado,
        )

        self.assertEqual(
            len(resultado["websockets_info"]),
            1,
        )

        websocket = resultado["websockets_info"][0]

        self.assertEqual(
            websocket["tipo"],
            "websocket",
        )

        self.assertEqual(
            websocket["url"],
            "wss://exemplo.test/socket",
        )

        self.assertIn(
            "open",
            websocket["eventos"],
        )

        self.assertIn(
            "message",
            websocket["eventos"],
        )

        self.assertTrue(
            websocket["envio"],
        )

        self.assertTrue(
            websocket["recepcao"],
        )

        self.assertEqual(
            websocket["url_resposta"],
            "https://exemplo.test/",
        )

        self.assertEqual(
            websocket["origem"],
            "script_inline",
        )

    def test_consolidar_javascript_integra_requisicoes_http(self):
        from online.orquestrador import _consolidar_javascript

        javascript_resultados = [
            {
                "url": "http://laboratorio.local/",
                "scripts": [
                    {
                        "origem": "script_inline",
                        "tipo": "classic",
                        "url": "",
                        "conteudo": "fetch('/api/login')",
                        "atributos": {},
                    }
                ],
                "analises": [
                    {
                        "origem": "script_inline",
                        "tipo": "classic",
                        "url": "",
                        "atributos": {},
                        "conteudo": "fetch('/api/login')",
                        "analise": {
                            "detectado": True,
                            "requisicoes_http": [
                                {
                                    "tipo": "fetch",
                                    "metodo": "POST",
                                    "url": "/api/login",
                                    "headers": [
                                        {
                                            "nome": "Content-Type",
                                            "valor": "application/json",
                                        }
                                    ],
                                    "body": "JSON.stringify(dados)",
                                    "linha": 1,
                                }
                            ],
                        },
                        "strings": [],
                    }
                ],
            }
        ]

        resultado = _consolidar_javascript(
            javascript_resultados
        )

        self.assertIn(
            "requisicoes_http",
            resultado,
        )

        self.assertEqual(
            len(resultado["requisicoes_http"]),
            1,
        )

        requisicao = resultado["requisicoes_http"][0]

        self.assertEqual(
            requisicao["tipo"],
            "fetch",
        )

        self.assertEqual(
            requisicao["metodo"],
            "POST",
        )

        self.assertEqual(
            requisicao["url"],
            "/api/login",
        )

        self.assertEqual(
            requisicao["body"],
            "JSON.stringify(dados)",
        )

        self.assertEqual(
            requisicao["url_resposta"],
            "http://laboratorio.local/",
        )

        self.assertEqual(
            requisicao["origem"],
            "script_inline",
        )

if __name__ == "__main__":
    unittest.main()
