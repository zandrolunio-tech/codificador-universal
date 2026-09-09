import unittest

from online.rastreador_javascript import (
    analisar_transformacoes_javascript,
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


    def test_detecta_json_parse(self):
        codigo = "const dados = JSON.parse(resposta);"

        resultado = analisar_transformacoes_javascript(codigo)

        self.assertEqual(
            resultado,
            [
                {
                    "tipo": "transformacao",
                    "operacao": "JSON.parse",
                    "entrada": "resposta",
                    "saida": "dados",
                }
            ],
        )

    def test_detecta_acesso_propriedade(self):
        codigo = "const nome = dados.user.name;"

        resultado = analisar_transformacoes_javascript(codigo)

        self.assertEqual(
            resultado,
            [
                {
                    "tipo": "propriedade",
                    "operacao": "dados.user.name",
                    "entrada": "dados",
                    "propriedade": "user.name",
                    "saida": "nome",
                }
            ],
        )

    def test_mantem_ordem_das_transformacoes(self):
        codigo = """
const nome = dados.user.name;
const dados = JSON.parse(resposta);
"""

        resultado = analisar_transformacoes_javascript(codigo)

        self.assertEqual(
            resultado,
            [
                {
                    "tipo": "propriedade",
                    "operacao": "dados.user.name",
                    "entrada": "dados",
                    "propriedade": "user.name",
                    "saida": "nome",
                },
                {
                    "tipo": "transformacao",
                    "operacao": "JSON.parse",
                    "entrada": "resposta",
                    "saida": "dados",
                },
            ],
        )


    def test_detecta_transformacoes_em_cadeia(self):
        codigo = """
const resposta = xhr.responseText;
const dados = JSON.parse(resposta);
const nome = dados.user.name;
"""

        resultado = analisar_transformacoes_javascript(codigo)

        self.assertEqual(
            resultado,
            [
                {
                    "tipo": "transformacao",
                    "operacao": "JSON.parse",
                    "entrada": "resposta",
                    "saida": "dados",
                },
                {
                    "tipo": "propriedade",
                    "operacao": "dados.user.name",
                    "entrada": "dados",
                    "propriedade": "user.name",
                    "saida": "nome",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
