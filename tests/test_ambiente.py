import unittest

from online.ambiente import normalizar_ambiente


class TestNormalizarAmbiente(unittest.TestCase):
    def test_normaliza_production(self):
        self.assertEqual(normalizar_ambiente("production"), "production")

    def test_normaliza_prod(self):
        self.assertEqual(normalizar_ambiente("prod"), "production")

    def test_normaliza_development(self):
        self.assertEqual(normalizar_ambiente("development"), "development")

    def test_normaliza_develop(self):
        self.assertEqual(normalizar_ambiente("develop"), "development")

    def test_normaliza_dev(self):
        self.assertEqual(normalizar_ambiente("dev"), "development")

    def test_normaliza_staging(self):
        self.assertEqual(normalizar_ambiente("staging"), "staging")

    def test_normaliza_stage(self):
        self.assertEqual(normalizar_ambiente("stage"), "staging")

    def test_normaliza_test(self):
        self.assertEqual(normalizar_ambiente("test"), "test")

    def test_normaliza_testing(self):
        self.assertEqual(normalizar_ambiente("testing"), "test")

    def test_preserva_ambiente_desconhecido(self):
        self.assertEqual(normalizar_ambiente("qa"), "qa")

    def test_preserva_ambiente_uat(self):
        self.assertEqual(normalizar_ambiente("uat"), "uat")

    def test_preserva_ambiente_sandbox(self):
        self.assertEqual(normalizar_ambiente("sandbox"), "sandbox")

    def test_remove_espacos(self):
        self.assertEqual(
            normalizar_ambiente("  Production  "),
            "production",
        )

    def test_normaliza_maiusculas(self):
        self.assertEqual(
            normalizar_ambiente("PRODUCTION"),
            "production",
        )

    def test_valor_vazio(self):
        self.assertEqual(normalizar_ambiente(""), "")

    def test_valor_apenas_espacos(self):
        self.assertEqual(normalizar_ambiente("   "), "")

    def test_valor_none(self):
        self.assertEqual(normalizar_ambiente(None), "")


if __name__ == "__main__":
    unittest.main()
