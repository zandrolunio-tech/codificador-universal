import unittest

from online.decodificador_javascript import (
    decodificar_base64,
    decodificar_escapes_javascript,
    decodificar_hex,
    decodificar_javascript,
    decodificar_url,
    extrair_strings_javascript,
)

class TestDecodificadorJavaScript(unittest.TestCase):

    def test_decodifica_escape_unicode(self):
        resultado = decodificar_escapes_javascript(
            r"\u0048\u0069"
     )

        self.assertEqual(resultado, "Hi")

    def test_decodifica_escape_hex(self):
        resultado = decodificar_escapes_javascript(
            r"\x48\x65\x6c\x6c\x6f"
        )

        self.assertEqual(resultado, "Hello")

    def test_decodifica_url(self):
        resultado = decodificar_url(
            "%48%65%6C%6C%6F"
        )

        self.assertEqual(resultado, "Hello")

    def test_decodifica_base64(self):
        resultado = decodificar_base64(
            "SGVsbG8="
        )

        self.assertEqual(resultado, "Hello")

    def test_rejeita_base64_invalido(self):
        resultado = decodificar_base64(
            "nao-base64!"
        )

        self.assertIsNone(resultado)

    def test_decodifica_hex(self):
        resultado = decodificar_hex(
            "48656c6c6f"
        )

        self.assertEqual(resultado, "Hello")

    def test_rejeita_hex_invalido(self):
        resultado = decodificar_hex(
            "xyz123"
        )

        self.assertIsNone(resultado)

    def test_analise_completa(self):
        resultado = decodificar_javascript(
            r"\x48\x69"
        )

        self.assertEqual(
            resultado["original"],
            r"\x48\x69",
        )

        self.assertEqual(
            resultado["escapes"],
            "Hi",
        )

        self.assertIn(
            "original",
            resultado,
        )

    def test_extrai_strings_javascript(self):
        codigo = """
        const a = "Hello";
        const b = '/api/login';
        const c = "SGVsbG8=";
        """

        resultado = extrair_strings_javascript(codigo)

        self.assertEqual(
            resultado,
            [
                "Hello",
                "/api/login",
                "SGVsbG8=",
            ],
        )

if __name__ == "__main__":
    unittest.main()
