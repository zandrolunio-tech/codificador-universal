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


if __name__ == "__main__":
    unittest.main()
