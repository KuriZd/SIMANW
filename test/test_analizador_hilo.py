import pytest

from src.analizador_hilo import HILO_IA_DEMO, AnalizadorHiloDiscusion


def test_analizador_hilo_carga_y_resume_discusion():
    analizador = AnalizadorHiloDiscusion()
    analizador.cargar_hilo(HILO_IA_DEMO)

    resumen = analizador.resumen_hilo()

    assert resumen["total_mensajes"] == 12
    assert resumen["participantes"] == 5
    assert resumen["tono"] in {"positivo", "negativo", "mixto"}
    assert resumen["hashtags_top"][0][0] == "AI"
    assert resumen["usuarios_activos"][0] == ("@dev_laura", 3)


def test_analizador_hilo_evolucion_sentimiento():
    analizador = AnalizadorHiloDiscusion()
    analizador.cargar_hilo(HILO_IA_DEMO)

    evolucion = analizador.evolucion_sentimiento(ventana=3)

    assert len(evolucion) == len(HILO_IA_DEMO)
    assert evolucion[0]["posicion"] == 1
    assert "sentimiento_puntual" in evolucion[0]
    assert "tendencia" in evolucion[0]


def test_analizador_hilo_detecta_subtemas():
    analizador = AnalizadorHiloDiscusion()
    analizador.cargar_hilo(HILO_IA_DEMO)

    subtemas = analizador.detectar_subtemas(n_clusters=3)

    assert 1 <= len(subtemas) <= 3
    assert sum(info["n_mensajes"] for info in subtemas.values()) == len(HILO_IA_DEMO)
    assert all("keywords" in info for info in subtemas.values())


def test_analizador_hilo_maneja_hilo_vacio_y_valida_ventana():
    analizador = AnalizadorHiloDiscusion()

    assert analizador.resumen_hilo()["total_mensajes"] == 0
    assert analizador.detectar_subtemas() == {}

    with pytest.raises(ValueError):
        analizador.evolucion_sentimiento(ventana=0)
