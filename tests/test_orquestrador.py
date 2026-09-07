import unittest
from unittest.mock import patch

from online.modelos import (
    HTTPHeader,
    HTTPResposta,
    ServicoObservado,
    ServidorObservado,
)
from online.orquestrador import analisar_online


class TestOrquestrador(unittest.TestCase):

    def criar_resposta(self):
        return HTTPResposta(
            url="https://exemplo.test/",
            status_code=200,
            reason="OK",
            http_version="HTTP/1.1",
            headers=[
                HTTPHeader(
                    nome="Server",
                    valor="nginx/1.24.0",
                ),
                HTTPHeader(
                    nome="Content-Type",
                    valor="text/html",
                ),
            ],
            content_type="text/html",
            tamanho=20,
            corpo="<html>teste</html>",
            tempo_resposta_ms=12.5,
        )

    @patch("online.orquestrador.construir_inventario")
    @patch("online.orquestrador.analisar_portas")
    @patch("online.orquestrador.analisar_tls")
    @patch("online.orquestrador.coletar")
    def test_fluxo_principal(
        self,
        mock_coletar,
        mock_tls,
        mock_portas,
        mock_inventario,
    ):
        resposta = self.criar_resposta()

        mock_coletar.return_value.sucesso = True
        mock_coletar.return_value.respostas = [resposta]
        mock_coletar.return_value.cookies = []
        mock_coletar.return_value.erros = []

        mock_tls.return_value = {
            "detectado": True,
            "sucesso": True,
            "url": "https://exemplo.test/",
            "host": "exemplo.test",
            "porta": 443,
            "versao_tls": "TLSv1.3",
            "cipher": {
                "nome": "TLS_AES_256_GCM_SHA384",
                "protocolo": "TLSv1.3",
                "bits": 256,
            },
            "alpn": "http/1.1",
            "certificado": {
                "not_after": "Jan 01 00:00:00 2030 GMT",
                "dias_para_expirar": 1000,
                "subject_alt_names": [
                    "exemplo.test",
                ],
            },
            "erros": [],
        }

        mock_portas.return_value = []

        mock_inventario.return_value = {
            "alvo": "https://exemplo.test/",
        }

        resultado = analisar_online(
            "https://exemplo.test/",
            timeout=5,
            analisar_certificado=True,
        )

        self.assertTrue(resultado.sucesso)

        self.assertEqual(
            len(resultado.respostas),
            1,
        )

        self.assertIsNotNone(
            resultado.tls
        )

        self.assertEqual(
            resultado.tls.protocolo,
            "TLSv1.3",
        )

        self.assertTrue(
            any(
                evidencia.identificador == "HTTP-STATUS"
                for evidencia in resultado.evidencias
            )
        )

        self.assertTrue(
            any(
                evidencia.identificador == "TLS-CONEXAO"
                for evidencia in resultado.evidencias
            )
        )

        self.assertTrue(
            any(
                servidor.produto.lower() == "nginx"
                for servidor in resultado.servidores
            )
        )

        self.assertIn(
            "correlacoes",
            resultado.metadados,
        )

        self.assertIn(
            "inventario_superficie",
            resultado.metadados,
        )

        mock_coletar.assert_called_once()
        mock_tls.assert_called_once()
        mock_inventario.assert_called_once()

    @patch("online.orquestrador.analisar_portas")
    @patch("online.orquestrador.analisar_tls")
    @patch("online.orquestrador.coletar")
    def test_portas_sao_verificadas_somente_quando_fornecidas(
        self,
        mock_coletar,
        mock_tls,
        mock_portas,
    ):
        resposta = self.criar_resposta()

        mock_coletar.return_value.sucesso = True
        mock_coletar.return_value.respostas = [resposta]
        mock_coletar.return_value.cookies = []
        mock_coletar.return_value.erros = []

        mock_tls.return_value = {
            "detectado": False,
            "sucesso": False,
            "url": "https://exemplo.test/",
            "erros": [],
        }

        mock_portas.return_value = []

        with patch(
            "online.orquestrador.construir_inventario"
        ) as mock_inventario:
            mock_inventario.return_value = {
                "alvo": "https://exemplo.test/",
            }

            analisar_online(
                "https://exemplo.test/",
                portas=[80, 443],
            )

        mock_portas.assert_called_once_with(
            host="exemplo.test",
            portas=[80, 443],
            timeout=10.0,
        )

    @patch("online.orquestrador.construir_inventario")
    @patch("online.orquestrador.analisar_portas")
    @patch("online.orquestrador.analisar_tls")
    @patch("online.orquestrador.coletar")
    def test_integracao_javascript_na_analise_online(
        self,
        mock_coletar,
        mock_tls,
        mock_portas,
        mock_inventario,
    ):
        resposta = self.criar_resposta()

        resposta.corpo = """
        <!DOCTYPE html>
        <html>
        <head>
            <script>
                function iniciar() {
                    return fetch("/api/login");
                }

                const socket = new WebSocket(
                    "wss://exemplo.test/socket"
                );

                const xhr = new XMLHttpRequest();
                element.innerHTML = xhr.response;

                const mensagem = "aHR0cHM6Ly9leGVtcGxvLnRlc3Q=";
            </script>
        </head>
        <body>
            <h1>Teste</h1>
        </body>
        </html>
        """

        mock_coletar.return_value.sucesso = True
        mock_coletar.return_value.respostas = [resposta]
        mock_coletar.return_value.cookies = []
        mock_coletar.return_value.erros = []

        mock_tls.return_value = {
            "detectado": False,
            "sucesso": False,
            "url": "https://exemplo.test/",
            "erros": [],
        }

        mock_portas.return_value = []

        mock_inventario.return_value = {
            "alvo": "https://exemplo.test/",
        }

        resultado = analisar_online(
            "https://exemplo.test/",
            timeout=5,
            analisar_certificado=True,
        )

        self.assertIn(
            "javascript",
            resultado.metadados,
        )

        javascript = resultado.metadados["javascript"]

        self.assertEqual(
            len(javascript),
            1,
        )

        self.assertEqual(
            javascript[0]["url"],
            "https://exemplo.test/",
        )

        self.assertEqual(
            len(javascript[0]["scripts"]),
            1,
        )

        self.assertEqual(
            javascript[0]["scripts"][0]["origem"],
            "script_inline",
        )

        self.assertEqual(
            len(javascript[0]["analises"]),
            1,
        )

        analise = javascript[0]["analises"][0]["analise"]

        self.assertTrue(
            analise["detectado"]
        )

        self.assertTrue(
            any(
                "iniciar" in funcao
                for funcao in analise["funcoes"]
            )
        )

        self.assertIn(
            "/api/login",
            analise["endpoints"],
        )

        self.assertIn(
            "wss://exemplo.test/socket",
            analise["websockets"],
        )

        self.assertTrue(
            analise["caracteristicas"]["usa_fetch"]
        )

        self.assertTrue(
            analise["caracteristicas"]["usa_websocket"]
        )

        strings = javascript[0]["analises"][0]["strings"]

        self.assertTrue(
            any(
                item["original"]
                == "aHR0cHM6Ly9leGVtcGxvLnRlc3Q="
                for item in strings
            )
        )

        correlacoes = resultado.metadados["correlacoes"]

        self.assertTrue(
            any(
                correlacao.identificador
                == "CORR-JS-DOM-SOURCE-SINK"
                for correlacao in correlacoes
            )
        )

if __name__ == "__main__":
    unittest.main()
