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


def test_detector_publicidad_umbral_bajo_devuelve_general_y_resumen_etico():
    detector = DetectorTemasPublicidad(umbral_confianza=0.5)
    resultados = detector.simular_chat([("Ana", "comentario breve sin tema claro")])

    assert resultados[0]["tema"] == "general"
    resumen = detector.resumen_temas()
    assert resumen["temas"] == {"general": 1}
    assert "consentimiento" in resumen["nota_etica"]
