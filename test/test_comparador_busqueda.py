import pytest

from src.comparador_busqueda import CONSULTAS_EVAL_AC5, ComparadorModelos


def documentos_demo():
    return [
        {
            "titulo": "Inteligencia artificial generativa",
            "cuerpo": "La inteligencia artificial transforma software y programacion.",
        },
        {
            "titulo": "Mercados financieros",
            "cuerpo": "La economia enfrenta volatilidad en mercado de valores.",
        },
        {
            "titulo": "Cambio climatico",
            "cuerpo": "Investigadores estudian calentamiento global y carbono.",
        },
        {
            "titulo": "Python para inteligencia artificial",
            "cuerpo": "Python ayuda a crear aplicaciones de machine learning.",
        },
        {
            "titulo": "Datos abiertos gobierno",
            "cuerpo": "El gobierno publica datos abiertos para transparencia.",
        },
    ]


def test_comparador_busqueda_booleana_y_vectorial():
    comparador = ComparadorModelos(documentos_demo())

    assert comparador.busqueda_booleana("inteligencia artificial") == [0, 3]

    resultados_vectoriales = comparador.busqueda_vectorial("inteligencia artificial", top_k=3)

    assert resultados_vectoriales
    assert resultados_vectoriales[0][0] in {0, 3}
    assert resultados_vectoriales[0][1] > 0


def test_comparador_evalua_ambos_modelos():
    comparador = ComparadorModelos(documentos_demo())

    resultado = comparador.evaluar_ambos("datos abiertos gobierno", [4])

    assert resultado["consulta"] == "datos abiertos gobierno"
    assert resultado["booleano"]["recuperados"] == 1
    assert resultado["booleano"]["precision"] == 1.0
    assert "precision_at_k" in resultado["booleano"]
    assert "average_precision" in resultado["booleano"]
    assert resultado["vectorial"]["recuperados"] >= 1
    assert resultado["vectorial"]["recall"] == 1.0


def test_comparador_genera_reporte_y_promedios():
    comparador = ComparadorModelos(documentos_demo())

    evaluacion = comparador.evaluar_consultas(CONSULTAS_EVAL_AC5)
    reporte = comparador.reporte(CONSULTAS_EVAL_AC5)

    assert len(evaluacion["resultados"]) == 4
    assert evaluacion["ganador_precision"] in {"booleano", "vectorial"}
    assert evaluacion["ganador_map"] in {"booleano", "vectorial"}
    assert 0 <= evaluacion["map_booleano"] <= 1
    assert 0 <= evaluacion["map_vectorial"] <= 1
    assert "PROMEDIO" in reporte
    assert "Conclusion" in reporte


def test_comparador_genera_consultas_desde_corpus_real():
    from src.comparador_busqueda import generar_consultas_desde_corpus

    docs = [
        {**doc, "categoria_predicha": "tecnologia" if idx in {0, 3} else "general"}
        for idx, doc in enumerate(documentos_demo())
    ]

    consultas = generar_consultas_desde_corpus(docs)

    assert consultas
    assert all("consulta" in item and "relevantes" in item for item in consultas)


def test_comparador_requiere_documentos():
    with pytest.raises(ValueError):
        ComparadorModelos([])
