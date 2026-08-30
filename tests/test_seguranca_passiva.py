import unittest

import analisador_banco as analisador


TEXTO_HTTP = """HTTP/1.1 200 OK
Content-Type: application/json
Set-Cookie: laravel_session=abc123; Path=/; Secure; HttpOnly
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.test.signature

{"username":"teste","password":"segredo","token":"abc123","session_id":"sessao123"}
"""


class TestJSON(unittest.TestCase):

    def test_detecta_json(self):
        resultado = analisador.detectar_json(TEXTO_HTTP)

        self.assertTrue(resultado["detectado"])
        self.assertEqual(resultado["quantidade"], 1)
        self.assertEqual(
            resultado["objetos"][0]["tipo"],
            "dict",
        )
        self.assertTrue(
            resultado["objetos"][0]["valido"]
        )


class TestCookies(unittest.TestCase):

    def test_detecta_cookie(self):
        resultado = analisador.detectar_cookies(TEXTO_HTTP)

        self.assertTrue(resultado["detectado"])
        self.assertEqual(resultado["quantidade"], 1)
        self.assertIn(
            "laravel_session",
            resultado["nomes"],
        )

    def test_detecta_atributos_cookie(self):
        resultado = analisador.detectar_atributos_cookie(
            TEXTO_HTTP
        )

        self.assertEqual(resultado["secure"], 1)
        self.assertEqual(resultado["httponly"], 1)
        self.assertEqual(resultado["path"], 1)
        self.assertEqual(resultado["samesite"], 0)


class TestJWT(unittest.TestCase):

    def test_detecta_padrao_jwt(self):
        resultado = analisador.detectar_jwt(TEXTO_HTTP)

        self.assertTrue(resultado["detectado"])
        self.assertEqual(resultado["quantidade"], 1)
        self.assertIn(
            "JWT",
            resultado["observacao"],
        )


class TestSessoes(unittest.TestCase):

    def test_detecta_formatos_de_sessao(self):
        resultado = analisador.detectar_sessoes(
            TEXTO_HTTP
        )

        self.assertTrue(resultado["detectado"])

        formatos = resultado["formatos"]

        self.assertEqual(
            formatos["laravel_session"],
            1,
        )
        self.assertEqual(
            formatos["session_id"],
            1,
        )


class TestAutenticacao(unittest.TestCase):

    def test_detecta_bearer_e_authorization(self):
        resultado = analisador.detectar_autenticacao(
            TEXTO_HTTP
        )

        self.assertTrue(resultado["detectado"])

        formatos = resultado["formatos"]

        self.assertEqual(
            formatos["Bearer"],
            1,
        )
        self.assertEqual(
            formatos["Authorization"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
