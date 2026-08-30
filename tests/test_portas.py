import socket
import threading
import unittest

from online.analisador_portas import analisar_porta
from online.inventario_superficie import (
    PortaObservada,
    construir_inventario,
    resumir_inventario,
    serializar_inventario,
)


class TestAnalisadorPortas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.servidor = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        cls.servidor.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        cls.servidor.bind(("127.0.0.1", 0))
        cls.servidor.listen(1)

        cls.porta_aberta = cls.servidor.getsockname()[1]

        cls.thread = threading.Thread(
            target=cls._aceitar,
            daemon=True,
        )

        cls.thread.start()

    @classmethod
    def _aceitar(cls):
        try:
            while True:
                conexao, _ = cls.servidor.accept()
                conexao.close()
        except OSError:
            pass

    @classmethod
    def tearDownClass(cls):
        cls.servidor.close()

    def test_porta_aberta(self):
        resultado = analisar_porta(
            "127.0.0.1",
            self.porta_aberta,
            timeout=1,
        )

        self.assertEqual(resultado.estado, "aberta")
        self.assertEqual(resultado.transporte, "TCP")
        self.assertEqual(resultado.confianca, "ALTA")

    def test_porta_fechada(self):
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.bind(("127.0.0.1", 0))
        porta = sock.getsockname()[1]
        sock.close()

        resultado = analisar_porta(
            "127.0.0.1",
            porta,
            timeout=1,
        )

        self.assertEqual(resultado.estado, "fechada")
        self.assertEqual(resultado.transporte, "TCP")
        self.assertEqual(resultado.confianca, "ALTA")


class TestInventarioPortas(unittest.TestCase):

    def test_resumo_portas_abertas_e_fechadas(self):
        aberta = PortaObservada(
            porta=8765,
            transporte="TCP",
            estado="aberta",
            servico="HTTP",
            protocolo="HTTP",
            origem="teste",
            confianca="ALTA",
        )

        fechada = PortaObservada(
            porta=8766,
            transporte="TCP",
            estado="fechada",
            origem="teste",
            confianca="ALTA",
        )

        inventario = construir_inventario(
            alvo="http://127.0.0.1",
            portas=[aberta, fechada],
        )

        resumo = resumir_inventario(inventario)

        self.assertEqual(
            resumo["total_portas"],
            2,
        )

        self.assertEqual(
            resumo["portas_abertas"],
            1,
        )

        self.assertEqual(
            resumo["portas_fechadas"],
            1,
        )


    def test_serializacao_inventario(self):
        porta = PortaObservada(
            porta=8765,
            transporte="TCP",
            estado="aberta",
            servico="HTTP",
            protocolo="HTTP",
            origem="teste",
            confianca="ALTA",
            detalhes={
                "origem_teste": True,
            },
        )

        inventario = construir_inventario(
            alvo="http://127.0.0.1:8765",
            portas=[porta],
        )

        dados = serializar_inventario(inventario)

        self.assertIsInstance(dados, dict)

        self.assertEqual(
            dados["alvo"],
            "http://127.0.0.1:8765",
        )

        self.assertIn("portas", dados)
        self.assertIn("servicos", dados)
        self.assertIn("servidores", dados)
        self.assertIn("evidencias", dados)
        self.assertIn("observacoes", dados)
        self.assertIn("metadados", dados)
        self.assertIn("resumo", dados)

        self.assertEqual(
            len(dados["portas"]),
            1,
        )

        self.assertEqual(
            dados["portas"][0]["porta"],
            8765,
        )

        self.assertEqual(
            dados["portas"][0]["estado"],
            "aberta",
        )

        self.assertEqual(
            dados["portas"][0]["servico"],
            "HTTP",
        )

        self.assertEqual(
            dados["portas"][0]["confianca"],
            "ALTA",
        )

        self.assertEqual(
            dados["resumo"]["total_portas"],
            1,
        )

        self.assertEqual(
            dados["resumo"]["portas_abertas"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
