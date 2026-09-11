import unittest

from online.analisador_javascript import (
    analisar_javascript,
)


class TestAnalisadorJavaScript(unittest.TestCase):

    def test_codigo_vazio(self):
        resultado = analisar_javascript("")

        self.assertFalse(
            resultado["detectado"]
        )
        self.assertEqual(
            resultado["tamanho"],
            0,
        )

    def test_detecta_funcao(self):
        codigo = """
        function carregarDados() {
            return true;
        }
        """

        resultado = analisar_javascript(codigo)

        self.assertIn(
            "carregarDados",
            resultado["funcoes"],
        )

    def test_detecta_import(self):
        codigo = """
        import React from "react";
        import { app } from "./app.js";
        """

        resultado = analisar_javascript(codigo)

        self.assertIn(
            "react",
            resultado["imports"],
        )

        self.assertIn(
            "./app.js",
            resultado["imports"],
        )

    def test_detecta_export(self):
        codigo = """
        export function iniciar() {}

        export const configuracao = {};
        """

        resultado = analisar_javascript(codigo)

        self.assertIn(
            "iniciar",
            resultado["exports"],
        )

        self.assertIn(
            "configuracao",
            resultado["exports"],
        )

    def test_detecta_url(self):
        codigo = """
        const api =
            "https://api.exemplo.test/v1/clientes";
        """

        resultado = analisar_javascript(codigo)

        self.assertIn(
            "https://api.exemplo.test/v1/clientes",
            resultado["urls"],
        )

    def test_detecta_endpoint(self):
        codigo = """
        fetch("/api/v1/clientes");
        fetch("/auth/login");
        """

        resultado = analisar_javascript(codigo)

        self.assertIn(
            "/api/v1/clientes",
            resultado["endpoints"],
        )

        self.assertIn(
            "/auth/login",
            resultado["endpoints"],
        )

    def test_detecta_websocket(self):
        codigo = """
        const socket =
            new WebSocket("wss://ws.exemplo.test/socket");
        """

        resultado = analisar_javascript(codigo)

        self.assertIn(
            "wss://ws.exemplo.test/socket",
            resultado["websockets"],
        )

    def test_detecta_fetch(self):
        codigo = """
        fetch("/api/clientes");
        """

        resultado = analisar_javascript(codigo)

        self.assertTrue(
            resultado["caracteristicas"]["usa_fetch"]
        )

        self.assertIn(
            "/api/clientes",
            resultado["apis"]["fetch"],
        )

    def test_detecta_xmlhttprequest(self):
        codigo = """
        const xhr = new XMLHttpRequest();
        xhr.open("GET", "/api/status");
        """

        resultado = analisar_javascript(codigo)

        self.assertTrue(
            resultado["caracteristicas"]["usa_xhr"]
        )

        self.assertIn(
            "/api/status",
            resultado["apis"]["xmlhttprequest"],
        )

    def test_detecta_axios(self):
        codigo = """
        axios.get("/api/clientes");
        axios.post("/api/login");
        """

        resultado = analisar_javascript(codigo)

        self.assertIn(
            "/api/clientes",
            resultado["apis"]["axios"],
        )

        self.assertIn(
            "/api/login",
            resultado["apis"]["axios"],
        )

    def test_detecta_frameworks(self):
        codigo = """
        import React from "react";
        import Vue from "vue";
        """

        resultado = analisar_javascript(codigo)

        self.assertIn(
            "react",
            resultado["frameworks"],
        )

        self.assertIn(
            "vue",
            resultado["frameworks"],
        )

    def test_detecta_caracteristicas(self):
        codigo = """
        async function carregar() {
            const resposta =
                await fetch("/api/dados");

            const socket =
                new WebSocket("wss://exemplo.test/ws");
        }
        """

        resultado = analisar_javascript(codigo)

        caracteristicas = (
            resultado["caracteristicas"]
        )

        self.assertTrue(
            caracteristicas["usa_fetch"]
        )

        self.assertTrue(
            caracteristicas["usa_websocket"]
        )

        self.assertTrue(
            caracteristicas["usa_async"]
        )

    def test_detecta_modules(self):
        codigo = """
        import { cliente } from "./cliente.js";

        export function iniciar() {}
        """

        resultado = analisar_javascript(codigo)

        self.assertTrue(
            resultado["caracteristicas"]["usa_modules"]
        )
    def test_detecta_padroes_sensiveis(self):
        codigo = """
        const token = document.cookie;

        localStorage.setItem("token", token);

        const sessao =
            sessionStorage.getItem("sessao");

        const executar =
            new Function("return 1 + 1");

        const xhr =
            new XMLHttpRequest();

        const ws =
            new WebSocket(
                "wss://ws.exemplo.test/socket"
            );
        """

        resultado = analisar_javascript(codigo)

        padroes = resultado["padroes_sensiveis"]

        self.assertTrue(
            padroes["document_cookie"]
        )

        self.assertTrue(
            padroes["local_storage"]
        )

        self.assertTrue(
            padroes["session_storage"]
        )

        self.assertTrue(
            padroes["new_function"]
        )

        self.assertTrue(
            padroes["xmlhttprequest"]
        )

        self.assertTrue(
            padroes["websocket"]
        )


    def test_inspecao_profunda(self):
        codigo = """
        const token = document.cookie;

        localStorage.setItem(
            "token",
            token
        );

        const xhr =
            new XMLHttpRequest();

        xhr.open(
            "POST",
            "https://api.exemplo.test/api/login"
        );

        const ws =
            new WebSocket(
                "wss://ws.exemplo.test/socket"
            );

        fetch(
            "https://api.exemplo.test/api/dados",
            {
                method: "GET",
                headers: {
                    Authorization:
                        "Bearer exemplo"
                }
            }
        );
        """

        resultado = analisar_javascript(codigo)

        profunda = resultado[
            "inspecao_profunda"
        ]

        self.assertIn(
            "https://api.exemplo.test/api/login",
            profunda["urls_http"],
        )

        self.assertIn(
            "https://api.exemplo.test/api/dados",
            profunda["urls_http"],
        )

        self.assertIn(
            "wss://ws.exemplo.test/socket",
            profunda["urls_websocket"],
        )

        self.assertEqual(
            profunda["metodos_http"]["POST"],
            1,
        )

        self.assertEqual(
            profunda["metodos_http"]["GET"],
            1,
        )

        indicadores = profunda[
            "indicadores_sensiveis"
        ]

        self.assertIn(
            "localStorage",
            indicadores,
        )

        self.assertIn(
            "document.cookie",
            indicadores,
        )

        self.assertIn(
            "Authorization",
            indicadores,
        )

        self.assertIn(
            "Bearer",
            indicadores,
        )

        self.assertIn(
            "XMLHttpRequest",
            indicadores,
        )

        self.assertIn(
            "WebSocket",
            indicadores,
        )


    def test_inspecao_profunda_resumo(self):
        codigo = """
        fetch("https://api.exemplo.test/dados");

        const ws =
            new WebSocket(
                "wss://ws.exemplo.test/socket"
            );

        const xhr =
            new XMLHttpRequest();

        xhr.open(
            "POST",
            "https://api.exemplo.test/login"
        );
        """

        resultado = analisar_javascript(codigo)

        resumo = resultado[
            "inspecao_profunda"
        ]["resumo"]

        self.assertEqual(
            resumo["urls_http"],
            2,
        )

        self.assertEqual(
            resumo["urls_websocket"],
            1,
        )

        self.assertEqual(
            resumo["metodos_http"],
            1,
        )

        self.assertGreaterEqual(
            resumo["indicadores_sensiveis"],
            2,
        )
    def test_detecta_dom_sinks(self):
        codigo = """
        const elemento = document.createElement("div");

        elemento.innerHTML = resposta;

        elemento.outerHTML = conteudo;

        elemento.insertAdjacentHTML(
            "beforeend",
            html
        );

        document.write(html);
        """

        resultado = analisar_javascript(codigo)

        sinks = resultado["dom_sinks"]

        tipos = {
            item["tipo"]
            for item in sinks
        }

        self.assertIn(
            "innerHTML",
            tipos,
        )

        self.assertIn(
            "outerHTML",
            tipos,
        )

        self.assertIn(
            "insertAdjacentHTML",
            tipos,
        )

        self.assertIn(
            "document.write",
            tipos,
        )

    def test_detecta_fontes_de_dados(self):
        codigo = """
        const xhr = new XMLHttpRequest();

        xhr.onload = function () {
            const dados = xhr.response;
            const texto = xhr.responseText;
        };

        fetch("/api/dados");
        """

        resultado = analisar_javascript(codigo)

        fontes = resultado["fontes_dados"]

        tipos = {
            item["tipo"]
            for item in fontes
        }

        self.assertIn(
            "XMLHttpRequest.response",
            tipos,
        )

        self.assertIn(
            "XMLHttpRequest.responseText",
            tipos,
        )

        self.assertIn(
            "fetch",
            tipos,
        )

    def test_detecta_cadeia_fonte_dom_sink(self):
        codigo = """
        const xhr = new XMLHttpRequest();

        xhr.onload = function () {
            elemento.innerHTML = xhr.response;
        };
        """

        resultado = analisar_javascript(codigo)

        fontes = resultado["fontes_dados"]
        sinks = resultado["dom_sinks"]

        self.assertTrue(
            any(
                item["tipo"] == "XMLHttpRequest.response"
                for item in fontes
            )
        )

        self.assertTrue(
            any(
                item["tipo"] == "innerHTML"
                for item in sinks
            )
        )

    def test_analisar_javascript_inventaria_requisicoes_http(self):
        from online.analisador_javascript import analisar_javascript

        codigo = """
    fetch("/api/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer segredo-lab"
        },
        body: JSON.stringify(dados)
    });

    const xhr = new XMLHttpRequest();
    xhr.open("GET", "/api/clientes");
    xhr.setRequestHeader("X-Lab-Test", "laboratorio");
    xhr.send();

    axios.post("/api/pagamentos", dados, {
        headers: {
            "Content-Type": "application/json"
        }
    });
    """

        resultado = analisar_javascript(codigo)

        requisicoes = resultado["requisicoes_http"]

        self.assertEqual(len(requisicoes), 3)

        fetch = requisicoes[0]

        self.assertEqual(fetch["tipo"], "fetch")
        self.assertEqual(fetch["metodo"], "POST")
        self.assertEqual(fetch["url"], "/api/login")
        self.assertEqual(fetch["body"], "JSON.stringify(dados)")

        nomes_fetch = {
            header["nome"]
            for header in fetch["headers"]
        }

        self.assertIn("Content-Type", nomes_fetch)
        self.assertIn("Authorization", nomes_fetch)

        valores_fetch = " ".join(
            header["valor"]
            for header in fetch["headers"]
        )

        self.assertNotIn("segredo-lab", valores_fetch)
        self.assertIn("[VALOR_REDACTED]", valores_fetch)

        xhr = requisicoes[1]

        self.assertEqual(xhr["tipo"], "xmlhttprequest")
        self.assertEqual(xhr["metodo"], "GET")
        self.assertEqual(xhr["url"], "/api/clientes")

        nomes_xhr = {
            header["nome"]
            for header in xhr["headers"]
        }

        self.assertIn("X-Lab-Test", nomes_xhr)

        axios = requisicoes[2]

        self.assertEqual(axios["tipo"], "axios")
        self.assertEqual(axios["metodo"], "POST")
        self.assertEqual(axios["url"], "/api/pagamentos")
        self.assertEqual(axios["body"], "dados")

        nomes_axios = {
            header["nome"]
            for header in axios["headers"]
        }

        self.assertIn("Content-Type", nomes_axios)

if __name__ == "__main__":
    unittest.main()
