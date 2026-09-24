import unittest

from online.detector_biblioteca import detectar_bibliotecas


class TestDetectorBiblioteca(unittest.TestCase):
    def test_detecta_import(self):
        codigo = """
        import axios from "axios";
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["biblioteca"], "axios")
        self.assertEqual(resultado[0]["tipo"], "import")

    def test_detecta_import_sem_bind(self):
        codigo = """
        import "lodash";
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["biblioteca"], "lodash")
        self.assertEqual(resultado[0]["tipo"], "import")

    def test_detecta_import_dinamico(self):
        codigo = """
        const modulo = import("axios");
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["biblioteca"], "axios")
        self.assertEqual(resultado[0]["tipo"], "dynamic_import")

    def test_detecta_require(self):
        codigo = """
        const axios = require("axios");
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["biblioteca"], "axios")
        self.assertEqual(resultado[0]["tipo"], "require")

    def test_normaliza_submodulo(self):
        codigo = """
        import debounce from "lodash/debounce";
        import core from "axios/lib/core";
        """

        resultado = detectar_bibliotecas(codigo)

        bibliotecas = {
            item["biblioteca"]
            for item in resultado
        }

        self.assertEqual(
            bibliotecas,
            {
                "lodash",
                "axios",
            },
        )

    def test_normaliza_pacote_com_escopo(self):
        codigo = """
        import { Component } from "@angular/core";
        import helper from "@angular/common/http";
        """

        resultado = detectar_bibliotecas(codigo)

        bibliotecas = {
            item["biblioteca"]
            for item in resultado
        }

        self.assertEqual(
            bibliotecas,
            {
                "@angular/core",
                "@angular/common",
            },
        )

    def test_ignora_modulos_relativos(self):
        codigo = """
        import app from "./app.js";
        import cliente from "../cliente.js";
        import util from "/interno/util.js";
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(resultado, [])

    def test_ignora_file_e_urls(self):
        codigo = """
        import local from "file:///tmp/modulo.js";
        import remoto from "https://example.com/modulo.js";
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(resultado, [])

    def test_ignora_comentarios(self):
        codigo = """
        // import axios from "axios";

        /*
        import lodash from "lodash";
        require("vue");
        */
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(resultado, [])

    def test_ignora_texto_com_import(self):
        codigo = '''
        const texto = 'import axios from "axios"';
        const outro = "require('lodash')";
        '''

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(resultado, [])

    def test_suporta_typescript(self):
        codigo = """
        import type { AxiosInstance } from "axios";
        """

        resultado = detectar_bibliotecas(
            codigo,
            linguagem="typescript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["biblioteca"], "axios")
        self.assertEqual(resultado[0]["linguagem"], "typescript")

    def test_suporta_alias_ts(self):
        codigo = """
        import React from "react";
        """

        resultado = detectar_bibliotecas(
            codigo,
            linguagem="ts",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["linguagem"], "typescript")

    def test_ignora_linguagem_nao_suportada(self):
        codigo = """
        import axios from "axios";
        """

        resultado = detectar_bibliotecas(
            codigo,
            linguagem="python",
        )

        self.assertEqual(resultado, [])

    def test_codigo_vazio(self):
        self.assertEqual(
            detectar_bibliotecas(""),
            [],
        )

    def test_preserva_origem_arquivo_e_localizacao(self):
        codigo = """
        const inicio = true;

        import axios from "axios";
        """

        resultado = detectar_bibliotecas(
            codigo,
            origem="script",
            arquivo="https://example.com/app.js",
        )

        self.assertEqual(len(resultado), 1)

        observacao = resultado[0]

        self.assertEqual(observacao["origem"], "script")
        self.assertEqual(
            observacao["arquivo"],
            "https://example.com/app.js",
        )
        self.assertEqual(
            observacao["localizacao"]["linha"],
            4,
        )
        self.assertEqual(
            observacao["localizacao"]["coluna"],
            9,
        )
        self.assertTrue(observacao["evidencias"])
        self.assertEqual(observacao["pontuacao"], 95)
        self.assertEqual(observacao["confianca"], "ALTA")

    def test_normaliza_jsx_para_javascript(self):
        codigo = """
        import React from "react";
        """

        resultado = detectar_bibliotecas(
            codigo,
            linguagem="jsx",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0]["linguagem"],
            "javascript",
        )

    def test_normaliza_tsx_para_typescript(self):
        codigo = """
        import React from "react";
        """

        resultado = detectar_bibliotecas(
            codigo,
            linguagem="tsx",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0]["linguagem"],
            "typescript",
        )

    def test_preserva_multiplas_evidencias_da_mesma_biblioteca(self):
        codigo = """
        import axios from "axios";
        import { AxiosError } from "axios";
        const cliente = require("axios");
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(len(resultado), 1)

        observacao = resultado[0]

        self.assertEqual(
            observacao["biblioteca"],
            "axios",
        )

        self.assertEqual(
            len(observacao["evidencias"]),
            3,
        )

        tipos = [
            evidencia["tipo"]
            for evidencia in observacao["evidencias"]
        ]

        self.assertEqual(
            tipos,
            [
                "import",
                "import",
                "require",
            ],
        )

        for evidencia in observacao["evidencias"]:
            self.assertIn(
                "localizacao",
                evidencia,
            )

    def test_nao_confunde_comentario_dentro_de_string(self):
        codigo = """
        const texto = "// isto nao e comentario";
        import axios from "axios";
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["biblioteca"], "axios")

    def test_nao_detecta_require_de_objeto(self):
        codigo = """
        const objeto = {
            require(valor) {
                return valor;
            }
        };

        objeto.require("nao-e-biblioteca");
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(resultado, [])

    def test_nao_detecta_import_de_objeto(self):
        codigo = """
        objeto.import("nao-e-biblioteca");
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(resultado, [])

    def test_nao_duplica_mesma_biblioteca(self):
        codigo = """
        import axios from "axios";
        import { AxiosError } from "axios";
        const cliente = require("axios");
        """

        resultado = detectar_bibliotecas(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["biblioteca"], "axios")


if __name__ == "__main__":
    unittest.main()
