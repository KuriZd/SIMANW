from src.extractor import ExtractorNoticias
from src.html_demo import html_portal_noticias


def test_extractor_extrae_5_noticias():
    extractor = ExtractorNoticias()
    noticias = extractor.extraer_de_html(html_portal_noticias)

    assert len(noticias) == 5


def test_extractor_no_genera_errores():
    extractor = ExtractorNoticias()
    extractor.extraer_de_html(html_portal_noticias)

    resumen = extractor.resumen_extraccion()

    assert resumen["errores"] == 0


def test_extractor_contiene_campos_obligatorios():
    extractor = ExtractorNoticias()
    noticias = extractor.extraer_de_html(html_portal_noticias)

    noticia = noticias[0]

    assert "titulo" in noticia
    assert "cuerpo" in noticia
    assert "fecha" in noticia
    assert "autor" in noticia
    assert "categoria_original" in noticia
    assert "url" in noticia
    assert "fuente" in noticia


def test_extractor_detecta_categorias():
    extractor = ExtractorNoticias()
    extractor.extraer_de_html(html_portal_noticias)

    resumen = extractor.resumen_extraccion()

    assert "tecnologia" in resumen["categorias"]
    assert "economia" in resumen["categorias"]
    assert "ciencia" in resumen["categorias"]
    assert "gobierno" in resumen["categorias"]