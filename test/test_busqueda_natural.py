from src.busqueda_natural import BusquedaNatural
from src.motor_busqueda import MotorBusqueda


def construir_busqueda():
    noticias = [
        {
            "titulo": "Python mejora la programacion",
            "cuerpo": "La tecnologia avanza con nuevas herramientas.",
            "categoria_predicha": "tecnologia",
            "sentimiento": {"etiqueta": "positivo"},
        },
        {
            "titulo": "Mercados financieros caen",
            "cuerpo": "La economia muestra volatilidad preocupante.",
            "categoria_predicha": "economia",
            "sentimiento": {"etiqueta": "negativo"},
        },
        {
            "titulo": "Cambio climatico preocupa",
            "cuerpo": "Investigacion cientifica alerta sobre el clima.",
            "categoria_predicha": "ciencia",
            "sentimiento": {"etiqueta": "negativo"},
        },
    ]
    motor = MotorBusqueda()
    motor.indexar(noticias)
    return BusquedaNatural(motor)


def test_busqueda_natural_interpreta_filtros():
    busqueda = construir_busqueda()

    filtros = busqueda.interpretar_consulta("Muestrame noticias positivas de tecnologia")

    assert filtros == {"sentimiento": "positivo", "categoria": "tecnologia"}


def test_busqueda_natural_filtra_por_categoria_y_sentimiento():
    busqueda = construir_busqueda()

    resultados = busqueda.buscar_natural("noticias positivas de programacion Python", top_k=2)

    assert resultados[0]["doc_id"] == 0
    assert resultados[0]["categoria"] == "tecnologia"
    assert resultados[0]["sentimiento"] == "positivo"


def test_busqueda_natural_devuelve_resultados_sin_filtro_si_no_hay_filtrados():
    busqueda = construir_busqueda()

    resultados = busqueda.buscar_natural("noticias sobre mercados financieros", top_k=1)

    assert len(resultados) == 1
    assert resultados[0]["doc_id"] == 1


def test_busqueda_natural_respeta_filtros_con_fallback():
    busqueda = construir_busqueda()

    resultados = busqueda.buscar_natural("Muestrame noticias positivas sobre tecnologia", top_k=1)

    assert resultados[0]["doc_id"] == 0
    assert resultados[0]["categoria"] == "tecnologia"
    assert resultados[0]["sentimiento"] == "positivo"
