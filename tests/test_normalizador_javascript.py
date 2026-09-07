import unittest

from online.normalizador_javascript import (
    normalizar_string_javascript,
)


class TestNormalizadorJavaScript(unittest.TestCase):

    def test_string_vazia(self):
        resultado = normalizar_string_javascript("")

        self.assertEqual(
            resultado["original"],
            "",
        )

        self.assertEqual(
            resultado["normalizado"],
            "",
        )

        self.assertEqual(
            resultado["transformacoes"],
            [],
        )

    def test_normaliza_escape_javascript(self):
        resultado = normalizar_string_javascript(
            r"\x48\x65\x6c\x6c\x6f"
        )

        self.assertEqual(
            resultado["original"],
            r"\x48\x65\x6c\x6c\x6f",
        )

        self.assertEqual(
            resultado["normalizado"],
            "Hello",
        )

        self.assertIn(
            "escape_javascript",
            resultado["transformacoes"],
        )

    def test_normaliza_url(self):
        resultado = normalizar_string_javascript(
            "%2Fapi%2Flogin"
        )

        self.assertEqual(
            resultado["normalizado"],
            "/api/login",
        )

        self.assertIn(
            "url_decode",
            resultado["transformacoes"],
        )

    def test_normaliza_base64(self):
        resultado = normalizar_string_javascript(
            "SGVsbG8="
        )

        self.assertEqual(
            resultado["normalizado"],
            "Hello",
        )

        self.assertIn(
            "base64",
            resultado["transformacoes"],
        )

    def test_normaliza_hex(self):
        resultado = normalizar_string_javascript(
            "48656c6c6f"
        )

        self.assertEqual(
            resultado["normalizado"],
            "Hello",
        )

        self.assertIn(
            "hex",
            resultado["transformacoes"],
        )

    def test_preserva_original(self):
        valor = r"\x2fapi\x2flogin"

        resultado = normalizar_string_javascript(
            valor
        )

        self.assertEqual(
            resultado["original"],
            valor,
        )

        self.assertNotEqual(
            resultado["original"],
            resultado["normalizado"],
        )


if __name__ == "__main__":
    unittest.main()
