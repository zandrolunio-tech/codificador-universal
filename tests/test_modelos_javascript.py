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


if __name__ == "__main__":
    unittest.main()
