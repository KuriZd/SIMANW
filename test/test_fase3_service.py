from pathlib import Path

from src.fase3_service import Fase3Service


def _noticias_supervisadas():
    base = [
        ("IA aplicada", "software inteligencia artificial datos modelos", "tecnologia"),
        ("Nueva plataforma", "aplicacion digital programacion cloud software", "tecnologia"),
        ("Mercados suben", "bolsa inversion mercados financieros acciones", "economia"),
        ("Banco central", "inflacion tasas interes economia monetaria", "economia"),
        ("Vacuna experimental", "investigacion cientifica laboratorio pacientes salud", "ciencia"),
        ("Mision espacial", "cohete satelite espacio nasa exploracion", "ciencia"),
        ("Reforma aprobada", "congreso gobierno ley reforma legisladores", "politica"),
        ("Elecciones locales", "presidente candidato democracia partido voto", "politica"),
    ]
    return [
        {
            "titulo": titulo,
            "cuerpo": cuerpo,
            "texto_original": cuerpo,
            "texto_limpio": cuerpo,
            "categoria": categoria,
            "fecha": "2026-01-01",
            "autor": "SIMANW",
            "url": f"https://simanw.local/{idx}",
            "tokens": cuerpo.split(),
            "terminos": cuerpo.split(),
            "stems": cuerpo.split(),
            "num_tokens": len(cuerpo.split()),
            "num_terminos": len(cuerpo.split()),
            "num_oraciones": 1,
            "vocabulario_unico": len(set(cuerpo.split())),
            "riqueza_lexica": 1.0,
            "terminos_relevantes": cuerpo.split()[:3],
        }
        for idx, (titulo, cuerpo, categoria) in enumerate(base)
    ]


def test_fase3_integra_ac3_multimodelo_y_recomendaciones():
    corpus = _noticias_supervisadas()
    service = Fase3Service()

    noticias, corpus_enriquecido, analisis = service.analizar(corpus, corpus)

    ac3 = analisis["clasificacion"]["ac3"]
    assert ac3["estado"] == "completo"
    assert ac3["mejor_modelo"]
    assert 0 <= ac3["accuracy"] <= 1
    assert set(ac3["modelos_comparados"]) == {
        "Naive Bayes",
        "SVM Lineal",
        "Logistic Regression",
        "Random Forest",
    }
    assert all(noticia.get("categoria_predicha") for noticia in noticias)
    assert all(item.get("recomendaciones") is not None for item in corpus_enriquecido)
    assert analisis["recomendaciones"]["disponible"]
    assert analisis["temas_conversacion"]["disponible"]
    assert Path("data/resultados_ac3.json").exists()


def test_fase3_ac3_corpus_pequeno_no_rompe_pipeline():
    corpus = _noticias_supervisadas()[:3]
    service = Fase3Service()

    noticias, corpus_enriquecido, analisis = service.analizar(corpus, corpus)

    ac3 = analisis["clasificacion"]["ac3"]
    assert ac3["estado"] == "parcial"
    assert noticias
    assert corpus_enriquecido


def test_fase3_sentimiento_dominante_usa_mayoria_no_promedio():
    corpus = _noticias_supervisadas()[:3]
    service = Fase3Service()

    class AnalizadorFake:
        def analizar_noticias(self, _noticias):
            return [
                {"etiqueta": "neutral", "compound": 0.0, "positivo": 0.0, "negativo": 0.0, "neutral": 1.0},
                {"etiqueta": "neutral", "compound": 0.0, "positivo": 0.0, "negativo": 0.0, "neutral": 1.0},
                {"etiqueta": "positivo", "compound": 0.9, "positivo": 1.0, "negativo": 0.0, "neutral": 0.0},
            ], {
                "distribucion": {"neutral": 2, "positivo": 1},
                "sentimiento_promedio": 0.3,
                "tono_general": "positivo",
            }

    service._analizador = AnalizadorFake()

    _noticias, _corpus, analisis = service.analizar(corpus, corpus)

    assert analisis["sentimientos"] == {"neutral": 2, "positivo": 1}
    assert analisis["sentimiento_dominante"] == "neutral"
    assert analisis["tono_general"] == "positivo"
    assert analisis["sentimiento_promedio"] == 0.3
