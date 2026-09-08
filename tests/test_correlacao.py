import unittest

from online.correlacao import (
    Correlacao,
    correlacionar_javascript,
    ordenar_correlacoes,
)


class TestCorrelacaoJavaScript(unittest.TestCase):

    def test_detecta_fonte_xmlhttprequest_para_innerhtml(self):
        analises = [
            {
                "origem": "inline",
                "tipo": "script",
                "url": "",
                "analise": {
                    "dom_sinks": [
                        {
                            "tipo": "innerHTML",
                            "linha": 4,
                            "conteudo": "element.innerHTML = xhr.response;",
                        }
                    ],
                    "fontes_dados": [
                        {
                            "tipo": "XMLHttpRequest.response",
                            "linha": 4,
                            "conteudo": "element.innerHTML = xhr.response;",
                        }
                    ],
                },
            }
        ]

        resultado = correlacionar_javascript(analises)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0].identificador,
            "CORR-JS-DOM-SOURCE-SINK",
        )
        self.assertEqual(
            resultado[0].categoria,
            "javascript",
        )
        self.assertEqual(
            resultado[0].severidade,
            "baixo",
        )

    def test_nao_cria_correlacao_sem_sink(self):
        analises = [
            {
                "origem": "inline",
                "tipo": "script",
                "url": "",
                "analise": {
                    "dom_sinks": [],
                    "fontes_dados": [
                        {
                            "tipo": "XMLHttpRequest.response",
                            "linha": 4,
                            "conteudo": "const dados = xhr.response;",
                        }
                    ],
                },
            }
        ]

        resultado = correlacionar_javascript(analises)

        self.assertEqual(resultado, [])

    def test_nao_cria_correlacao_sem_fonte(self):
        analises = [
            {
                "origem": "inline",
                "tipo": "script",
                "url": "",
                "analise": {
                    "dom_sinks": [
                        {
                            "tipo": "innerHTML",
                            "linha": 4,
                            "conteudo": "element.innerHTML = valor;",
                        }
                    ],
                    "fontes_dados": [],
                },
            }
        ]

        resultado = correlacionar_javascript(analises)

        self.assertEqual(resultado, [])

    def test_correlacao_javascript_tem_metadados(self):
        analises = [
            {
                "origem": "inline",
                "tipo": "script",
                "url": "https://exemplo.test/",
                "analise": {
                    "dom_sinks": [
                        {
                            "tipo": "innerHTML",
                            "linha": 4,
                            "conteudo": "element.innerHTML = xhr.response;",
                        }
                    ],
                    "fontes_dados": [
                        {
                            "tipo": "XMLHttpRequest.response",
                            "linha": 4,
                            "conteudo": "element.innerHTML = xhr.response;",
                        }
                    ],
                },
            }
        ]

        resultado = correlacionar_javascript(analises)

        self.assertEqual(len(resultado), 1)

        correlacao = resultado[0]

        self.assertEqual(
            correlacao.confianca,
            "ALTA",
        )
        self.assertEqual(
            correlacao.metadados["origem"],
            "inline",
        )
        self.assertEqual(
            correlacao.metadados["url"],
            "https://exemplo.test/",
        )
        self.assertEqual(
            correlacao.metadados["sink"],
            "innerHTML",
        )
        self.assertEqual(
            correlacao.metadados["source"],
            "XMLHttpRequest.response",
        )

    def test_ordenacao_preserva_correlacoes(self):
        analises = [
            {
                "origem": "inline",
                "tipo": "script",
                "url": "",
                "analise": {
                    "dom_sinks": [
                        {
                            "tipo": "innerHTML",
                            "linha": 4,
                            "conteudo": "element.innerHTML = xhr.response;",
                        }
                    ],
                    "fontes_dados": [
                        {
                            "tipo": "XMLHttpRequest.response",
                            "linha": 4,
                            "conteudo": "element.innerHTML = xhr.response;",
                        }
                    ],
                },
            }
        ]

        resultado = correlacionar_javascript(analises)
        ordenado = ordenar_correlacoes(resultado)

        self.assertEqual(len(ordenado), 1)
        self.assertIsInstance(
            ordenado[0],
            Correlacao,
        )

    def test_detecta_fluxo_fonte_variavel_para_dom_sink(self):
        analises = [
            {
                "origem": "inline",
                "tipo": "script",
                "url": "",
                "analise": {
                    "dom_sinks": [
                        {
                            "tipo": "innerHTML",
                            "linha": 6,
                            "conteudo": "element.innerHTML = resposta;",
                        }
                    ],
                    "fontes_dados": [
                        {
                            "tipo": "XMLHttpRequest.response",
                            "linha": 3,
                            "conteudo": "const resposta = xhr.response;",
                        }
                    ],
                },
            }
        ]

        resultado = correlacionar_javascript(analises)

        self.assertEqual(len(resultado), 1)

        correlacao = resultado[0]

        self.assertEqual(
            correlacao.identificador,
            "CORR-JS-FLUXO-DOM-SOURCE-SINK",
        )
        self.assertEqual(
            correlacao.metadados["source"],
            "XMLHttpRequest.response",
        )
        self.assertEqual(
            correlacao.metadados["sink"],
            "innerHTML",
        )
        self.assertEqual(
            correlacao.metadados["variavel"],
            "resposta",
        )

    def test_detecta_fluxo_response_text_para_dom_sink(self):
        analises = [
            {
                "origem": "inline",
                "tipo": "script",
                "url": "",
                "analise": {
                    "dom_sinks": [
                        {
                            "tipo": "innerHTML",
                            "linha": 6,
                            "conteudo": "element.innerHTML = resultado;",
                        }
                    ],
                    "fontes_dados": [
                        {
                            "tipo": "XMLHttpRequest.responseText",
                            "linha": 3,
                            "conteudo": "var resultado = xhr.responseText;",
                        }
                    ],
                },
            }
        ]

        resultado = correlacionar_javascript(analises)

        self.assertEqual(len(resultado), 1)

        correlacao = resultado[0]

        self.assertEqual(
            correlacao.identificador,
            "CORR-JS-FLUXO-DOM-SOURCE-SINK",
        )
        self.assertEqual(
            correlacao.metadados["source"],
            "XMLHttpRequest.responseText",
        )
        self.assertEqual(
            correlacao.metadados["sink"],
            "innerHTML",
        )
        self.assertEqual(
            correlacao.metadados["variavel"],
            "resultado",
        )
