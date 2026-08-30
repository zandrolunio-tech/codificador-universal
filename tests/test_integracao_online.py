import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from online.orquestrador import analisar_online


class HandlerTeste(BaseHTTPRequestHandler):

    server_version = "nginx/1.24.0"
    sys_version = ""

    def do_GET(self):
        corpo = b"<html><body>teste local</body></html>"

        self.send_response(200)
        # O header Server já é criado por send_response().
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header(
            "Set-Cookie",
            "sessao=teste-local; HttpOnly; Secure; SameSite=Lax",
        )
        self.send_header(
            "Content-Length",
            str(len(corpo)),
        )
        self.end_headers()

        self.wfile.write(corpo)

    def log_message(self, format, *args):
        pass


class TestIntegracaoOnline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.servidor = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            HandlerTeste,
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

    def test_pipeline_online_completo(self):
        alvo = f"http://127.0.0.1:{self.porta}/"

        resultado = analisar_online(
            alvo,
            timeout=5,
            analisar_certificado=False,
        )

        self.assertTrue(resultado.sucesso)

        self.assertEqual(
            len(resultado.respostas),
            1,
        )

        resposta = resultado.respostas[0]

        self.assertEqual(
            resposta.status_code,
            200,
        )

        self.assertEqual(
            resposta.content_type,
            "text/html; charset=utf-8",
        )

        self.assertTrue(
            any(
                servidor.produto.lower() == "nginx"
                for servidor in resultado.servidores
            )
        )

        self.assertTrue(
            any(
                servico.servico == "HTTP"
                for servico in resultado.servicos
            )
        )

        self.assertTrue(
            any(
                evidencia.identificador == "HTTP-STATUS"
                for evidencia in resultado.evidencias
            )
        )

        inventario = resultado.metadados.get(
            "inventario_superficie"
        )

        self.assertIsNotNone(inventario)

        self.assertEqual(
            inventario.alvo,
            alvo,
        )

        self.assertTrue(
            any(
                porta.porta == self.porta
                for porta in inventario.portas
            )
        )


if __name__ == "__main__":
    unittest.main()
