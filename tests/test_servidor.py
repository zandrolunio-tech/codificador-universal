import unittest

from online.analisador_servidor import (
    analisar_servidor,
    consolidar_servidores,
)
from online.modelos import (
    HTTPHeader,
    HTTPResposta,
    ServidorObservado,
)


def criar_resposta(
    url,
    headers,
):
    return HTTPResposta(
        url=url,
        status_code=200,
        reason="OK",
        http_version="HTTP/1.1",
        headers=[
            HTTPHeader(nome=nome, valor=valor)
            for nome, valor in headers
        ],
    )


class TestAnalisadorServidor(unittest.TestCase):

    def test_detecta_nginx_e_versao(self):
        resposta = criar_resposta(
            "http://127.0.0.1",
            [
                ("Server", "nginx/1.24.0"),
            ],
        )

        servidores = analisar_servidor(resposta)

        self.assertEqual(len(servidores), 1)

        servidor = servidores[0]

        self.assertEqual(
            servidor.produto,
            "nginx",
        )
        self.assertEqual(
            servidor.versao,
            "1.24.0",
        )
        self.assertEqual(
            servidor.familia,
            "servidor web",
        )
        self.assertEqual(
            servidor.porta,
            80,
        )
        self.assertEqual(
            servidor.protocolo,
            "HTTP",
        )
        self.assertEqual(
            servidor.origem,
            "header_server",
        )
        self.assertEqual(
            servidor.confianca,
            "ALTA",
        )

    def test_detecta_x_powered_by(self):
        resposta = criar_resposta(
            "https://127.0.0.1:8443",
            [
                ("X-Powered-By", "Express/4.18.2"),
            ],
        )

        servidores = analisar_servidor(resposta)

        self.assertEqual(len(servidores), 1)

        servidor = servidores[0]

        self.assertEqual(
            servidor.produto,
            "Express",
        )
        self.assertEqual(
            servidor.versao,
            "4.18.2",
        )
        self.assertEqual(
            servidor.familia,
            "framework/servidor",
        )
        self.assertEqual(
            servidor.porta,
            8443,
        )
        self.assertEqual(
            servidor.protocolo,
            "HTTP",
        )
        self.assertEqual(
            servidor.origem,
            "header_x_powered_by",
        )

    def test_https_usa_443_por_padrao(self):
        resposta = criar_resposta(
            "https://example.test",
            [
                ("Server", "Apache/2.4.62"),
            ],
        )

        servidores = analisar_servidor(resposta)

        self.assertEqual(len(servidores), 1)

        servidor = servidores[0]

        self.assertEqual(
            servidor.porta,
            443,
        )
        self.assertEqual(
            servidor.protocolo,
            "HTTPS/TLS",
        )

    def test_header_desconhecido_ainda_e_observado(self):
        resposta = criar_resposta(
            "http://example.test",
            [
                ("Server", "MeuServidor/2.0"),
            ],
        )

        servidores = analisar_servidor(resposta)

        self.assertEqual(len(servidores), 1)

        servidor = servidores[0]

        self.assertEqual(
            servidor.produto,
            "MeuServidor",
        )
        self.assertEqual(
            servidor.versao,
            "2.0",
        )
        self.assertEqual(
            servidor.familia,
            "desconhecida",
        )

    def test_resposta_sem_headers_de_servidor(self):
        resposta = criar_resposta(
            "http://example.test",
            [
                ("Content-Type", "text/html"),
            ],
        )

        servidores = analisar_servidor(resposta)

        self.assertEqual(
            servidores,
            [],
        )


class TestConsolidacaoServidores(unittest.TestCase):

    def test_remove_duplicados(self):
        primeiro = ServidorObservado(
            produto="nginx",
            versao="1.24.0",
            porta=80,
            protocolo="HTTP",
            origem="header_server",
        )

        duplicado = ServidorObservado(
            produto="nginx",
            versao="1.24.0",
            porta=80,
            protocolo="HTTP",
            origem="outra_fonte",
        )

        resultado = consolidar_servidores(
            [duplicado, primeiro]
        )

        self.assertEqual(
            len(resultado),
            1,
        )

        self.assertEqual(
            resultado[0].produto,
            "nginx",
        )

    def test_preserva_servidores_diferentes(self):
        nginx = ServidorObservado(
            produto="nginx",
            versao="1.24.0",
            porta=80,
            protocolo="HTTP",
        )

        apache = ServidorObservado(
            produto="apache",
            versao="2.4.62",
            porta=443,
            protocolo="HTTPS/TLS",
        )

        resultado = consolidar_servidores(
            [apache, nginx]
        )

        self.assertEqual(
            len(resultado),
            2,
        )

        self.assertEqual(
            resultado[0].porta,
            80,
        )
        self.assertEqual(
            resultado[1].porta,
            443,
        )


if __name__ == "__main__":
    unittest.main()
