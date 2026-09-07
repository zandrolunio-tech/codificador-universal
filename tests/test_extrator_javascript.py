import unittest

from online.extrator_javascript import (
    extrair_codigo_inline,
    extrair_javascript,
    extrair_urls_javascript,
)


class TestExtratorJavaScript(unittest.TestCase):

    def test_extrai_script_externo(self):
        html = """
        <html>
            <head>
                <script src="/static/app.js"></script>
            </head>
        </html>
        """

        resultado = extrair_javascript(
            html,
            "https://exemplo.test/"
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0].origem,
            "script_src",
        )
        self.assertEqual(
            resultado[0].tipo,
            "externo",
        )
        self.assertEqual(
            resultado[0].url,
            "https://exemplo.test/static/app.js",
        )

    def test_extrai_script_inline(self):
        html = """
        <script>
            const nome = "teste";
            console.log(nome);
        </script>
        """

        resultado = extrair_javascript(html)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0].origem,
            "script_inline",
        )
        self.assertEqual(
            resultado[0].tipo,
            "inline",
        )
        self.assertIn(
            'const nome = "teste";',
            resultado[0].conteudo,
        )

    def test_detecta_modulo_externo(self):
        html = """
        <script
            type="module"
            src="/assets/main.js">
        </script>
        """

        resultado = extrair_javascript(
            html,
            "https://exemplo.test/app/"
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0].tipo,
            "module",
        )
        self.assertEqual(
            resultado[0].url,
            "https://exemplo.test/assets/main.js",
        )

    def test_detecta_modulo_inline(self):
        html = """
        <script type="module">
            import { app } from "./app.js";
            app();
        </script>
        """

        resultado = extrair_javascript(html)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0].tipo,
            "module",
        )
        self.assertIn(
            "import",
            resultado[0].conteudo,
        )

    def test_extrai_varios_scripts(self):
        html = """
        <script src="/a.js"></script>

        <script>
            const a = 1;
        </script>

        <script src="/b.js"></script>

        <script>
            const b = 2;
        </script>
        """

        resultado = extrair_javascript(
            html,
            "https://exemplo.test/"
        )

        self.assertEqual(len(resultado), 4)

    def test_extrair_urls_javascript(self):
        html = """
        <script src="/a.js"></script>
        <script src="https://cdn.exemplo.test/b.js"></script>
        <script>
            console.log("inline");
        </script>
        """

        resultado = extrair_urls_javascript(
            html,
            "https://exemplo.test/"
        )

        self.assertEqual(
            resultado,
            [
                "https://cdn.exemplo.test/b.js",
                "https://exemplo.test/a.js",
            ],
        )

    def test_extrair_codigo_inline(self):
        html = """
        <script>
            const a = 1;
        </script>

        <script src="/app.js"></script>

        <script>
            const b = 2;
        </script>
        """

        resultado = extrair_codigo_inline(html)

        self.assertEqual(len(resultado), 2)
        self.assertIn(
            "const a = 1;",
            resultado[0],
        )
        self.assertIn(
            "const b = 2;",
            resultado[1],
        )

    def test_ignora_script_vazio(self):
        html = """
        <script></script>
        <script>   </script>
        """

        resultado = extrair_javascript(html)

        self.assertEqual(resultado, [])

    def test_html_vazio(self):
        resultado = extrair_javascript("")

        self.assertEqual(resultado, [])


if __name__ == "__main__":
    unittest.main()
