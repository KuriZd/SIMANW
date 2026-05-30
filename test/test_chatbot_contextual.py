from src.chatbot_contextual import ChatbotContextual
from src.fase5_service import Fase5Service
from src.motor_busqueda import MotorBusqueda


def noticias_demo():
    return [
        {
            "titulo": "Inteligencia artificial generativa",
            "cuerpo": "La inteligencia artificial transforma software y programacion.",
            "categoria_predicha": "tecnologia",
            "sentimiento": {"etiqueta": "positivo"},
        },
        {
            "titulo": "Mercados financieros",
            "cuerpo": "La economia enfrenta volatilidad en mercado de valores.",
            "categoria_predicha": "economia",
            "sentimiento": {"etiqueta": "negativo"},
        },
        {
            "titulo": "Python para inteligencia artificial",
            "cuerpo": "Python ayuda a crear aplicaciones de machine learning.",
            "categoria_predicha": "tecnologia",
            "sentimiento": {"etiqueta": "positivo"},
        },
    ]


def motor_demo():
    motor = MotorBusqueda()
    motor.indexar(noticias_demo())
    return motor


def test_chatbot_contextual_responde_y_actualiza_contexto():
    chatbot = ChatbotContextual(noticias_demo(), motor_demo())

    respuesta, tipo, confianza = chatbot.responder("Que noticias hay de tecnologia?")

    assert tipo == "personalizada"
    assert confianza > 0
    assert "tecnologia" in chatbot.contexto_temas
    assert len(chatbot.historial) == 1
    assert respuesta


def test_chatbot_contextual_usa_referencia_anterior():
    chatbot = ChatbotContextual(noticias_demo(), motor_demo())
    chatbot.responder("Que noticias hay de tecnologia?")

    respuesta, tipo, confianza = chatbot.responder("Cuentame mas sobre eso")

    assert tipo == "contextual"
    assert "conversacion anterior" in respuesta
    assert confianza > 0
    assert len(chatbot.historial) == 2


def test_chatbot_contextual_personaliza_por_tema_favorito():
    chatbot = ChatbotContextual(noticias_demo(), motor_demo())
    chatbot.responder("Que noticias hay de tecnologia?")

    respuesta, tipo, confianza = chatbot.responder("inteligencia artificial economia")

    assert tipo == "personalizada"
    assert "Como te interesa economia" in respuesta
    assert confianza > 0


def test_chatbot_contextual_estadisticas_sesion_y_fallback():
    chatbot = ChatbotContextual(noticias_demo(), motor_demo())

    respuesta, tipo, confianza = chatbot.responder("astronomia galaxias telescopio")
    stats = chatbot.estadisticas_sesion()

    assert tipo == "fallback"
    assert confianza == 0.0
    assert "No encontre" in respuesta
    assert stats["interacciones"] == 1
    assert stats["tipos_respuesta"]["fallback"] == 1


def test_fase5_service_usa_chatbot_contextual_con_motor_real():
    service = Fase5Service()
    service.preparar(noticias_demo(), motor_demo())

    primera = service.responder("Que noticias hay de tecnologia?")
    segunda = service.responder("Cuentame mas sobre eso")
    historial = service.obtener_historial()
    stats = service.estadisticas_contexto()

    assert primera
    assert "conversacion anterior" in segunda
    assert historial[-1]["tipo"] == "contextual"
    assert historial[-1]["usa_contexto"] is True
    assert stats["ultima_consulta_expandida"]
