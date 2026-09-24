import unittest

from online.modelos import (
    JavaScriptAnalise,
    JavaScriptExtraido,
    OnlineResultado,
)


class TestModelosJavaScript(unittest.TestCase):

    def test_javascript_extraido(self):
        resultado = JavaScriptExtraido(
            origem="script_src",
            tipo="externo",
            url="https://exemplo.test/app.js",
        )

        self.assertEqual(
            resultado.origem,
            "script_src",
        )

        self.assertEqual(
            resultado.tipo,
            "externo",
        )

        self.assertEqual(
            resultado.url,
            "https://exemplo.test/app.js",
        )

        self.assertEqual(
            resultado.conteudo,
            "",
        )

    def test_javascript_extraido_inline(self):
        resultado = JavaScriptExtraido(
            origem="script_inline",
            tipo="inline",
            conteudo="const valor = 10;",
        )

        self.assertEqual(
            resultado.origem,
            "script_inline",
        )

        self.assertEqual(
            resultado.tipo,
            "inline",
        )

        self.assertIn(
            "const valor",
            resultado.conteudo,
        )

    def test_online_resultado_possui_javascript_info(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        self.assertEqual(
            resultado.javascript_info,
            {},
        )

    def test_online_resultado_possui_javascript(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        self.assertEqual(
            resultado.javascript,
            [],
        )


    def test_javascript_analise_padrao(self):
        resultado = JavaScriptAnalise()

        self.assertFalse(
            resultado.detectado
        )

        self.assertEqual(
            resultado.tamanho,
            0,
        )

        self.assertEqual(
            resultado.funcoes,
            [],
        )

        self.assertEqual(
            resultado.imports,
            [],
        )

        self.assertEqual(
            resultado.exports,
            [],
        )

    def test_javascript_analise_completa(self):
        resultado = JavaScriptAnalise(
            detectado=True,
            tamanho=250,
            funcoes=["carregar"],
            imports=["react"],
            exports=["app"],
            urls=[
                "https://api.exemplo.test"
            ],
            endpoints=[
                "/api/clientes"
            ],
            websockets=[
                "wss://ws.exemplo.test"
            ],
            frameworks=["react"],
            apis={
                "fetch": [
                    "/api/clientes"
                ],
                "axios": [],
                "xmlhttprequest": [],
            },
            caracteristicas={
                "usa_fetch": True,
                "usa_xhr": False,
                "usa_websocket": True,
                "usa_modules": True,
                "usa_async": True,
            },
        )

        self.assertTrue(
            resultado.detectado
        )

        self.assertEqual(
            resultado.tamanho,
            250,
        )

        self.assertIn(
            "carregar",
            resultado.funcoes,
        )

        self.assertIn(
            "/api/clientes",
            resultado.endpoints,
        )

        self.assertTrue(
            resultado.caracteristicas[
                "usa_fetch"
            ]
        )


    def test_normaliza_rota_parametros_repetidos(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "/api/clientes?id=10&id=20&ativo=true",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            rota["parametros"],
            ["id", "ativo"],
        )

    def test_normaliza_rota_parametro_sem_valor(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "/api/clientes?ativo",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            rota["parametros"],
            ["ativo"],
        )

    def test_normaliza_rota_sem_caminho(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "https://exemplo.test",
            base_url="https://exemplo.test/",
            origem="http",
        )

        self.assertEqual(
            rota["rota"],
            "/",
        )

    def test_normaliza_rota_normaliza_metodo(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "/api/clientes",
            base_url="https://exemplo.test/",
            origem="javascript",
            metodo="  post  ",
        )

        self.assertEqual(
            rota["metodo"],
            "POST",
        )

    def test_normaliza_rota_fragmento_nao_e_parametro(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "/api/clientes?id=10#detalhes",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            rota["parametros"],
            ["id"],
        )

    def test_normaliza_rota_rejeita_esquema_nao_rede(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "mailto:teste@exemplo.test",
            base_url="https://exemplo.test/",
            origem="html",
        )

        self.assertEqual(
            rota,
            {},
        )

    def test_normaliza_rota_preserva_porta(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "https://api.exemplo.test:8443/clientes",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            rota["url_base"],
            "https://api.exemplo.test:8443",
        )

    def test_normaliza_rota_observada(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "https://exemplo.test/api/clientes?id=10",
            base_url="https://exemplo.test/",
            origem="javascript",
            metodo="GET",
        )

        self.assertEqual(
            rota["rota"],
            "/api/clientes",
        )

        self.assertEqual(
            rota["metodo"],
            "GET",
        )

        self.assertEqual(
            rota["url_base"],
            "https://exemplo.test",
        )

        self.assertEqual(
            rota["parametros"],
            ["id"],
        )

        self.assertEqual(
            rota["tipo"],
            "http",
        )

        self.assertTrue(
            rota["interna"],
        )

        self.assertEqual(
            rota["origens"],
            ["javascript"],
        )

    def test_normaliza_rota_relativa(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "/api/clientes?id=10&ativo=true",
            base_url="https://exemplo.test/app/",
            origem="html",
        )

        self.assertEqual(
            rota["rota"],
            "/api/clientes",
        )

        self.assertEqual(
            rota["parametros"],
            ["id", "ativo"],
        )

        self.assertEqual(
            rota["url_base"],
            "https://exemplo.test",
        )

        self.assertTrue(
            rota["interna"],
        )

    def test_normaliza_rota_websocket(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "wss://exemplo.test/socket",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            rota["rota"],
            "/socket",
        )

        self.assertEqual(
            rota["tipo"],
            "websocket",
        )

        self.assertEqual(
            rota["metodo"],
            "",
        )

    def test_normaliza_rota_externa(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "https://api.externo.test/v1/clientes",
            base_url="https://exemplo.test/",
            origem="javascript",
            metodo="POST",
        )

        self.assertEqual(
            rota["rota"],
            "/v1/clientes",
        )

        self.assertEqual(
            rota["metodo"],
            "POST",
        )

        self.assertFalse(
            rota["interna"],
        )

        self.assertEqual(
            rota["url_base"],
            "https://api.externo.test",
        )

    def test_normaliza_rota_invalida(self):
        from online.rotas import normalizar_rota

        rota = normalizar_rota(
            "",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            rota,
            {},
        )

    def test_normaliza_configuracao_basica(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="api_base_url",
            valor="https://api.exemplo.test",
            origem="javascript",
            fonte="configuracao",
            tipo="url",
            sensivel=False,
            confianca="alta",
        )

        self.assertEqual(
            configuracao["nome"],
            "api_base_url",
        )
        self.assertEqual(
            configuracao["valor"],
            "https://api.exemplo.test",
        )
        self.assertEqual(
            configuracao["origem"],
            "javascript",
        )
        self.assertEqual(
            configuracao["fonte"],
            "configuracao",
        )
        self.assertEqual(
            configuracao["tipo"],
            "url",
        )
        self.assertFalse(
            configuracao["sensivel"],
        )
        self.assertEqual(
            configuracao["confianca"],
            "alta",
        )

    def test_normaliza_configuracao_sensivel_redige_valor(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="api_key",
            valor="segredo-original",
            origem="javascript",
            fonte="configuracao",
            tipo="segredo",
            sensivel=True,
            confianca="alta",
        )

        self.assertEqual(
            configuracao["valor"],
            "[REDACTED]",
        )
        self.assertTrue(
            configuracao["sensivel"],
        )

    def test_normaliza_configuracao_rejeita_nome_vazio(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="",
            valor="algum-valor",
            origem="javascript",
            fonte="configuracao",
            tipo="texto",
            sensivel=False,
            confianca="alta",
        )

        self.assertEqual(
            configuracao,
            {},
        )

    def test_normaliza_configuracao_preserva_origem(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="ambiente",
            valor="production",
            origem="html",
            fonte="atributo",
            tipo="ambiente",
            sensivel=False,
            confianca="media",
        )

        self.assertEqual(
            configuracao["origem"],
            "html",
        )
        self.assertEqual(
            configuracao["fonte"],
            "atributo",
        )

    def test_normaliza_configuracao_preserva_tipo(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="habilitado",
            valor="true",
            origem="javascript",
            fonte="configuracao",
            tipo="boolean",
            sensivel=False,
            confianca="media",
        )

        self.assertEqual(
            configuracao["tipo"],
            "boolean",
        )

    def test_normaliza_configuracao_normaliza_confianca(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="api_url",
            valor="https://api.exemplo.test",
            origem="javascript",
            fonte="configuracao",
            tipo="url",
            sensivel=False,
            confianca=" ALTA ",
        )

        self.assertEqual(
            configuracao["confianca"],
            "alta",
        )

    def test_normaliza_configuracao_preserva_valor_nao_sensivel(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="ambiente",
            valor="production",
            origem="javascript",
            fonte="configuracao",
            tipo="ambiente",
            sensivel=False,
            confianca="alta",
        )

        self.assertEqual(
            configuracao["valor"],
            "production",
        )

    def test_normaliza_configuracao_com_proveniencia(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="token",
            valor="valor-secreto",
            origem="javascript",
            fonte="app.js",
            localizacao={
                "linha": 184,
                "coluna": 17,
            },
            caminho="config.authentication.token",
            contexto="objeto de configuração",
            tipo="segredo",
            sensivel=True,
            classificacao="provavel",
            pontuacao=92,
            confianca="alta",
            evidencias=[
                "nome compatível com credencial",
                "encontrado em objeto de configuração",
            ],
        )

        self.assertEqual(
            configuracao["nome"],
            "token",
        )
        self.assertEqual(
            configuracao["origem"],
            "javascript",
        )
        self.assertEqual(
            configuracao["fonte"],
            "app.js",
        )
        self.assertEqual(
            configuracao["localizacao"]["linha"],
            184,
        )
        self.assertEqual(
            configuracao["localizacao"]["coluna"],
            17,
        )
        self.assertEqual(
            configuracao["caminho"],
            "config.authentication.token",
        )
        self.assertEqual(
            configuracao["contexto"],
            "objeto de configuração",
        )
        self.assertEqual(
            configuracao["tipo"],
            "segredo",
        )
        self.assertTrue(
            configuracao["sensivel"],
        )
        self.assertEqual(
            configuracao["classificacao"],
            "provavel",
        )
        self.assertEqual(
            configuracao["pontuacao"],
            92,
        )
        self.assertEqual(
            configuracao["confianca"],
            "alta",
        )
        self.assertEqual(
            len(configuracao["evidencias"]),
            2,
        )
        self.assertTrue(
            configuracao["valor_protegido"],
        )
        self.assertEqual(
            configuracao["valor"],
            "[REDACTED]",
        )

    def test_normaliza_configuracao_gera_fingerprint(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="api_key",
            valor="segredo-original",
            origem="javascript",
            fonte="app.js",
            tipo="segredo",
            sensivel=True,
            classificacao="provavel",
            pontuacao=90,
            confianca="alta",
            evidencias=[
                "nome compatível com API key",
            ],
        )

        self.assertIn(
            "fingerprint",
            configuracao,
        )
        self.assertEqual(
            configuracao["fingerprint"]["algoritmo"],
            "sha256",
        )
        self.assertTrue(
            configuracao["fingerprint"]["valor"],
        )
        self.assertNotEqual(
            configuracao["fingerprint"]["valor"],
            "segredo-original",
        )

    def test_normaliza_configuracao_nao_expoe_segredo(self):
        from online.configuracao import normalizar_configuracao

        segredo = "MINHA-CREDENCIAL-SECRETA"

        configuracao = normalizar_configuracao(
            nome="private_key",
            valor=segredo,
            origem="javascript",
            fonte="app.js",
            tipo="segredo",
            sensivel=True,
            classificacao="provavel",
            pontuacao=95,
            confianca="alta",
            evidencias=[
                "nome compatível com chave privada",
            ],
        )

        self.assertEqual(
            configuracao["valor"],
            "[REDACTED]",
        )
        self.assertNotIn(
            segredo,
            str(configuracao),
        )

    def test_normaliza_configuracao_sem_localizacao_preserva_proveniencia(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="authorization",
            valor="Bearer exemplo",
            origem="http",
            fonte="header",
            caminho="Authorization",
            contexto="cabecalho HTTP",
            tipo="credencial",
            sensivel=True,
            classificacao="possivel",
            pontuacao=70,
            confianca="media",
            evidencias=[
                "header HTTP observado",
            ],
        )

        self.assertEqual(
            configuracao["origem"],
            "http",
        )
        self.assertEqual(
            configuracao["fonte"],
            "header",
        )
        self.assertEqual(
            configuracao["caminho"],
            "Authorization",
        )
        self.assertEqual(
            configuracao["contexto"],
            "cabecalho HTTP",
        )
        self.assertIsNone(
            configuracao["localizacao"],
        )

    def test_normaliza_configuracao_rejeita_classificacao_invalida(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="token",
            valor="abc",
            origem="javascript",
            fonte="app.js",
            tipo="segredo",
            sensivel=True,
            classificacao="certeza-absoluta",
            pontuacao=90,
            confianca="alta",
            evidencias=[
                "nome compatível com token",
            ],
        )

        self.assertEqual(
            configuracao,
            {},
        )

    def test_normaliza_configuracao_rejeita_pontuacao_invalida(self):
        from online.configuracao import normalizar_configuracao

        configuracao = normalizar_configuracao(
            nome="token",
            valor="abc",
            origem="javascript",
            fonte="app.js",
            tipo="segredo",
            sensivel=True,
            classificacao="provavel",
            pontuacao=150,
            confianca="alta",
            evidencias=[
                "nome compatível com token",
            ],
        )

        self.assertEqual(
            configuracao,
            {},
        )

    def test_online_resultado_possui_configuracoes(self):
        resultado = OnlineResultado(alvo="https://exemplo.test")

        self.assertEqual(resultado.configuracoes, [])
        self.assertIsInstance(resultado.configuracoes, list)

    def test_online_resultado_possui_frameworks(self):
        resultado = OnlineResultado(
            alvo="https://exemplo.test"
        )

        self.assertEqual(
            resultado.frameworks,
            [],
        )

        self.assertIsInstance(
            resultado.frameworks,
            list,
        )


    def test_online_resultado_possui_ambientes(self):
        resultado = OnlineResultado(
            alvo="https://exemplo.test"
        )

        self.assertEqual(
            resultado.ambientes,
            [],
        )

        self.assertIsInstance(
            resultado.ambientes,
            list,
        )

    def test_online_resultado_possui_rotas(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        self.assertIsInstance(
            resultado.rotas,
            list,
        )

        resultado.rotas.append(
            {
                "rota": "/api/clientes",
                "metodo": "GET",
                "origens": ["javascript"],
                "url_base": "https://exemplo.test",
                "parametros": ["id"],
                "tipo": "http",
                "interna": True,
                "confianca": "alta",
            }
        )

        self.assertEqual(
            len(resultado.rotas),
            1,
        )

        rota = resultado.rotas[0]

        self.assertEqual(
            rota["rota"],
            "/api/clientes",
        )

        self.assertEqual(
            rota["metodo"],
            "GET",
        )

        self.assertEqual(
            rota["tipo"],
            "http",
        )

        self.assertTrue(
            rota["interna"],
        )

        self.assertEqual(
            rota["confianca"],
            "alta",
        )

    def test_online_resultado_possui_urls(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        self.assertEqual(
            resultado.urls,
            [],
        )


    def test_online_resultado_possui_url_estruturada(self):
        from online.modelos import OnlineResultado

        resultado = OnlineResultado(
            alvo="https://exemplo.test/"
        )

        url = {
            "url": "https://api.exemplo.test:8443/api/clientes?id=10#dados",
            "esquema": "https",
            "host": "api.exemplo.test",
            "porta": 8443,
            "caminho": "/api/clientes",
            "query": "id=10",
            "fragmento": "dados",
            "origens": ["javascript"],
            "interna": False,
            "tipo": "http",
        }

        resultado.urls.append(url)

        self.assertEqual(
            len(resultado.urls),
            1,
        )

        self.assertEqual(
            resultado.urls[0]["url"],
            "https://api.exemplo.test:8443/api/clientes?id=10#dados",
        )

        self.assertEqual(
            resultado.urls[0]["esquema"],
            "https",
        )

        self.assertEqual(
            resultado.urls[0]["host"],
            "api.exemplo.test",
        )

        self.assertEqual(
            resultado.urls[0]["porta"],
            8443,
        )

        self.assertEqual(
            resultado.urls[0]["caminho"],
            "/api/clientes",
        )

        self.assertEqual(
            resultado.urls[0]["query"],
            "id=10",
        )

        self.assertEqual(
            resultado.urls[0]["fragmento"],
            "dados",
        )

        self.assertEqual(
            resultado.urls[0]["origens"],
            ["javascript"],
        )

        self.assertFalse(
            resultado.urls[0]["interna"],
        )

        self.assertEqual(
            resultado.urls[0]["tipo"],
            "http",
        )


    def test_normaliza_url_observada(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "https://api.exemplo.test:8443/api/clientes?id=10#dados",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            resultado["url"],
            "https://api.exemplo.test:8443/api/clientes?id=10#dados",
        )

        self.assertEqual(
            resultado["esquema"],
            "https",
        )

        self.assertEqual(
            resultado["host"],
            "api.exemplo.test",
        )

        self.assertEqual(
            resultado["porta"],
            8443,
        )

        self.assertEqual(
            resultado["caminho"],
            "/api/clientes",
        )

        self.assertEqual(
            resultado["query"],
            "id=10",
        )

        self.assertEqual(
            resultado["fragmento"],
            "dados",
        )

        self.assertEqual(
            resultado["origens"],
            ["javascript"],
        )

        self.assertFalse(
            resultado["interna"],
        )

        self.assertEqual(
            resultado["tipo"],
            "http",
        )


    def test_normaliza_url_relativa(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "/api/clientes?id=10",
            base_url="https://exemplo.test/app/",
            origem="html",
        )

        self.assertEqual(
            resultado["url"],
            "https://exemplo.test/api/clientes?id=10",
        )

        self.assertEqual(
            resultado["esquema"],
            "https",
        )

        self.assertEqual(
            resultado["host"],
            "exemplo.test",
        )

        self.assertEqual(
            resultado["porta"],
            443,
        )

        self.assertEqual(
            resultado["caminho"],
            "/api/clientes",
        )

        self.assertEqual(
            resultado["query"],
            "id=10",
        )

        self.assertEqual(
            resultado["origens"],
            ["html"],
        )

        self.assertTrue(
            resultado["interna"],
        )

    def test_normaliza_url_http(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "http://exemplo.test/",
            base_url="http://exemplo.test/",
            origem="http",
        )

        self.assertEqual(
            resultado["esquema"],
            "http",
        )

        self.assertEqual(
            resultado["porta"],
            80,
        )

        self.assertEqual(
            resultado["tipo"],
            "http",
        )

        self.assertTrue(
            resultado["interna"],
        )

    def test_normaliza_url_websocket(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "wss://ws.exemplo.test/socket",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            resultado["esquema"],
            "wss",
        )

        self.assertEqual(
            resultado["host"],
            "ws.exemplo.test",
        )

        self.assertEqual(
            resultado["porta"],
            443,
        )

        self.assertEqual(
            resultado["tipo"],
            "websocket",
        )

        self.assertFalse(
            resultado["interna"],
        )

    def test_normaliza_url_externa(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "https://cdn.externo.test/app.js",
            base_url="https://exemplo.test/",
            origem="html",
        )

        self.assertFalse(
            resultado["interna"],
        )

        self.assertEqual(
            resultado["host"],
            "cdn.externo.test",
        )

    def test_normaliza_url_com_fragmento(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "/clientes/10?modo=detalhado#perfil",
            base_url="https://exemplo.test/",
            origem="html",
        )

        self.assertEqual(
            resultado["query"],
            "modo=detalhado",
        )

        self.assertEqual(
            resultado["fragmento"],
            "perfil",
        )

    def test_normaliza_url_invalida(self):
        from online.urls import normalizar_url

        resultado = normalizar_url(
            "://url-invalida",
            base_url="https://exemplo.test/",
            origem="javascript",
        )

        self.assertEqual(
            resultado,
            {},
        )


if __name__ == "__main__":
    unittest.main()
