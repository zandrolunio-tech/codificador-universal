import unittest

from online.evidencias import (
    _normalizar_severidade,
    criar_evidencia,
    evidenciar_status_http,
    evidenciar_tls,
    ordenar_evidencias,
    serializar_evidencias,
)
from online.modelos import Evidencia


class TestCriarEvidencia(unittest.TestCase):

    def test_cria_evidencia_com_valores_normalizados(self):
        evidencia = criar_evidencia(
            identificador="TESTE-001",
            titulo="Evidência de teste",
            categoria="teste",
            descricao="Descrição de teste",
            confianca="alta",
            severidade="ALTO",
            origem="teste",
            observacao="observado",
            recomendacao="revisar",
            metadados={"chave": "valor"},
        )

        self.assertIsInstance(evidencia, Evidencia)
        self.assertEqual(
            evidencia.identificador,
            "TESTE-001",
        )
        self.assertEqual(
            evidencia.confianca,
            "ALTA",
        )
        self.assertEqual(
            evidencia.detalhes["severidade"],
            "alto",
        )
        self.assertEqual(
            evidencia.detalhes["observacao"],
            "observado",
        )
        self.assertEqual(
            evidencia.detalhes["recomendacao"],
            "revisar",
        )
        self.assertEqual(
            evidencia.detalhes["metadados"]["chave"],
            "valor",
        )

    def test_severidade_desconhecida_vira_informativo(self):
        self.assertEqual(
            _normalizar_severidade("inexistente"),
            "informativo",
        )

    def test_severidade_vazia_vira_informativo(self):
        self.assertEqual(
            _normalizar_severidade(""),
            "informativo",
        )


class TestEvidenciarStatusHTTP(unittest.TestCase):

    def test_status_2xx(self):
        evidencia = evidenciar_status_http(200)

        self.assertEqual(
            evidencia.identificador,
            "HTTP-STATUS",
        )
        self.assertEqual(
            evidencia.categoria,
            "http",
        )
        self.assertEqual(
            evidencia.detalhes["severidade"],
            "informativo",
        )
        self.assertEqual(
            evidencia.detalhes["observacao"],
            "HTTP 200",
        )

    def test_status_3xx(self):
        evidencia = evidenciar_status_http(302)

        self.assertEqual(
            evidencia.detalhes["severidade"],
            "informativo",
        )
        self.assertIn(
            "Redirecionamento",
            evidencia.titulo,
        )

    def test_status_4xx(self):
        evidencia = evidenciar_status_http(404)

        self.assertEqual(
            evidencia.detalhes["severidade"],
            "informativo",
        )
        self.assertIn(
            "cliente",
            evidencia.titulo,
        )

    def test_status_5xx(self):
        evidencia = evidenciar_status_http(500)

        self.assertEqual(
            evidencia.detalhes["severidade"],
            "medio",
        )
        self.assertIn(
            "servidor",
            evidencia.titulo,
        )


