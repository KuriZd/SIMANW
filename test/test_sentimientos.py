from src.sentimientos import AnalizadorSentimientos


def test_analizador_sentimientos_devuelve_scores_y_etiqueta():
    analizador = AnalizadorSentimientos()

    resultado = analizador.analizar("This is excellent, successful and very good news.")

    assert resultado["etiqueta"] == "positivo"
    assert resultado["compound"] > 0
    assert set(resultado) == {"positivo", "negativo", "neutral", "compound", "etiqueta"}


def test_analizador_sentimientos_analiza_corpus_vacio():
    analizador = AnalizadorSentimientos()

    resultados, resumen = analizador.analizar_corpus([])

    assert resultados == []
    assert resumen["distribucion"] == {}
    assert resumen["tono_general"] == "neutral"


def test_analizador_sentimientos_agrega_resultado_a_noticias():
    analizador = AnalizadorSentimientos()
    noticias = [{"cuerpo": "This is bad, risky and worrying."}]

    resultados, resumen = analizador.analizar_noticias(noticias)

    assert len(resultados) == 1
    assert "sentimiento" in noticias[0]
    assert resumen["distribucion"]


def test_analizador_sentimientos_usa_lexico_espanol():
    analizador = AnalizadorSentimientos()

    negativo = analizador.analizar("Los mercados muestran volatilidad e incertidumbre preocupante.")
    positivo = analizador.analizar("La nueva tecnologia trae mejoras y avances significativos.")

    assert negativo["etiqueta"] == "negativo"
    assert positivo["etiqueta"] == "positivo"


def test_analizador_sentimientos_maneja_noticias_sin_cuerpo():
    analizador = AnalizadorSentimientos()
    noticias = [{"titulo": "Avances", "resumen": "mejoras y avances significativos"}]

    resultados, resumen = analizador.analizar_noticias(noticias)

    assert resultados[0]["etiqueta"] == "positivo"
    assert resumen["distribucion"]["positivo"] == 1
