import unittest

from online.detector_configuracao import detectar_configuracoes


class TestDetectorConfiguracao(unittest.TestCase):

    def test_detecta_api_key_em_javascript(self):
        codigo = '''
        const config = {
            api_key: "abc123"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "api_key")
        self.assertEqual(resultado[0]["origem"], "javascript")

    def test_detecta_token_em_contexto_de_configuracao(self):
        codigo = '''
        const config = {
            token: "abc123"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "token")

    def test_detecta_password(self):
        codigo = '''
        const config = {
            password: "senha123"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "password")

    def test_valor_sensivel_nao_e_exposto(self):
        codigo = '''
        const config = {
            api_key: "SEGREDO_REAL_123"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["valor"], "[REDACTED]")
        self.assertNotIn(
            "SEGREDO_REAL_123",
            str(resultado),
        )

    def test_preserva_proveniencia(self):
        codigo = '''
        const config = {
            api_key: "abc123"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(resultado[0]["origem"], "javascript")
        self.assertEqual(resultado[0]["localizacao"]["arquivo"], "app.js")
        self.assertIn("evidencias", resultado[0])

    def test_detecta_multiplas_configuracoes(self):
        codigo = '''
        const config = {
            api_key: "abc",
            token: "def",
            password: "ghi"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        nomes = {item["nome"] for item in resultado}

        self.assertEqual(
            nomes,
            {"api_key", "token", "password"},
        )

    def test_nao_detecta_nome_comum_sem_contexto(self):
        codigo = '''
        const token = usuario.token;
        console.log(token);
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(resultado, [])

    def test_detecta_authorization(self):
        codigo = '''
        const config = {
            authorization: "Bearer abc123"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "authorization")

    def test_detecta_private_key(self):
        codigo = '''
        const config = {
            private_key: "-----BEGIN PRIVATE KEY-----"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "private_key")

    def test_detecta_api_url(self):
        codigo = '''
        const config = {
            api_url: "https://api.exemplo.test"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "api_url")


    def test_detecta_token_em_propriedade_indexada_com_aspas_simples(self):
        codigo = "const config = {};\nconfig['token'] = 'abc123';\n"

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "token")

    def test_valor_sensivel_em_propriedade_indexada_nao_e_exposto(self):
        codigo = """const config = {};
config["api_key"] = "super-segredo";
"""

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "api_key")
        self.assertNotEqual(resultado[0].get("valor"), "super-segredo")

    def test_propriedade_indexada_dentro_de_string_nao_e_detectada(self):
        codigo = 'const mensagem = \'config["token"] = "abc123"\';\n'

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(resultado, [])

    def test_propriedade_indexada_em_comentario_nao_e_detectada(self):
        codigo = '// config["token"] = "abc123"\n'

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(resultado, [])

    def test_propriedade_indexada_preserva_localizacao(self):
        codigo = 'const config = {};\nconfig["token"] = "abc123";\n'

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["localizacao"]["linha"], 2)
        self.assertGreater(resultado[0]["localizacao"]["coluna"], 0)

    def test_detecta_token_em_propriedade_indexada(self):
        codigo = """
const config = {};
config["token"] = "abc123";
"""

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "token")


    def test_detecta_variavel_ambiente_process_env_indexado(self):
        codigo = """
        const apiUrl = process.env["API_URL"];
        """

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)

        item = resultado[0]

        self.assertEqual(item["nome"], "API_URL")
        self.assertEqual(item["tipo"], "variavel_ambiente")
        self.assertFalse(item["sensivel"])
        self.assertIsNone(item["valor"])

    def test_detecta_variavel_ambiente_import_meta_env_indexado(self):
        codigo = """
        const token = import.meta.env["VITE_API_TOKEN"];
        """

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)

        item = resultado[0]

        self.assertEqual(item["nome"], "VITE_API_TOKEN")
        self.assertEqual(item["tipo"], "variavel_ambiente")
        self.assertFalse(item["sensivel"])
        self.assertIsNone(item["valor"])

    def test_nao_detecta_variavel_ambiente_indexada_em_string(self):
        codigo = """
        const mensagem = 'process.env["API_URL"]';
        const outra = "import.meta.env['VITE_API_TOKEN']";
        """

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(resultado, [])


    def test_detecta_variavel_ambiente_process_env(self):
        codigo = """
        const apiUrl = process.env.API_URL;
        """

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)

        item = resultado[0]

        self.assertEqual(item["nome"], "API_URL")
        self.assertEqual(item["tipo"], "variavel_ambiente")
        self.assertFalse(item["sensivel"])
        self.assertIsNone(item["valor"])

    def test_detecta_variavel_ambiente_import_meta_env(self):
        codigo = """
        const token = import.meta.env.VITE_API_TOKEN;
        """

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)

        item = resultado[0]

        self.assertEqual(item["nome"], "VITE_API_TOKEN")
        self.assertEqual(item["tipo"], "variavel_ambiente")
        self.assertFalse(item["sensivel"])
        self.assertIsNone(item["valor"])


    def test_nao_detecta_variavel_ambiente_em_comentario(self):
        codigo = """
        // process.env.API_URL
        /* import.meta.env.VITE_API_TOKEN */
        """

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(resultado, [])

    def test_nao_detecta_variavel_ambiente_dentro_de_string(self):
        codigo = """
        const mensagem = "process.env.API_URL";
        const outra = 'import.meta.env.VITE_API_TOKEN';
        """

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(resultado, [])


