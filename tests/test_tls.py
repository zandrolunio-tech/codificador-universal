import unittest
from unittest.mock import patch

from online.analisador_tls import (
    _dias_para_expirar,
    _parse_data_certificado,
    analisar_tls,
)


class TestFuncoesTLS(unittest.TestCase):

    def test_parse_data_certificado_valida(self):
        resultado = _parse_data_certificado(
            "Jan 02 03:04:05 2030 GMT"
        )

        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.year, 2030)
        self.assertEqual(resultado.month, 1)
        self.assertEqual(resultado.day, 2)

    def test_parse_data_certificado_invalida(self):
        resultado = _parse_data_certificado(
            "data-invalida"
        )

        self.assertIsNone(resultado)

    def test_parse_data_certificado_vazia(self):
        self.assertIsNone(
            _parse_data_certificado("")
        )

    def test_dias_para_expirar_sem_data(self):
        self.assertIsNone(
            _dias_para_expirar(None)
        )


class TestAnalisadorTLS(unittest.TestCase):

    def test_rejeita_http(self):
        resultado = analisar_tls(
            "http://127.0.0.1"
        )

        self.assertFalse(resultado["detectado"])
        self.assertFalse(resultado["sucesso"])
        self.assertEqual(
            resultado["erro"],
            "O alvo não utiliza HTTPS.",
        )

    def test_rejeita_hostname_ausente(self):
        resultado = analisar_tls(
            "https:///caminho"
        )

        self.assertFalse(resultado["detectado"])
        self.assertFalse(resultado["sucesso"])
        self.assertEqual(
            resultado["erro"],
            "Hostname não identificado.",
        )

    @patch(
        "online.analisador_tls.socket.create_connection"
    )
    def test_timeout(self, mock_create_connection):
        mock_create_connection.side_effect = TimeoutError(
            "tempo excedido"
        )

        resultado = analisar_tls(
            "https://127.0.0.1",
            timeout=1,
        )

        self.assertTrue(resultado["detectado"])
        self.assertFalse(resultado["sucesso"])
        self.assertEqual(
            resultado["host"],
            "127.0.0.1",
        )
        self.assertEqual(
            resultado["porta"],
            443,
        )
        self.assertEqual(
            len(resultado["erros"]),
            1,
        )
        self.assertIn(
            "Timeout:",
            resultado["erros"][0],
        )

    @patch(
        "online.analisador_tls.socket.create_connection"
    )
    def test_usa_porta_https_padrao(
        self,
        mock_create_connection,
    ):
        mock_create_connection.side_effect = OSError(
            "falha controlada"
        )

        resultado = analisar_tls(
            "https://exemplo.test",
            timeout=1,
        )

        mock_create_connection.assert_called_once_with(
            ("exemplo.test", 443),
            timeout=1,
        )

        self.assertTrue(resultado["detectado"])
        self.assertEqual(
            resultado["porta"],
            443,
        )
        self.assertFalse(resultado["sucesso"])

    @patch(
        "online.analisador_tls.socket.create_connection"
    )
    def test_usa_porta_https_explicitamente(
        self,
        mock_create_connection,
    ):
        mock_create_connection.side_effect = OSError(
            "falha controlada"
        )

        resultado = analisar_tls(
            "https://exemplo.test:8443",
            timeout=2,
        )

        mock_create_connection.assert_called_once_with(
            ("exemplo.test", 8443),
            timeout=2,
        )

        self.assertEqual(
            resultado["porta"],
            8443,
        )


if __name__ == "__main__":
    unittest.main()
