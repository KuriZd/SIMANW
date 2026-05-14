from src.control_rastreo import ControlRastreo


def test_control_rastreo_acepta_urls_del_directorio():
    control = ControlRastreo(
        "https://portal-noticias.com/noticias/",
        modo="directorio",
        max_paginas=10,
    )

    assert control.url_permitida("https://portal-noticias.com/noticias/tecnologia/ia")


def test_control_rastreo_rechaza_otro_directorio():
    control = ControlRastreo(
        "https://portal-noticias.com/noticias/",
        modo="directorio",
        max_paginas=10,
    )

    assert not control.url_permitida("https://portal-noticias.com/deportes/futbol")


def test_control_rastreo_rechaza_directorio_con_prefijo_similar():
    control = ControlRastreo(
        "https://portal-noticias.com/noticias/",
        modo="directorio",
        max_paginas=10,
    )

    assert not control.url_permitida("https://portal-noticias.com/noticias-extra/articulo")


def test_control_rastreo_rechaza_otro_dominio():
    control = ControlRastreo(
        "https://portal-noticias.com/noticias/",
        modo="directorio",
        max_paginas=10,
    )

    assert not control.url_permitida("https://otro-sitio.com/articulo")


def test_control_rastreo_agrega_solo_enlaces_validos():
    control = ControlRastreo(
        "https://portal-noticias.com/noticias/",
        modo="directorio",
        max_paginas=10,
    )

    enlaces = [
        "/noticias/pagina/2",
        "/noticias/tecnologia/ia-2026",
        "/deportes/futbol-liga",
        "https://otro-sitio.com/articulo",
        "/noticias/economia/mercados",
    ]

    agregados = control.agregar_enlaces(enlaces)

    assert agregados == 3
    assert len(control.rechazadas) == 2


def test_control_rastreo_subdominio_acepta_subdominios_del_portal():
    control = ControlRastreo(
        "https://portal-noticias.com/noticias/",
        modo="subdominio",
        max_paginas=10,
    )

    assert control.url_permitida("https://archivo.portal-noticias.com/noticias/ia")


def test_control_rastreo_subdominio_rechaza_otros_dominios_com():
    control = ControlRastreo(
        "https://portal-noticias.com/noticias/",
        modo="subdominio",
        max_paginas=10,
    )

    assert not control.url_permitida("https://otro-sitio.com/noticias/ia")
