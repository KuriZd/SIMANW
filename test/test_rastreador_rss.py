from src.rastreador_rss import RastreadorRSS


def test_rss_infiere_categoria_desde_url_editorial():
    assert (
        RastreadorRSS._categoria_desde_url(
            "https://www.jornada.com.mx/2026/05/28/politica/005n2pol?partner=rss"
        )
        == "politica"
    )


def test_rss_no_confunde_fuente_con_categoria_si_no_hay_segmento_editorial():
    assert RastreadorRSS._categoria_desde_url("https://www.jornada.com.mx/rss/edicion.xml") == ""
