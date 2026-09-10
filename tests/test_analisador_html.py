import unittest

from online.analisador_html import analisar_html


class TestAnalisadorHTML(unittest.TestCase):

    def setUp(self):
        self.url = "https://exemplo.test/login"

        self.html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width">
    <meta name="description" content="Página de login">
    <meta property="og:title" content="Login">
    <meta name="twitter:card" content="summary">
    <title>Página de Login</title>
    <link rel="canonical" href="https://exemplo.test/login">
    <link rel="stylesheet" href="/css/app.css">
    <link rel="icon" href="/favicon.ico">
    <link rel="preconnect" href="https://cdn.externo.test">
</head>
<body>
    <!-- comentário de teste -->

    <script src="/js/app.js" defer></script>
    <script type="module">
        const exemplo = true;
    </script>

    <img src="/img/logo.png" alt="Logo">
    <iframe
        src="https://externo.test/widget"
        sandbox
        referrerpolicy="no-referrer"
    ></iframe>

    <form action="/login" method="POST" autocomplete="off">
        <input
            type="text"
            name="username"
            id="username"
            placeholder="Utilizador"
            required
        >
        <input
            type="password"
            name="password"
            id="password"
            required
            autocomplete="current-password"
        >
        <button type="submit">Entrar</button>
    </form>
