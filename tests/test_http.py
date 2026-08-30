import unittest

import analisador_banco as analisador


class TestDeteccaoRespostaHTTP(unittest.TestCase):

    def test_detecta_resposta_http(self):
        texto = "HTTP/1.1 200 OK"

        resultado = analisador.detectar_resposta_http(texto)

        self.assertTrue(resultado["detectado"])
        self.assertEqual(resultado["quantidade"], 1)
        self.assertEqual(
            resultado["respostas"][0]["codigo"],
            200,
        )
        self.assertEqual(
            resultado["respostas"][0]["descricao"],
            "OK",
        )


class TestDeteccaoRequisicaoHTTP(unittest.TestCase):

    def test_detecta_requisicao_completa(self):
        texto = (
            "POST https://exemplo.local/v1/auth/login "
            "HTTP/1.1\n"
            "Host: exemplo.local\n"
        )

        resultado = analisador.detectar_requisicao(texto)

        self.assertTrue(resultado["detectado"])
        self.assertEqual(resultado["metodo"], "POST")
        self.assertEqual(
            resultado["host"],
            "exemplo.local",
        )
        self.assertEqual(
            resultado["endpoint"],
            "/v1/auth/login",
        )
        self.assertEqual(
            resultado["versao"],
            "1.1",
        )


class TestTransacoesHTTP(unittest.TestCase):

    def test_agrupa_requisicoes_e_respostas(self):
        texto = """POST https://exemplo.local/v1/auth/login HTTP/1.1
HTTP/1.1 401 Unauthorized
GET https://exemplo.local/v1/profile HTTP/1.1
HTTP/1.1 200 OK
"""

        resultado = analisador.detectar_transacoes_http(texto)

        self.assertTrue(resultado["detectado"])
        self.assertEqual(resultado["quantidade"], 2)

        primeira = resultado["transacoes"][0]
        segunda = resultado["transacoes"][1]

        self.assertEqual(
            primeira["requisicao"]["metodo"],
            "POST",
        )
        self.assertEqual(
            primeira["requisicao"]["host"],
            "exemplo.local",
        )
        self.assertEqual(
            primeira["requisicao"]["endpoint"],
            "/v1/auth/login",
        )
        self.assertEqual(
            primeira["resposta"]["codigo"],
            401,
        )

        self.assertEqual(
            segunda["requisicao"]["metodo"],
            "GET",
        )
        self.assertEqual(
            segunda["resposta"]["codigo"],
            200,
        )


class TestValidacaoHTTP(unittest.TestCase):

    def test_requisicao_valida(self):
        texto = (
            "GET https://exemplo.local/v1/profile "
            "HTTP/1.1"
        )

        resultado = analisador.validar_sintaxe_http(texto)

        self.assertTrue(resultado["detectado"])
        self.assertTrue(resultado["valido"])
        self.assertEqual(
            resultado["requisicoes_validas"],
            1,
        )
        self.assertEqual(
            resultado["quantidade_erros"],
            0,
        )

    def test_requisicao_invalida_mostra_correcao(self):
        texto = (
            "GET https://exemplo.local/v1/profile"
        )

        resultado = analisador.validar_sintaxe_http(texto)

        self.assertTrue(resultado["detectado"])
        self.assertFalse(resultado["valido"])
        self.assertEqual(
            resultado["quantidade_erros"],
            1,
        )

        erro = resultado["erros"][0]

        self.assertIn(
            "MÉTODO URL HTTP/1.1",
            erro["forma_correta"],
        )
        self.assertTrue(erro["exemplo"])


if __name__ == "__main__":
    unittest.main()
