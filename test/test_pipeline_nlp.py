from src.pipeline_nlp import PipelineNLP


def test_pipeline_nlp_limpia_texto_en_espanol():
    pipeline = PipelineNLP()

    texto = "La IA generativa crece en 2026, y transforma industrias."
    limpio = pipeline.limpiar(texto)

    assert limpio == "la ia generativa crece en y transforma industrias"


def test_pipeline_nlp_procesa_texto_con_metricas():
    pipeline = PipelineNLP()

    resultado = pipeline.procesar("La inteligencia artificial transforma la industria. La IA avanza rapido.")

    assert "inteligencia" in resultado["sin_stopwords"]
    assert "artificial" in resultado["sin_stopwords"]
    assert "la" not in resultado["sin_stopwords"]
    assert resultado["num_oraciones"] == 2
    assert resultado["vocabulario_unico"] > 0
    assert 0 < resultado["riqueza_lexica"] <= 1


def test_pipeline_nlp_estadisticas_corpus():
    pipeline = PipelineNLP()
    textos = [
        pipeline.procesar("Python mejora el rendimiento de aplicaciones."),
        pipeline.procesar("Python y datos abiertos impulsan tecnologia."),
    ]

    stats = pipeline.estadisticas_corpus(textos)

    assert stats["total_documentos"] == 2
    assert stats["total_tokens"] > 0
    assert stats["vocabulario_total"] > 0
    assert stats["palabras_frecuentes"][0][0] == "python"