class TestEvidenciarTLS(unittest.TestCase):

    def test_tls_nao_detectado_nao_produz_evidencias(self):
        resultado = evidenciar_tls(
            {
                "detectado": False,
                "sucesso": False,
            }
        )

        self.assertEqual(resultado, [])

    def test_tls_sucesso_produz_evidencias_basicas(self):
        resultado = evidenciar_tls(
            {
                "detectado": True,
                "sucesso": True,
                "versao_tls": "TLSv1.3",
                "certificado": {},
                "erros": [],
            }
        )

        ids = {
            evidencia.identificador
            for evidencia in resultado
        }

        self.assertIn(
            "TLS-CONEXAO",
            ids,
        )
        self.assertIn(
            "TLS-VERSAO",
            ids
        )

    def test_tls_com_certificado_e_san(self):
        resultado = evidenciar_tls(
            {
                "detectado": True,
                "sucesso": True,
                "versao_tls": "TLSv1.3",
                "certificado": {
                    "not_after": "2030-01-01",
                    "dias_para_expirar": 100,
                    "subject_alt_names": [
                        "example.test",
                        "www.example.test",
                    ],
                },
                "erros": [],
            }
        )

        ids = {
            evidencia.identificador
            for evidencia in resultado
        }

        self.assertIn(
            "TLS-CERT-VALIDADE",
            ids,
        )
        self.assertIn(
            "TLS-CERT-SAN",
            ids,
        )

    def test_tls_certificado_expirado_tem_severidade_alta(self):
        resultado = evidenciar_tls(
            {
                "detectado": True,
                "sucesso": True,
                "versao_tls": "TLSv1.2",
                "certificado": {
                    "not_after": "2020-01-01",
                    "dias_para_expirar": -1,
                    "subject_alt_names": [],
                },
                "erros": [],
            }
        )

        validade = next(
            evidencia
            for evidencia in resultado
            if evidencia.identificador
            == "TLS-CERT-VALIDADE"
        )

        self.assertEqual(
            validade.detalhes["severidade"],
            "alto",
        )

    def test_tls_certificado_proximo_de_expirar_tem_severidade_media(self):
        resultado = evidenciar_tls(
            {
                "detectado": True,
                "sucesso": True,
                "versao_tls": "TLSv1.3",
                "certificado": {
                    "not_after": "2026-09-01",
                    "dias_para_expirar": 30,
                    "subject_alt_names": [],
                },
                "erros": [],
            }
        )

        validade = next(
            evidencia
            for evidencia in resultado
            if evidencia.identificador
            == "TLS-CERT-VALIDADE"
        )

        self.assertEqual(
            validade.detalhes["severidade"],
            "medio",
        )

    def test_tls_com_erro_produz_evidencia_de_erro(self):
        resultado = evidenciar_tls(
            {
                "detectado": True,
                "sucesso": False,
                "erros": [
                    "Timeout: conexão excedeu o limite."
                ],
            }
        )

        self.assertEqual(
            len(resultado),
            1,
        )
        self.assertEqual(
            resultado[0].identificador,
            "TLS-ERRO",
        )
        self.assertIn(
            "Timeout",
            resultado[0].detalhes["observacao"],
        )


class TestOrdenacaoEvidencias(unittest.TestCase):

    def test_ordena_por_severidade(self):
        informativo = criar_evidencia(
            "EVID-INFO",
            "Informativo",
            "teste",
            "Teste",
            severidade="informativo",
        )

        alto = criar_evidencia(
            "EVID-ALTO",
            "Alto",
            "teste",
            "Teste",
            severidade="alto",
        )

        critico = criar_evidencia(
            "EVID-CRITICO",
            "Crítico",
            "teste",
            "Teste",
            severidade="critico",
        )

        resultado = ordenar_evidencias(
            [
                informativo,
                critico,
                alto,
            ]
        )

        self.assertEqual(
            [
                item.identificador
                for item in resultado
            ],
            [
                "EVID-CRITICO",
                "EVID-ALTO",
                "EVID-INFO",
            ],
        )

    def test_desempate_por_identificador(self):
        primeiro = criar_evidencia(
            "EVID-A",
            "A",
            "teste",
            "Teste",
            severidade="medio",
        )

        segundo = criar_evidencia(
            "EVID-B",
            "B",
            "teste",
            "Teste",
            severidade="medio",
        )

        resultado = ordenar_evidencias(
            [
                segundo,
                primeiro,
            ]
        )

        self.assertEqual(
            [
                item.identificador
                for item in resultado
            ],
            [
                "EVID-B",
                "EVID-A",
            ],
        )


class TestSerializacaoEvidencias(unittest.TestCase):

    def test_serializa_evidencias(self):
        evidencia = criar_evidencia(
            identificador="TESTE-001",
            titulo="Teste",
            categoria="teste",
            descricao="Descrição",
            severidade="baixo",
        )

        resultado = serializar_evidencias(
            [evidencia]
        )

        self.assertIsInstance(
            resultado,
            list,
        )
        self.assertEqual(
            len(resultado),
            1,
        )
        self.assertIsInstance(
            resultado[0],
            dict,
        )
        self.assertEqual(
            resultado[0]["identificador"],
            "TESTE-001",
        )
        self.assertEqual(
            resultado[0]["detalhes"]["severidade"],
            "baixo",
        )


if __name__ == "__main__":
    unittest.main()
