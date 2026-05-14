from src.detector_publicidad import DetectorTemasPublicidad


def test_detector_publicidad_sin_mensajes_devuelve_general():
    detector = DetectorTemasPublicidad()

    tema, confianza = detector.detectar_tema()

    assert tema == "general"
    assert confianza == 0.0


def test_detector_publicidad_detecta_tema_tecnologia():
    detector = DetectorTemasPublicidad()
    detector.agregar_mensaje("Laura", "La inteligencia artificial ayuda a programar software")

    tema, confianza = detector.detectar_tema()

    assert tema == "tecnologia"
    assert confianza > 0


def test_detector_publicidad_simula_chat_con_anuncios():
    detector = DetectorTemasPublicidad()
    conversacion = [
        ("Miguel", "Los mercados y las inversiones estan cambiando"),
        ("Laura", "El banco subio tasas de interes"),
    ]

    resultados = detector.simular_chat(conversacion)

    assert len(resultados) == 2
    assert resultados[-1]["tema"] == "economia"
    assert "publicidad" in resultados[-1]
