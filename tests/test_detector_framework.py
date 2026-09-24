import unittest

from online.detector_framework import detectar_frameworks


class TestDetectorFramework(unittest.TestCase):

    def test_detecta_react_por_import(self):
        codigo = """
        import React from "react";
        """

        resultado = detectar_frameworks(
            codigo,
            origem="script_inline",
            arquivo="app.js",
        )

        self.assertEqual(
            len(resultado),
            1,
        )

        observacao = resultado[0]

        self.assertEqual(
            observacao["framework"],
            "react",
        )

        self.assertEqual(
            observacao["tipo"],
            "import",
        )

        self.assertEqual(
            observacao["pontuacao"],
            95,
        )

        self.assertEqual(
            observacao["confianca"],
            "ALTA",
        )

        self.assertEqual(
            observacao["origem"],
            "script_inline",
        )

        self.assertEqual(
            observacao["arquivo"],
            "app.js",
        )

    def test_detecta_react_por_require_sem_duplicar_simbolo(self):
        codigo = """
        const React = require("react");
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertEqual(
            len(resultado),
            1,
        )

        self.assertEqual(
            resultado[0]["framework"],
            "react",
        )

        self.assertEqual(
            resultado[0]["tipo"],
            "require",
        )

        self.assertEqual(
            resultado[0]["pontuacao"],
            95,
        )

        self.assertEqual(
            resultado[0]["confianca"],
            "ALTA",
        )

    def test_import_forte_nao_duplica_simbolo_do_mesmo_framework(self):
        codigo = '''
import React from "react";
const app = React.createElement("div");
'''

        resultado = detectar_frameworks(
            codigo,
            origem="inline",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0]["framework"],
            "react",
        )
        self.assertEqual(
            resultado[0]["tipo"],
            "import",
        )
        self.assertEqual(
            resultado[0]["pontuacao"],
            95,
        )
        self.assertEqual(
            resultado[0]["confianca"],
            "ALTA",
        )

    def test_detecta_multiplos_frameworks(self):
        codigo = """
        import React from "react";
        import Vue from "vue";
        """

        resultado = detectar_frameworks(
            codigo
        )

        frameworks = {
            item["framework"]
            for item in resultado
        }

        self.assertIn(
            "react",
            frameworks,
        )

        self.assertIn(
            "vue",
            frameworks,
        )

    def test_detecta_angular(self):
        codigo = """
        import { Component } from "@angular/core";
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertTrue(
            any(
                item["framework"] == "angular"
                and item["tipo"] == "import"
                for item in resultado
            )
        )

    def test_detecta_next(self):
        codigo = """
        import Link from "next/link";
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertTrue(
            any(
                item["framework"] == "next.js"
                for item in resultado
            )
        )

    def test_detecta_nuxt(self):
        codigo = """
        import Nuxt from "nuxt";
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertTrue(
            any(
                item["framework"] == "nuxt"
                for item in resultado
            )
        )

    def test_detecta_svelte(self):
        codigo = """
        import App from "svelte";
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertTrue(
            any(
                item["framework"] == "svelte"
                for item in resultado
            )
        )

    def test_detecta_jquery_por_import(self):
        codigo = """
        import $ from "jquery";
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertTrue(
            any(
                item["framework"] == "jquery"
                and item["tipo"] == "import"
                for item in resultado
            )
        )

    def test_detecta_jquery_por_chamada(self):
        codigo = """
        $(".botao").addClass("ativo");
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertTrue(
            any(
                item["framework"] == "jquery"
                and item["tipo"] == "chamada_dollar"
                for item in resultado
            )
        )

    def test_ignora_comentarios(self):
        codigo = """
        // import React from "react";
        /*
            import Vue from "vue";
        */
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertEqual(
            resultado,
            [],
        )

    def test_ignora_string_comum(self):
        codigo = """
        const texto =
            "import React from 'react'";
        """

        resultado = detectar_frameworks(
            codigo
        )

        self.assertEqual(
            resultado,
            [],
        )

    def test_localizacao(self):
        codigo = (
            "\n"
            "\n"
            'import React from "react";'
        )

        resultado = detectar_frameworks(
            codigo
        )

        self.assertEqual(
            resultado[0]["localizacao"]["linha"],
            3,
        )

    def test_linguagem_typescript(self):
        codigo = """
        import React from "react";
        """

        resultado = detectar_frameworks(
            codigo,
            linguagem="typescript",
        )

        self.assertTrue(
            resultado
        )

    def test_linguagem_python_nao_e_suportada(self):
        codigo = """
        import React from "react"
        """

        resultado = detectar_frameworks(
            codigo,
            linguagem="python",
        )

        self.assertEqual(
            resultado,
            [],
        )

    def test_codigo_vazio(self):
        resultado = detectar_frameworks("")

        self.assertEqual(
            resultado,
            [],
        )


if __name__ == "__main__":
    unittest.main()
