import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from online.cliente_http import USER_AGENT, coletar


class _ServidorTeste(BaseHTTPRequestHandler):

    corpo = b"Resposta de teste do Codificador Universal."

    def do_GET(self):
        self.server.metodo_recebido = "GET"
        self.server.user_agent_recebido = self.headers.get(
            "User-Agent",
            "",
        )

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(self.corpo)),
        )
        self.end_headers()

        self.wfile.write(self.corpo)

    def log_message(self, format, *args):
        pass


class TestClienteHTTP(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(
            ("127.0.0.1", 0),
            _ServidorTeste,
        )

        cls.porta = cls.servidor.server_address[1]

        cls.thread = threading.Thread(
            target=cls.servidor.serve_forever,
            daemon=True,
        )

        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.thread.join(timeout=2)

    def _url(self):
        return f"http://127.0.0.1:{self.porta}/teste"

    def test_coleta_resposta_200(self):
        resultado = coletar(
            self._url(),
            timeout=2,
        )

        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.erros, [])
        self.assertEqual(len(resultado.respostas), 1)

        resposta = resultado.respostas[0]

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.content_type,
            "text/plain; charset=utf-8",
        )
        self.assertEqual(
            resposta.corpo,
            "Resposta de teste do Codificador Universal.",
        )

    def test_envia_get_e_user_agent(self):
        resultado = coletar(
            self._url(),
            timeout=2,
        )

        self.assertTrue(resultado.sucesso)

        self.assertEqual(
            self.servidor.metodo_recebido,
            "GET",
        )

        self.assertEqual(
            self.servidor.user_agent_recebido,
            USER_AGENT,
        )

    def test_limite_do_corpo(self):
        resultado = coletar(
            self._url(),
            timeout=2,
            max_bytes=10,
        )

        self.assertTrue(resultado.sucesso)

        resposta = resultado.respostas[0]

        self.assertEqual(
            resposta.tamanho,
            10,
        )

        self.assertEqual(
            len(resposta.corpo.encode("utf-8")),
            10,
        )

        self.assertTrue(
            resultado.metadados["corpo_truncado"]
        )

        self.assertEqual(
            resultado.metadados["limite_corpo_bytes"],
            10,
        )


if __name__ == "__main__":
    unittest.main()
