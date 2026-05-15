import pytest

from src.chatbot_qa import ChatbotSIMANW, SistemaQA
from src.motor_busqueda import MotorBusqueda


def noticias_demo():
    return [
        {
            "titulo": "Inteligencia artificial en tecnologia",
            "cuerpo": "La IA transforma procesos digitales y mejora la productividad.",
            "categoria_predicha": "tecnologia",
            "sentimiento": {"etiqueta": "positivo", "compound": 0.7},
        },
        {
            "titulo": "Mercados financieros y economia",
            "cuerpo": "La bolsa registra volatilidad y caidas por incertidumbre.",
            "categoria_predicha": "economia",
            "sentimiento": {"etiqueta": "negativo", "compound": -0.6},
        },
        {
            "titulo": "Datos abiertos del gobierno",
            "cuerpo": "El portal publico libera conjuntos de datos para investigacion.",
            "categoria_predicha": "politica",
            "sentimiento": {"etiqueta": "neutral", "compound": 0.0},
        },
    ]


def motor_demo():
    motor = MotorBusqueda()
    motor.indexar(noticias_demo())
    return motor


def test_chatbot_responde_por_similitud():
    chatbot = ChatbotSIMANW(noticias_demo())

    respuesta, confianza = chatbot.responder("Que hay sobre inteligencia artificial?")

    assert "Inteligencia artificial" in respuesta
    assert confianza > 0
    assert chatbot.resumen_interaccion().startswith("1 preguntas")


def test_chatbot_respeta_umbral_sin_informacion():
    chatbot = ChatbotSIMANW(noticias_demo())

    respuesta, confianza = chatbot.responder("astronomia galactica telescopios", umbral=0.8)

    assert "No tengo informacion suficiente" in respuesta
    assert confianza == 0.0


def test_chatbot_requiere_noticias():
    with pytest.raises(ValueError):
        ChatbotSIMANW([])


def test_sistema_qa_clasifica_intenciones():
    qa = SistemaQA(noticias_demo(), motor_demo())

    assert qa.clasificar_intencion("Cuantas noticias tienes?") == "conteo"
    assert qa.clasificar_intencion("Dame un resumen") == "resumen"
    assert qa.clasificar_intencion("Cual es el tono?") == "sentimiento"
    assert qa.clasificar_intencion("Que categorias hay?") == "categoria"
    assert qa.clasificar_intencion("Recomiendame tecnologia") == "recomendacion"


def test_sistema_qa_responde_conteo_y_sentimiento():
    qa = SistemaQA(noticias_demo(), motor_demo())

    respuesta_conteo, tipo_conteo, confianza_conteo = qa.conversar("Cuantas noticias tienes?")
    respuesta_sentimiento, tipo_sentimiento, confianza_sentimiento = qa.conversar("Sentimiento general")

    assert tipo_conteo == "conteo"
    assert "Tengo 3 noticias indexadas" in respuesta_conteo
    assert confianza_conteo == 1.0
    assert tipo_sentimiento == "sentimiento"
    assert "Analisis de sentimiento" in respuesta_sentimiento
    assert confianza_sentimiento == 0.9
    assert len(qa.historial_conversacion) == 2


def test_sistema_qa_busqueda_y_recomendacion():
    qa = SistemaQA(noticias_demo(), motor_demo())

    respuesta_busqueda, tipo_busqueda, confianza_busqueda = qa.conversar("Que dice la noticia sobre datos abiertos?")
    respuesta_recomendacion, tipo_recomendacion, confianza_recomendacion = qa.conversar(
        "Recomiendame algo sobre tecnologia"
    )

    assert tipo_busqueda == "busqueda"
    assert "Datos abiertos" in respuesta_busqueda
    assert confianza_busqueda > 0
    assert tipo_recomendacion == "recomendacion"
    assert "Te recomiendo" in respuesta_recomendacion
    assert confianza_recomendacion > 0
