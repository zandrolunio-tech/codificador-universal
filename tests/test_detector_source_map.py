from online.detector_source_map import detectar_source_maps


def test_detecta_source_mapping_url_com_hash():
    codigo = "//# sourceMappingURL=app.js.map"

    resultado = detectar_source_maps(
        codigo,
        origem="script_inline",
        arquivo="https://exemplo.test/app.js",
        script_url="https://exemplo.test/app.js",
    )

    assert len(resultado) == 1
    assert resultado[0]["referencia"] == "app.js.map"
    assert resultado[0]["tipo"] == "relativa"
    assert resultado[0]["url"] == "https://exemplo.test/app.js.map"
    assert resultado[0]["linha"] == 1
    assert resultado[0]["classificacao"] == "SOURCE_MAP_REFERENCIA"
    assert resultado[0]["confianca"] == "ALTA"


def test_detecta_source_mapping_url_com_at():
    codigo = "//@ sourceMappingURL=app.js.map"

    resultado = detectar_source_maps(
        codigo,
        script_url="https://exemplo.test/static/app.js",
    )

    assert len(resultado) == 1
    assert resultado[0]["referencia"] == "app.js.map"


def test_detecta_referencia_absoluta_site():
    codigo = "//# sourceMappingURL=/static/js/app.js.map"

    resultado = detectar_source_maps(
        codigo,
        script_url="https://exemplo.test/js/app.js",
    )

    assert len(resultado) == 1
    assert resultado[0]["tipo"] == "absoluta_site"
    assert resultado[0]["url"] == (
        "https://exemplo.test/static/js/app.js.map"
    )


def test_detecta_url_absoluta():
    codigo = (
        "//# sourceMappingURL="
        "https://cdn.exemplo.test/app.js.map"
    )

    resultado = detectar_source_maps(
        codigo,
        script_url="https://exemplo.test/app.js",
    )

    assert len(resultado) == 1
    assert resultado[0]["tipo"] == "absoluta"
    assert resultado[0]["url"] == (
        "https://cdn.exemplo.test/app.js.map"
    )


def test_detecta_espacos_ao_redor_do_igual():
    codigo = "//# sourceMappingURL = app.js.map"

    resultado = detectar_source_maps(
        codigo,
        script_url="https://exemplo.test/app.js",
    )

    assert len(resultado) == 1
    assert resultado[0]["referencia"] == "app.js.map"


def test_detecta_multiplas_referencias():
    codigo = (
        "//# sourceMappingURL=primeiro.js.map\n"
        "const x = 1;\n"
        "//@ sourceMappingURL=segundo.js.map\n"
    )

    resultado = detectar_source_maps(
        codigo,
        script_url="https://exemplo.test/app.js",
    )

    assert len(resultado) == 2
    assert resultado[0]["referencia"] == "primeiro.js.map"
    assert resultado[0]["linha"] == 1
    assert resultado[1]["referencia"] == "segundo.js.map"
    assert resultado[1]["linha"] == 3


def test_nao_detecta_comentario_comum():
    codigo = "// sourceMappingURL=app.js.map"

    assert detectar_source_maps(codigo) == []


def test_nao_detecta_string():
    codigo = (
        'const texto = "//# sourceMappingURL=falso.js.map";'
    )

    assert detectar_source_maps(codigo) == []


def test_nao_detecta_sem_referencia():
    codigo = "//# sourceMappingURL="

    assert detectar_source_maps(codigo) == []


def test_nao_detecta_codigo_vazio():
    assert detectar_source_maps("") == []


def test_preserva_origem_arquivo_e_script_url():
    codigo = "//# sourceMappingURL=app.js.map"

    resultado = detectar_source_maps(
        codigo,
        origem="script_inline",
        arquivo="https://exemplo.test/pagina",
        script_url="https://exemplo.test/static/app.js",
        linguagem="javascript",
    )

    assert resultado[0]["origem"] == "script_inline"
    assert resultado[0]["arquivo"] == (
        "https://exemplo.test/pagina"
    )
    assert resultado[0]["script_url"] == (
        "https://exemplo.test/static/app.js"
    )
    assert resultado[0]["linguagem"] == "javascript"
    assert resultado[0]["evidencia"] == (
        "//# sourceMappingURL=app.js.map"
    )
