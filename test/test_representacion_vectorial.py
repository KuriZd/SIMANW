from src.representacion_vectorial import RepresentacionVectorial


def test_representacion_vectorial_construye_matriz_tfidf():
    documentos = [
        "inteligencia artificial modelos generativos",
        "mercados financieros volatilidad inversores",
        "inteligencia artificial automatiza procesos",
    ]
    representacion = RepresentacionVectorial()

    matriz = representacion.construir_matriz(documentos)
    info = representacion.info_matriz()

    assert matriz.shape[0] == 3
    assert info["documentos"] == 3
    assert info["features"] > 0
    assert info["densidad"] > 0


def test_representacion_vectorial_obtiene_top_terminos():
    documentos = [
        "python rendimiento optimizacion python",
        "clima calentamiento global estudio",
    ]
    representacion = RepresentacionVectorial()
    representacion.construir_matriz(documentos)

    top = representacion.top_terminos_documento(0, n=3)

    assert len(top) > 0
    assert top[0][1] > 0
    assert any(termino == "python" for termino, _peso in top)
