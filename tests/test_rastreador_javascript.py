import unittest

from online.rastreador_javascript import (
    explicar_cadeia_variaveis,
)


class TestRastreadorJavaScript(unittest.TestCase):

    def test_explica_cadeia_de_variaveis(self):
        cadeia = [
            "resposta",
            "dados",
            "corpo",
            "valor",
        ]

        resultado = explicar_cadeia_variaveis(cadeia)

        self.assertEqual(
            resultado["origem"],
            "resposta",
        )
        self.assertEqual(
            resultado["destino"],
            "valor",
        )
        self.assertEqual(
            resultado["total_etapas"],
            3,
        )
        self.assertEqual(
            resultado["cadeia"],
            [
                "resposta",
                "dados",
                "corpo",
                "valor",
            ],
        )

    def test_gera_fluxo_visual(self):
        cadeia = [
            "resposta",
            "dados",
            "corpo",
            "valor",
        ]

        resultado = explicar_cadeia_variaveis(cadeia)

        self.assertEqual(
            resultado["fluxo_visual"],
            (
                "resposta\n"
                "   ↓\n"
                "dados\n"
                "   ↓\n"
                "corpo\n"
                "   ↓\n"
                "valor"
            ),
        )

    def test_cadeia_vazia(self):
        resultado = explicar_cadeia_variaveis([])

        self.assertEqual(
            resultado,
            {
                "origem": None,
                "destino": None,
                "total_etapas": 0,
                "cadeia": [],
                "fluxo_visual": "",
            },
        )

    def test_uma_variavel(self):
        resultado = explicar_cadeia_variaveis(
            ["valor"]
        )

        self.assertEqual(
            resultado["origem"],
            "valor",
        )
        self.assertEqual(
            resultado["destino"],
            "valor",
        )
        self.assertEqual(
            resultado["total_etapas"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