</body>
</html>
"""

    def test_documento_basico(self):
        resultado = analisar_html(
            self.html,
            self.url,
            "text/html; charset=UTF-8",
        )

        self.assertTrue(resultado.detectado)
        self.assertTrue(resultado.valido)
        self.assertEqual(resultado.url, self.url)
        self.assertEqual(resultado.content_type, "text/html; charset=UTF-8")
        self.assertEqual(resultado.charset.lower(), "utf-8")
        self.assertEqual(resultado.lang, "pt-BR")
        self.assertEqual(resultado.titulo, "Página de Login")
        self.assertTrue(resultado.doctype)
        self.assertGreater(resultado.tamanho, 0)
        self.assertGreater(resultado.profundidade, 0)

    def test_head_e_metas(self):
        resultado = analisar_html(
            self.html,
            self.url,
            "text/html; charset=UTF-8",
        )

        nomes = {
            item.get("name")
            for item in resultado.metas
            if item.get("name")
        }

        self.assertIn("viewport", nomes)
        self.assertIn("description", nomes)

        propriedades = {
            item.get("atributos", {}).get("property")
            for item in resultado.metas
        }

        self.assertIn("og:title", propriedades)

        self.assertTrue(
            any(
                item.get("tipo") == "canonical"
                for item in resultado.links
            )
        )

        self.assertTrue(
            any(
                item.get("tipo") == "favicon"
                for item in resultado.links
            )
        )

    def test_scripts_externos_e_inline(self):
        resultado = analisar_html(
            self.html,
            self.url,
            "text/html",
        )

        self.assertEqual(len(resultado.scripts), 2)

        externos = [
            item
            for item in resultado.scripts
            if item.get("tipo") == "externo"
        ]

        inline = [
            item
            for item in resultado.scripts
            if item.get("tipo") == "inline"
        ]

        self.assertEqual(len(externos), 1)
        self.assertEqual(len(inline), 1)
        self.assertEqual(externos[0]["url"], "https://exemplo.test/js/app.js")
        self.assertGreater(inline[0]["tamanho_inline"], 0)

    def test_formulario_e_campos(self):
        resultado = analisar_html(
            self.html,
            self.url,
            "text/html",
        )

        self.assertEqual(len(resultado.formularios), 1)
        self.assertEqual(len(resultado.campos_formulario), 3)

        formulario = resultado.formularios[0]

        self.assertEqual(formulario["method"], "POST")
        self.assertEqual(formulario["url"], "https://exemplo.test/login")

        classificacoes = {
            campo["name"]: campo["classificacao"]
            for campo in resultado.campos_formulario
            if campo.get("name")
        }

        self.assertEqual(classificacoes["username"], "login")
        self.assertEqual(classificacoes["password"], "login")

    def test_recursos_e_origens(self):
        resultado = analisar_html(
            self.html,
            self.url,
            "text/html",
        )

        self.assertEqual(len(resultado.imagens), 1)
        self.assertEqual(len(resultado.iframes), 1)

        iframe = resultado.iframes[0]

        self.assertEqual(
            iframe["url"],
            "https://externo.test/widget",
        )
        self.assertTrue(iframe["externo"])

        self.assertTrue(
            any(
                item.get("tipo") == "preconnect"
                for item in resultado.indicadores
            )
        )

    def test_elementos_importantes_comentarios_e_estatisticas(self):
        resultado = analisar_html(
            self.html,
            self.url,
            "text/html",
        )

        elementos = {
            item["elemento"]
            for item in resultado.elementos_importantes
        }

        self.assertIn("form", elementos)
        self.assertIn("script", elementos)
        self.assertIn("iframe", elementos)
        self.assertIn("img", elementos)

        self.assertEqual(len(resultado.comentarios), 1)

        estatisticas = resultado.estatisticas

        self.assertEqual(estatisticas["scripts"], 2)
        self.assertEqual(estatisticas["scripts_inline"], 1)
        self.assertEqual(estatisticas["scripts_externos"], 1)
        self.assertEqual(estatisticas["formularios"], 1)
        self.assertEqual(estatisticas["campos_formulario"], 3)
        self.assertEqual(estatisticas["imagens"], 1)
        self.assertEqual(estatisticas["iframes"], 1)
        self.assertEqual(estatisticas["comentarios"], 1)

    def test_indicadores_de_seguranca(self):
        resultado = analisar_html(
            self.html,
            self.url,
            "text/html",
        )

        tipos = {
            item.get("tipo")
            for item in resultado.indicadores
        }

        self.assertIn("autocomplete", tipos)
        self.assertIn("sandbox", tipos)
        self.assertIn("referrerpolicy", tipos)

    def test_html_nao_detectado(self):
        resultado = analisar_html(
            "texto simples sem HTML",
            "https://exemplo.test/",
            "text/plain",
        )

        self.assertFalse(resultado.detectado)
        self.assertFalse(resultado.valido)

    def test_email_e_jwt_sao_mascarados(self):
        html = """
        <html>
        <body>
            contato: teste@example.com
            token:
            eyJhbGciOiJIUzI1NiJ9.abc123.xyz789
        </body>
        </html>
        """

        resultado = analisar_html(
            html,
            "https://exemplo.test/",
            "text/html",
        )

        tipos = {
            item["tipo"]
            for item in resultado.dados_potencialmente_sensiveis
        }

        self.assertIn("email", tipos)
        self.assertIn("jwt_aparente", tipos)

        valores = [
            item["valor"]
            for item in resultado.dados_potencialmente_sensiveis
        ]

        self.assertNotIn("teste@example.com", valores)
        self.assertNotIn(
            "eyJhbGciOiJIUzI1NiJ9.abc123.xyz789",
            valores,
        )

    def test_links_a_e_fontes_sao_inventariados(self):
        html = """
        <!doctype html>
        <html>
        <head>
            <link
                rel="preload"
                as="font"
                href="/fonts/app.woff2"
                type="font/woff2"
            >
        </head>
        <body>
            <a href="/login">Login</a>
            <a href="https://externo.test/pagina">Externo</a>
            <a href="#secao">Secao</a>
        </body>
        </html>
        """

        resultado = analisar_html(
            html,
            url="https://exemplo.test/",
            content_type="text/html",
        )

        self.assertTrue(resultado.detectado)
        self.assertEqual(len(resultado.links), 4)

        navegacao = [
            item
            for item in resultado.links
            if item.get("tipo") == "navegacao"
        ]

        self.assertEqual(len(navegacao), 3)

        interno = next(
            item
            for item in navegacao
            if item.get("href") == "/login"
        )

        self.assertEqual(
            interno.get("url"),
            "https://exemplo.test/login",
        )
        self.assertFalse(interno.get("externo"))
        self.assertEqual(
            interno.get("protocolo"),
            "https",
        )

        externo = next(
            item
            for item in navegacao
            if item.get("href")
            == "https://externo.test/pagina"
        )

        self.assertTrue(externo.get("externo"))

        fragmento = next(
            item
            for item in navegacao
            if item.get("href") == "#secao"
        )

        self.assertEqual(
            fragmento.get("url"),
            "https://exemplo.test/#secao",
        )

        fontes = [
            item
            for item in resultado.recursos
            if item.get("tipo") == "fonte"
        ]

        self.assertEqual(len(fontes), 1)
        self.assertEqual(
            fontes[0].get("url"),
            "https://exemplo.test/fonts/app.woff2",
        )
        self.assertEqual(
            fontes[0].get("host"),
            "exemplo.test",
        )

        self.assertGreaterEqual(
            resultado.estatisticas.get("links", 0),
            3,
        )
        self.assertGreaterEqual(
            resultado.estatisticas.get("recursos", 0),
            1,
        )

if __name__ == "__main__":
    unittest.main()
