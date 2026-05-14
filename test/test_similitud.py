import pytest

from src.representacion_vectorial import RepresentacionVectorial
from src.similitud import CalculadorSimilitud


def test_calculador_similitud_diagonal_es_uno():
    representacion = RepresentacionVectorial()
    matriz = representacion.construir_matriz(
        [
            "inteligencia artificial modelos",
            "mercados financieros bolsa",
            "cambio climatico temperatura",
        ]
    )
    calculador = CalculadorSimilitud(matriz)

    assert calculador.similitud_par(0, 0) == pytest.approx(1.0)
    assert calculador.similitud_par(1, 1) == pytest.approx(1.0)


def test_calculador_similitud_encuentra_documentos_similares():
    representacion = RepresentacionVectorial()
    matriz = representacion.construir_matriz(
        [
            "inteligencia artificial modelos generativos",
            "inteligencia artificial automatiza procesos",
            "mercados financieros bolsa inversion",
        ]
    )
    calculador = CalculadorSimilitud(matriz)

    similares = calculador.documentos_similares(0, top_n=1)

    assert similares[0][0] == 1
    assert similares[0][1] > 0


def test_calculador_similitud_agrupa_por_umbral():
    representacion = RepresentacionVectorial()
    matriz = representacion.construir_matriz(
        [
            "python datos ciencia",
            "python datos analisis",
            "futbol torneo liga",
        ]
    )
    calculador = CalculadorSimilitud(matriz)

    grupos = calculador.agrupar_por_similitud(umbral=0.1)

    assert [0, 1] in grupos
    assert [2] in grupos
