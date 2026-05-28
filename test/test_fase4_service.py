from pathlib import Path

from src.fase4_service import Fase4Service


def _corpus():
    return [
        {
            "titulo": "IA generativa",
            "cuerpo": "La inteligencia artificial transforma software.",
            "categoria_predicha": "tecnologia",
            "sentimiento": {"etiqueta": "positivo"},
            "terminos_relevantes": ["inteligencia", "artificial", "software"],
        },
        {
            "titulo": "Python y datos",
            "cuerpo": "Python ayuda a crear modelos de inteligencia artificial.",
            "categoria_predicha": "tecnologia",
            "sentimiento": {"etiqueta": "neutral"},
            "terminos_relevantes": ["python", "modelos", "inteligencia"],
        },
        {
            "titulo": "Mercados financieros",
            "cuerpo": "La economia registra volatilidad en bolsa.",
            "categoria_predicha": "economia",
            "sentimiento": {"etiqueta": "negativo"},
            "terminos_relevantes": ["economia", "bolsa", "volatilidad"],
        },
        {
            "titulo": "Banco central",
            "cuerpo": "Tasas de interes e inflacion afectan mercados.",
            "categoria_predicha": "economia",
            "sentimiento": {"etiqueta": "neutral"},
            "terminos_relevantes": ["tasas", "inflacion", "mercados"],
        },
    ]


def test_fase4_busca_con_modelo_booleano_y_vectorial():
    service = Fase4Service()
    service.construir_indice(_corpus())

    booleanos = service.buscar_con_modelo("inteligencia artificial", modelo="booleano")
    vectoriales = service.buscar_con_modelo("inteligencia artificial", modelo="vectorial")

    assert booleanos
    assert vectoriales
    assert all("doc_id" in item for item in vectoriales)


def test_fase4_evalua_modelos_y_exporta_ac5(tmp_path):
    service = Fase4Service()
    service.construir_indice(_corpus())
    ruta = tmp_path / "resultados_ac5.json"

    evidencia = service.evaluar_modelos_busqueda(ruta)

    assert evidencia["estado"] == "completo"
    assert evidencia["total_consultas"] >= 1
    assert evidencia["ganador_f1"] in {"booleano", "vectorial"}
    assert 0 <= evidencia["map_booleano"] <= 1
    assert 0 <= evidencia["map_vectorial"] <= 1
    assert Path(evidencia["archivo_json"]).exists()


def test_fase4_usa_consultas_configuradas_por_categoria(tmp_path):
    service = Fase4Service()
    service.construir_indice(_corpus())
    consultas = tmp_path / "consultas_ac5.json"
    consultas.write_text(
        '[{"consulta":"software artificial","categoria_relevante":"tecnologia"}]',
        encoding="utf-8",
    )

    evidencia = service.evaluar_modelos_busqueda(tmp_path / "resultados_ac5.json", consultas)

    assert evidencia["estado"] == "completo"
    assert evidencia["origen_consultas"] == "config/consultas_ac5.json"
    assert evidencia["total_consultas"] == 1
    assert evidencia["resultados"][0]["relevantes"] == [0, 1]
