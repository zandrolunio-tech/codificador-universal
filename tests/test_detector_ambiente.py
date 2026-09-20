import unittest

from online.detector_ambiente import detectar_ambientes


class TestDetectorAmbiente(unittest.TestCase):
    def test_detecta_comparacao_node_env(self):
        codigo = 'if (process.env.NODE_ENV === "production") {}'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ambiente"], "production")
        self.assertEqual(resultado[0]["tipo"], "comparacao")
        self.assertEqual(resultado[0]["confianca"], "ALTA")

    def test_detecta_node_env_indexado_sem_inventar_valor(self):
        codigo = 'const ambiente = process.env["NODE_ENV"];'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(resultado, [])

    def test_detecta_import_meta_prod(self):
        codigo = "if (import.meta.env.PROD) {}"

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ambiente"], "production")
        self.assertEqual(resultado[0]["tipo"], "import_meta_env_flag")

    def test_detecta_import_meta_dev(self):
        codigo = "if (import.meta.env.DEV) {}"

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ambiente"], "development")
        self.assertEqual(resultado[0]["tipo"], "import_meta_env_flag")

    def test_nao_inventa_valor_para_import_meta_mode(self):
        codigo = "const modo = import.meta.env.MODE;"

        resultado = detectar_ambientes(codigo)

        self.assertEqual(resultado, [])

    def test_detecta_atribuicao_environment(self):
        codigo = 'const environment = "production";'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ambiente"], "production")
        self.assertEqual(resultado[0]["tipo"], "atribuicao_ambiente")

    def test_detecta_atribuicao_env(self):
        codigo = 'const env = "staging";'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ambiente"], "staging")

    def test_detecta_propriedade_config(self):
        codigo = 'config.environment = "production";'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ambiente"], "production")
        self.assertEqual(resultado[0]["tipo"], "propriedade_ambiente")

    def test_detecta_objeto_configuracao(self):
        codigo = 'const config = { environment: "production" };'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ambiente"], "production")
        self.assertEqual(resultado[0]["tipo"], "objeto_ambiente")

    def test_preserva_qa(self):
        codigo = 'const environment = "qa";'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["ambiente"], "qa")

    def test_ignora_production_solto(self):
        codigo = 'const texto = "production";'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(resultado, [])

    def test_ignora_atribuicao_dentro_de_string(self):
        codigo = 'const texto = \'const environment = "production";\';'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(resultado, [])

    def test_ignora_propriedade_dentro_de_string(self):
        codigo = 'const texto = "config.environment = \'production\'";'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(resultado, [])

    def test_ignora_comentario(self):
        codigo = '// const environment = "production";'

        resultado = detectar_ambientes(codigo)

        self.assertEqual(resultado, [])

    def test_ordena_por_localizacao(self):
        codigo = (
            'const environment = "production";\n'
            'const env = "staging";\n'
        )

        resultado = detectar_ambientes(codigo)

        self.assertEqual(len(resultado), 2)
        self.assertEqual(resultado[0]["ambiente"], "production")
        self.assertEqual(resultado[1]["ambiente"], "staging")

    def test_ignora_linguagem_nao_suportada(self):
        codigo = 'const environment = "production";'

        resultado = detectar_ambientes(
            codigo,
            linguagem="python",
        )

        self.assertEqual(resultado, [])

    def test_retorna_lista_vazia_para_codigo_vazio(self):
        self.assertEqual(detectar_ambientes(""), [])


if __name__ == "__main__":
    unittest.main()
