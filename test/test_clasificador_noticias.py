from src.clasificador_noticias import (
    ETIQUETAS_ENTRENAMIENTO,
    TEXTOS_ENTRENAMIENTO,
    ClasificadorNoticias,
)


def test_clasificador_entrena_con_categorias_esperadas():
    clasificador = ClasificadorNoticias()

    resultado = clasificador.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)

    assert resultado["n_muestras"] == len(TEXTOS_ENTRENAMIENTO)
    assert set(resultado["categorias"]) == {"tecnologia", "economia", "ciencia", "politica"}
    assert 0 <= resultado["accuracy_cv"] <= 1
    assert clasificador.entrenado


def test_clasificador_predice_texto_tecnologico():
    clasificador = ClasificadorNoticias()
    clasificador.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)

    prediccion, scores = clasificador.predecir_con_confianza(
        "software de inteligencia artificial para programacion y automatizacion"
    )

    assert prediccion == "tecnologia"
    assert set(scores) == {"tecnologia", "economia", "ciencia", "politica"}


def test_clasificador_agrega_prediccion_a_noticias():
    clasificador = ClasificadorNoticias()
    clasificador.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)
    noticias = [
        {
            "titulo": "Banco central sube tasas",
            "cuerpo": "Los mercados financieros reaccionaron ante la politica monetaria.",
        }
    ]

    clasificador.clasificar_noticias(noticias)

    assert noticias[0]["categoria_predicha"] == "economia"
    assert "scores_categoria" in noticias[0]


def test_clasificador_valida_datos_de_entrenamiento_vacios():
    clasificador = ClasificadorNoticias()

    try:
        clasificador.entrenar([], [])
    except ValueError as exc:
        assert "vacios" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError")


def test_clasificador_usa_resumen_si_falta_cuerpo():
    clasificador = ClasificadorNoticias()
    clasificador.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)
    noticias = [{"titulo": "Mercados", "resumen": "bolsa acciones inversion y finanzas"}]

    clasificador.clasificar_noticias(noticias)

    assert noticias[0]["categoria_predicha"] == "economia"