if __name__ == "__main__":
    unittest.main()


class TestDetectorConfiguracaoNegativos(unittest.TestCase):

    def test_ignora_objeto_sem_valor_string(self):
        codigo = '''
        const config = {
            token: null
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(resultado, [])

    def test_ignora_comentario_com_api_key(self):
        codigo = '''
        // const config = { api_key: "exemplo" };
        const nome = "usuario";
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(resultado, [])

    def test_ignora_texto_comum_contendo_token(self):
        codigo = '''
        const mensagem = "o token expirou";
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(resultado, [])

    def test_nao_detecta_propriedade_dentro_de_string(self):
        casos = [
            """const mensagem = "token: 'abc123'";""",
            """const mensagem = "password: 'abc123'";""",
            """const mensagem = "api_key: 'abc123'";""",
        ]

        for codigo in casos:
            with self.subTest(codigo=codigo):
                resultado = detectar_configuracoes(
                    codigo,
                    origem="teste",
                    arquivo="teste.js",
                    linguagem="javascript",
                )

                self.assertEqual(resultado, [])


    def test_detecta_propriedade_real_mesmo_com_strings_no_codigo(self):
        codigo = """
const mensagem = "token: 'abc123'";

const config = {
    token: "valor-real"
};
"""

        resultado = detectar_configuracoes(
            codigo,
            origem="teste",
            arquivo="teste.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "token")
        self.assertEqual(
            resultado[0]["localizacao"]["linha"],
            5,
        )


    def test_classificacao_token_em_configuracao(self):
        codigo = '''
        const config = {
            token: "abc123"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertEqual(resultado[0]["classificacao"], "provavel")
        self.assertGreaterEqual(resultado[0]["pontuacao"], 80)
        self.assertEqual(resultado[0]["confianca"], "alta")

    def test_fingerprint_e_gerado_para_segredo(self):
        codigo = '''
        const config = {
            api_key: "abc123"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        self.assertIn("fingerprint", resultado[0])
        self.assertEqual(
            resultado[0]["fingerprint"]["algoritmo"],
            "sha256",
        )

    def test_localizacao_tem_linha_e_coluna(self):
        codigo = '''const config = {
    api_key: "abc123"
};'''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
        )

        localizacao = resultado[0]["localizacao"]

        self.assertEqual(localizacao["arquivo"], "app.js")
        self.assertEqual(localizacao["linha"], 2)
        self.assertGreater(localizacao["coluna"], 0)


if __name__ == "__main__":
    unittest.main()


class TestDetectorConfiguracaoLexico(unittest.TestCase):

    def test_ignora_comentario_bloco_javascript(self):
        codigo = '''
        /*
        const config = {
            api_key: "segredo"
        };
        */
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(resultado, [])

    def test_ignora_comentario_cpp(self):
        codigo = '''
        // const config = { password: "segredo" };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="cpp",
            arquivo="config.cpp",
            linguagem="cpp",
        )

        self.assertEqual(resultado, [])

    def test_ignora_comentario_php_com_hash(self):
        codigo = '''
        <?php
        # $config = ["password" => "segredo"];
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="php",
            arquivo="config.php",
            linguagem="php",
        )

        self.assertEqual(resultado, [])

    def test_ignora_comentario_php_com_duas_barras(self):
        codigo = '''
        <?php
        // $config = ["password" => "segredo"];
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="php",
            arquivo="config.php",
            linguagem="php",
        )

        self.assertEqual(resultado, [])

    def test_nao_confunde_duas_barras_dentro_de_string(self):
        codigo = '''
        const config = {
            api_url: "https://api.exemplo.test"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "api_url")

    def test_nao_confunde_comentario_bloco_dentro_de_string(self):
        codigo = '''
        const config = {
            api_url: "https://api.exemplo.test/*nao_e_comentario*/"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "api_url")

    def test_segredo_em_comentario_nao_e_configuracao(self):
        codigo = '''
        /*
        password: "senha-antiga"
        token: "token-antigo"
        api_key: "chave-antiga"
        */

        const config = {
            api_url: "https://api.exemplo.test"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        nomes = [item["nome"] for item in resultado]

        self.assertEqual(nomes, ["api_url"])

    def test_detecta_configuracao_real_em_cpp(self):
        codigo = '''
        const char* config = "production";
        const char* token = "abc123";
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="cpp",
            arquivo="config.cpp",
            linguagem="cpp",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "token")

    def test_detecta_configuracao_real_em_php(self):
        codigo = '''
        <?php
        $token = "abc123";
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="php",
            arquivo="config.php",
            linguagem="php",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "token")

    def test_comentario_nao_destroi_localizacao_da_configuracao(self):
        codigo = '''// comentario
// outro comentario

const config = {
    api_key: "abc123"
};'''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)

        localizacao = resultado[0]["localizacao"]

        self.assertEqual(localizacao["arquivo"], "app.js")
        self.assertEqual(localizacao["linha"], 5)
        self.assertGreater(localizacao["coluna"], 0)


