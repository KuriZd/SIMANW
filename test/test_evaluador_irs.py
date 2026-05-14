import pytest

from src.evaluador_irs import EvaluadorIRS


def test_evaluador_irs_metricas_basicas():
    evaluador = EvaluadorIRS()

    precision = evaluador.precision([1, 2, 3], [1, 3])
    recall = evaluador.recall([1, 2, 3], [1, 3])
    f1 = evaluador.f1(precision, recall)

    assert precision == pytest.approx(2 / 3)
    assert recall == pytest.approx(1.0)
    assert f1 == pytest.approx(0.8)


def test_evaluador_irs_precision_at_k_y_average_precision():
    evaluador = EvaluadorIRS()
    ranking = [0, 3, 1, 2, 4]
    relevantes = [0, 3]

    assert evaluador.precision_at_k(ranking, relevantes, 1) == pytest.approx(1.0)
    assert evaluador.precision_at_k(ranking, relevantes, 3) == pytest.approx(2 / 3)
    assert evaluador.average_precision(ranking, relevantes) == pytest.approx(1.0)


def test_evaluador_irs_consulta_completa_y_map():
    evaluador = EvaluadorIRS()
    evaluaciones = [
        {"recuperados": [0, 1], "relevantes": [0]},
        {"recuperados": [2, 3], "relevantes": [3]},
    ]

    metricas = evaluador.evaluar_consulta([0, 1], [0], total_docs=4)

    assert metricas["precision"] == pytest.approx(0.5)
    assert metricas["recall"] == pytest.approx(1.0)
    assert evaluador.mean_average_precision(evaluaciones) == pytest.approx(0.75)
