import pytest

from src.selector_modelo import ETIQUETAS_AC3, TEXTOS_AC3, SelectorModelo


def test_selector_modelo_evalua_y_selecciona_mejor():
    selector = SelectorModelo()

    resultados = selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)

    assert set(resultados) == {"Naive Bayes", "SVM Lineal", "Logistic Regression", "Random Forest"}
    assert selector.mejor_modelo is not None
    assert selector.mejor_modelo[0] in resultados
    assert "accuracy_mean" in resultados[selector.mejor_modelo[0]]


def test_selector_modelo_predice_con_modelo_seleccionado():
    selector = SelectorModelo()
    selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)

    predicciones = selector.predecir(
        [
            "nueva aplicacion de machine learning para detectar fraudes",
            "el presidente anuncio reformas al sistema de justicia",
        ]
    )

    assert len(predicciones) == 2
    assert set(predicciones) <= {"tecnologia", "economia", "ciencia", "politica"}


def test_selector_modelo_reporte_marca_mejor_modelo():
    selector = SelectorModelo()
    selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)

    reporte = selector.reporte()

    assert "Modelo" in reporte
    assert "Accuracy" in reporte
    assert "*" in reporte


def test_selector_modelo_valida_datos():
    selector = SelectorModelo()

    with pytest.raises(ValueError):
        selector.predecir(["texto sin entrenar"])

    with pytest.raises(ValueError):
        selector.evaluar_todos(["a"], ["x", "y"])

    with pytest.raises(ValueError):
        selector.evaluar_todos(["a", "b"], ["x", "y"], cv_folds=1)


def test_selector_modelo_rechaza_una_sola_clase():
    selector = SelectorModelo()
    with pytest.raises(ValueError, match="al menos dos clases"):
        selector.evaluar_todos(["texto a", "texto b"], ["misma", "misma"])


def test_selector_modelo_ajusta_folds_con_pocas_muestras():
    selector = SelectorModelo()
    textos = ["texto a uno", "texto b dos", "texto c tres", "texto d cuatro"]
    etiquetas = ["A", "A", "B", "B"]
    resultados = selector.evaluar_todos(textos, etiquetas, cv_folds=5)
    assert selector.mejor_modelo is not None
    for nombre, metricas in resultados.items():
        if "accuracy_mean" in metricas:
            assert len(metricas["scores"]) <= 2


def test_selector_modelo_round_trip_guardar_cargar(tmp_path):
    selector = SelectorModelo()
    selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)
    ruta_modelo = tmp_path / "modelo.joblib"
    ruta_vec = tmp_path / "vectorizer.joblib"
    selector.guardar_modelo(ruta_modelo, ruta_vec)

    selector2 = SelectorModelo()
    selector2.cargar_modelo(ruta_modelo, ruta_vec)
    preds = selector2.predecir(["inteligencia artificial machine learning"])
    assert preds[0] in {"tecnologia", "economia", "ciencia", "politica"}


def test_selector_modelo_predice_con_mismo_vectorizador():
    selector = SelectorModelo()
    selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)
    pred = selector.predecir(["inflacion banco central tasas interes"])
    assert pred[0] == "economia"