if __name__ == "__main__":
    unittest.main()


class TestDetectorConfiguracaoAtribuicaoRobustez(unittest.TestCase):

    def test_ignora_atribuicao_em_comentario_javascript(self):
        codigo = '''
        // token = "segredo";
        const config = {
            api_url: "https://api.exemplo.test"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        nomes = [item["nome"] for item in resultado]

        self.assertEqual(nomes, ["api_url"])

    def test_ignora_atribuicao_em_comentario_bloco(self):
        codigo = '''
        /*
        token = "segredo";
        password = "senha";
        */
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(resultado, [])

    def test_ignora_atribuicao_dentro_de_string(self):
        codigo = '''
        const mensagem = 'token = "nao_e_configuracao"';
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(resultado, [])

    def test_url_dentro_de_string_nao_vira_comentario(self):
        codigo = '''
        const config = {
            api_url: "https://api.exemplo.test/v1"
        };
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="app.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["nome"], "api_url")
        self.assertEqual(resultado[0]["valor"], "[REDACTED]" if resultado[0]["sensivel"] else "https://api.exemplo.test/v1")

    def test_comentario_cpp_com_atribuicao_nao_e_detectado(self):
        codigo = '''
        // token = "segredo";
        const char* token_real = "valor";
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="cpp",
            arquivo="config.cpp",
            linguagem="cpp",
        )

        self.assertEqual(resultado, [])

    def test_comentario_php_com_atribuicao_nao_e_detectado(self):
        codigo = '''
        <?php
        # $token = "segredo";
        // $password = "senha";
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="php",
            arquivo="config.php",
            linguagem="php",
        )

        self.assertEqual(resultado, [])

    def test_detecta_varias_atribuicoes(self):
        codigo = '''
        token = "abc123";
        password = "senha123";
        api_key = "chave123";
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="config.js",
            linguagem="javascript",
        )

        nomes = [item["nome"] for item in resultado]

        self.assertEqual(
            nomes,
            ["token", "password", "api_key"],
        )

    def test_atribuicao_sensivel_mantem_protecao(self):
        codigo = '''
        token = "segredo-super-secreto";
        '''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="config.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)

        item = resultado[0]

        self.assertTrue(item["sensivel"])
        self.assertEqual(item["valor"], "[REDACTED]")
        self.assertIn("fingerprint", item)

        self.assertNotIn(
            "segredo-super-secreto",
            str(item),
        )

    def test_atribuicao_preserva_localizacao(self):
        codigo = '''// comentario

token = "abc123";
'''

        resultado = detectar_configuracoes(
            codigo,
            origem="javascript",
            arquivo="config.js",
            linguagem="javascript",
        )

        self.assertEqual(len(resultado), 1)

        localizacao = resultado[0]["localizacao"]

        self.assertEqual(localizacao["arquivo"], "config.js")
        self.assertEqual(localizacao["linha"], 3)
        self.assertGreater(localizacao["coluna"], 0)


if __name__ == "__main__":
    unittest.main()
