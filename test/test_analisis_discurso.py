from src.analisis_discurso import AnalisisDiscurso


TEXTO = """
Mexico impulsa la educacion tecnologica. El Instituto Tecnologico de Morelia
desarrolla proyectos de inteligencia artificial. Mexico necesita profesionales
en ciencia de datos, programacion y recuperacion de informacion.
"""


def test_analisis_discurso_calcula_ngramas_y_riqueza():
    analizador = AnalisisDiscurso()

    resultado = analizador.analizar(TEXTO, "Discurso")

    assert resultado["titulo"] == "Discurso"
    assert resultado["oraciones"] >= 2
    assert resultado["palabras_totales"] > 10
    assert resultado["vocabulario_unico"] > 0
    assert 0 < resultado["riqueza_lexica_global"] <= 1
    assert len(resultado["riqueza_por_seccion"]) >= 1
    assert resultado["top_bigramas"]
    assert resultado["top_trigramas"]


def test_analisis_discurso_detecta_entidades_heuristicas():
    analizador = AnalisisDiscurso()

    resultado = analizador.analizar(TEXTO, "Discurso")
    entidades = [entidad for entidad, _ in resultado["posibles_entidades"]]

    assert "Mexico" in entidades
    assert "Instituto" in entidades
    assert "Morelia" in entidades


def test_analisis_discurso_compara_textos():
    analizador = AnalisisDiscurso()
    analisis_1 = analizador.analizar(TEXTO, "Texto A")
    analisis_2 = analizador.analizar("Python y datos. Python permite analizar datos.", "Texto B")

    comparativa = analizador.comparar_textos([analisis_1, analisis_2])

    assert len(comparativa) == 2
    assert comparativa[0]["titulo"] == "Texto A"
    assert set(comparativa[0]) == {"titulo", "palabras", "vocabulario", "riqueza", "promedio_oracion"}
