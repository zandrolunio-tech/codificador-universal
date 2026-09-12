import unittest

from online.modelos import (
    JavaScriptAnalise,
    JavaScriptExtraido,
)


class TestModelosJavaScript(unittest.TestCase):

    def test_javascript_extraido(self):
        resultado = JavaScriptExtraido(
            origem="script_src",
            tipo="externo",
            url="https://exemplo.test/app.js",
        )

        self.assertEqual(
            resultado.origem,
            "script_src",
        )

        self.assertEqual(
            resultado.tipo,
            "externo",
        )

        self.assertEqual(
            resultado.url,
            "https://exemplo.test/app.js",
        )

        self.assertEqual(
            resultado.conteudo,
            "",
        )

    def test_javascript_extraido_inline(self):
        resultado = JavaScriptExtraido(
            origem="script_inline",
            tipo="inline",
            conteudo="const valor = 10;",
        )

        self.assertEqual(
            resultado.origem,
            "script_inline",
        )

        self.assertEqual(
            resultado.tipo,
            "inline",
        )

        self.assertIn(
            "const valor",
            resultado.conteudo,
        )

    def test_online_resultado_possui_javascript_info(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        self.assertEqual(
            resultado.javascript_info,
            {},
        )

    def test_online_resultado_possui_javascript(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        self.assertEqual(
            resultado.javascript,
            [],
        )


    def test_javascript_analise_padrao(self):
        resultado = JavaScriptAnalise()

        self.assertFalse(
            resultado.detectado
        )

        self.assertEqual(
            resultado.tamanho,
            0,
        )

        self.assertEqual(
            resultado.funcoes,
            [],
        )

        self.assertEqual(
            resultado.imports,
            [],
        )

        self.assertEqual(
            resultado.exports,
            [],
        )

    def test_javascript_analise_completa(self):
        resultado = JavaScriptAnalise(
            detectado=True,
            tamanho=250,
            funcoes=["carregar"],
            imports=["react"],
            exports=["app"],
            urls=[
                "https://api.exemplo.test"
            ],
            endpoints=[
                "/api/clientes"
            ],
            websockets=[
                "wss://ws.exemplo.test"
            ],
            frameworks=["react"],
            apis={
                "fetch": [
                    "/api/clientes"
                ],
                "axios": [],
                "xmlhttprequest": [],
            },
            caracteristicas={
                "usa_fetch": True,
                "usa_xhr": False,
                "usa_websocket": True,
                "usa_modules": True,
                "usa_async": True,
            },
        )

        self.assertTrue(
            resultado.detectado
        )

        self.assertEqual(
            resultado.tamanho,
            250,
        )

        self.assertIn(
            "carregar",
            resultado.funcoes,
        )

        self.assertIn(
            "/api/clientes",
            resultado.endpoints,
        )

        self.assertTrue(
            resultado.caracteristicas[
                "usa_fetch"
            ]
        )


    def test_online_resultado_possui_urls(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        self.assertEqual(
            resultado.urls,
            [],
        )


    def test_online_resultado_possui_url_estruturada(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        url = {
            "url": "https://api.exemplo.test:8443/api/clientes?id=10#dados",
            "esquema": "https",
            "host": "api.exemplo.test",
            "porta": 8443,
            "caminho": "/api/clientes",
            "query": "id=10",
            "fragmento": "dados",
            "origens": ["javascript"],
            "interna": False,
            "tipo": "http",
        }

        resultado.urls.append(url)

        self.assertEqual(
            len(resultado.urls),
            1,
        )

        self.assertEqual(
            resultado.urls[0]["url"],
            "https://api.exemplo.test:8443/api/clientes?id=10#dados",
        )

        self.assertEqual(
            resultado.urls[0]["esquema"],
            "https",
        )

        self.assertEqual(
            resultado.urls[0]["host"],
            "api.exemplo.test",
        )

        self.assertEqual(
            resultado.urls[0]["porta"],
            8443,
        )

        self.assertEqual(
            resultado.urls[0]["caminho"],
            "/api/clientes",
        )

        self.assertEqual(
            resultado.urls[0]["query"],
            "id=10",
        )

        self.assertEqual(
            resultado.urls[0]["fragmento"],
            "dados",
        )

        self.assertEqual(
            resultado.urls[0]["origens"],
            ["javascript"],
        )

        self.assertFalse(
            resultado.urls[0]["interna"],
        )

        self.assertEqual(
            resultado.urls[0]["tipo"],
            "http",
        )


    def test_normaliza_url_observada(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "https://api.exemplo.test:8443/api/clientes?id=10#dados",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            resultado["url"],
            "https://api.exemplo.test:8443/api/clientes?id=10#dados",
        )

        self.assertEqual(
            resultado["esquema"],
            "https",
        )

        self.assertEqual(
            resultado["host"],
            "api.exemplo.test",
        )

        self.assertEqual(
            resultado["porta"],
            8443,
        )

        self.assertEqual(
            resultado["caminho"],
            "/api/clientes",
        )

        self.assertEqual(
            resultado["query"],
            "id=10",
        )

        self.assertEqual(
            resultado["fragmento"],
            "dados",
        )

        self.assertEqual(
            resultado["origens"],
            ["javascript"],
        )

        self.assertFalse(
            resultado["interna"],
        )

        self.assertEqual(
            resultado["tipo"],
            "http",
        )


    def test_normaliza_url_relativa(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "/api/clientes?id=10",
            base_url="https://exemplo.test/app/",
            origem="html",
        )

        self.assertEqual(
            resultado["url"],
            "https://exemplo.test/api/clientes?id=10",
        )

        self.assertEqual(
            resultado["esquema"],
            "https",
        )

        self.assertEqual(
            resultado["host"],
            "exemplo.test",
        )

        self.assertEqual(
            resultado["porta"],
            443,
        )

        self.assertEqual(
            resultado["caminho"],
            "/api/clientes",
        )

        self.assertEqual(
            resultado["query"],
            "id=10",
        )

        self.assertEqual(
            resultado["origens"],
            ["html"],
        )

        self.assertTrue(
            resultado["interna"],
        )

    def test_normaliza_url_http(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "http://exemplo.test/",
            base_url="http://exemplo.test/",
            origem="http",
        )

        self.assertEqual(
            resultado["esquema"],
            "http",
        )

        self.assertEqual(
            resultado["porta"],
            80,
        )

        self.assertEqual(
            resultado["tipo"],
            "http",
        )

        self.assertTrue(
            resultado["interna"],
        )

    def test_normaliza_url_websocket(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "wss://ws.exemplo.test/socket",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            resultado["esquema"],
            "wss",
        )

        self.assertEqual(
            resultado["host"],
            "ws.exemplo.test",
        )

        self.assertEqual(
            resultado["porta"],
            443,
        )

        self.assertEqual(
            resultado["tipo"],
            "websocket",
        )

        self.assertFalse(
            resultado["interna"],
        )

    def test_normaliza_url_externa(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "https://cdn.externo.test/app.js",
            base_url="https://exemplo.test/",
            origem="html",
        )

        self.assertFalse(
            resultado["interna"],
        )

        self.assertEqual(
            resultado["host"],
            "cdn.externo.test",
        )

    def test_normaliza_url_com_fragmento(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "/clientes/10?modo=detalhado#perfil",
            base_url="https://exemplo.test/",
            origem="html",
        )

        self.assertEqual(
            resultado["query"],
            "modo=detalhado",
        )

        self.assertEqual(
            resultado["fragmento"],
            "perfil",
        )

    def test_normaliza_url_invalida(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "://url-invalida",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            resultado,
            {},
        )


if __name__ == "__main__":
    unittest.main()
