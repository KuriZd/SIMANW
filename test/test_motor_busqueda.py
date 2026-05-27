import pytest

from src.motor_busqueda import MotorBusqueda


def noticias_demo():
    return [
        {
            "titulo": "Inteligencia artificial en tecnologia",
            "cuerpo": "La IA transforma procesos digitales.",
            "fecha": "2026-05-10",
            "url": "https://demo.test/ia",
            "categoria_predicha": "tecnologia",
            "sentimiento": {"etiqueta": "positivo"},
        },
        {
            "titulo": "Mercados financieros y economia",
            "cuerpo": "La bolsa registra volatilidad.",
            "categoria_predicha": "economia",
            "sentimiento": {"etiqueta": "negativo"},
        },
        {
            "titulo": "Cambio climatico",
            "cuerpo": "Investigadores publican un estudio cientifico.",
            "categoria_predicha": "ciencia",
            "sentimiento": {"etiqueta": "neutral"},
        },
    ]


def test_motor_busqueda_indexa_documentos():
    motor = MotorBusqueda()
    motor.indexar(noticias_demo())

    info = motor.info_indice()

    assert info["documentos_indexados"] == 3
    assert info["terminos_en_indice"] > 0
    assert "tecnologia" in motor.indice_invertido


def test_motor_busqueda_booleana_and_y_or():
    motor = MotorBusqueda()
    motor.indexar(noticias_demo())

    assert motor.buscar_booleana("mercados economia", modo="AND") == [1]
    assert motor.buscar_booleana("tecnologia economia", modo="OR") == [0, 1]


def test_motor_busqueda_vectorial_devuelve_metadata():
    motor = MotorBusqueda()
    motor.indexar(noticias_demo())

    resultados = motor.buscar_vectorial("inteligencia artificial", top_k=2)

    assert resultados[0]["doc_id"] == 0
    assert resultados[0]["categoria"] == "tecnologia"
    assert resultados[0]["sentimiento"] == "positivo"
    assert resultados[0]["relevancia"] > 0
    assert resultados[0]["score"] == resultados[0]["relevancia"]
    assert resultados[0]["fecha"] == "2026-05-10"
    assert resultados[0]["url"] == "https://demo.test/ia"
    assert resultados[0]["snippet"]


def test_motor_busqueda_requiere_documentos():
    motor = MotorBusqueda()

    with pytest.raises(ValueError):
        motor.indexar([])
