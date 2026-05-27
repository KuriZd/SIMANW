import pytest

from src.usabilidad import CUESTIONARIO_USABILIDAD, EstudioUsabilidad, estudio_demo


def test_estudio_demo_tiene_tres_participantes_y_cinco_tareas():
    estudio = estudio_demo()

    assert len(estudio.participantes) == 3
    assert len(estudio.tareas) == 5


def test_promedios_por_item_del_cuestionario():
    estudio = estudio_demo()
    promedios = estudio.promedios()

    assert set(promedios) == set(CUESTIONARIO_USABILIDAD)
    assert promedios["Rapidez percibida"] == pytest.approx(4.33, abs=0.01)


def test_exporta_tabla_anonimizada(tmp_path):
    estudio = estudio_demo()
    ruta = estudio.exportar_csv(tmp_path / "usabilidad.csv")

    contenido = ruta.read_text(encoding="utf-8")
    assert "participante" in contenido
    assert "P1" in contenido


def test_problemas_y_mejoras_contiene_cinco_items():
    estudio = estudio_demo()

    items = estudio.problemas_y_mejoras()

    assert len(items) == 5
    assert all(item["problema"] and item["mejora"] for item in items)


def test_rechaza_cuestionario_incompleto():
    estudio = EstudioUsabilidad()

    with pytest.raises(ValueError):
        estudio.registrar_participante("P0", {"Facilidad para completar las tareas": 5}, [])
