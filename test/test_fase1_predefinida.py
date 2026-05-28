"""Tests de Fase1Service para el modo de fuentes predefinidas."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from src.fase1_service import Fase1Service


_NOTICIA_MUESTRA = {
    "titulo": "Noticia de prueba",
    "cuerpo": "Texto del cuerpo de la noticia de prueba para tests unitarios.",
    "fecha": "2024-01-15",
    "autor": "Redacción de prueba",
    "categoria": "Mexico",
    "url": "https://editorial.aristeguinoticias.com/noticia-de-prueba",
}


@pytest.fixture
def rss_mock():
    """Instancia falsa de RastreadorRSS que devuelve una noticia sin red."""
    m = MagicMock()
    m.extraer.return_value = [_NOTICIA_MUESTRA]
    m.errores = []
    return m


def test_ejecutar_fuente_predefinida_rss_devuelve_noticias_normalizadas(rss_mock):
    with patch("src.fase1_service.RastreadorRSS", return_value=rss_mock):
        service = Fase1Service()
        noticias = service.ejecutar_fuente_predefinida("aristegui_noticias")

    assert len(noticias) >= 1
    for campo in ("titulo", "cuerpo", "fecha", "autor", "categoria", "url"):
        assert campo in noticias[0], f"Campo '{campo}' ausente en la noticia normalizada"


def test_metadata_fuente_preservada_en_noticias_normalizadas(rss_mock):
    with patch("src.fase1_service.RastreadorRSS", return_value=rss_mock):
        service = Fase1Service()
        noticias = service.ejecutar_fuente_predefinida("aristegui_noticias")

    n = noticias[0]
    assert n["fuente_nombre"] == "Aristegui Noticias"
    assert n["fuente_id"] == "aristegui_noticias"
    assert n["fuente_tipo"] == "rss"
    assert n["categoria"] != "aristegui_noticias"


def test_ejecutar_fuente_predefinida_id_invalido_lanza_key_error():
    service = Fase1Service()
    with pytest.raises(KeyError):
        service.ejecutar_fuente_predefinida("fuente_inexistente_xyz")


def test_ejecutar_via_modo_predefinida_usa_fuente_correcta(rss_mock):
    """ejecutar('predefinida', fuente_id) es alias de ejecutar_fuente_predefinida."""
    with patch("src.fase1_service.RastreadorRSS", return_value=rss_mock):
        service = Fase1Service()
        resultado = service.ejecutar("predefinida", "la_jornada")

    assert resultado.fuente == "predefinida"
    assert len(resultado.noticias) >= 1
    assert resultado.noticias[0]["fuente_nombre"] == "La Jornada"
    assert resultado.noticias[0]["fuente_id"] == "la_jornada"


def test_ejecutar_fuente_predefinida_respeta_limite_noticias(rss_mock):
    """El número de noticias no supera limite_noticias de la fuente."""
    with patch("src.fase1_service.RastreadorRSS", return_value=rss_mock):
        service = Fase1Service()
        noticias = service.ejecutar_fuente_predefinida("aristegui_noticias")

    fuente = service.fuentes_service.obtener_fuente("aristegui_noticias")
    assert len(noticias) <= fuente["limite_noticias"]


def test_rss_predefinido_no_usa_id_de_fuente_como_categoria(rss_mock):
    with patch("src.fase1_service.RastreadorRSS", return_value=rss_mock) as cls:
        service = Fase1Service()
        service.ejecutar_fuente_predefinida("la_jornada")

    assert cls.call_args.kwargs["categoria_default"] == "sin_categoria"


def test_normalizar_noticia_sin_fuente_no_incluye_metadata():
    """_normalizar_noticia sin fuente no agrega fuente_nombre ni fuente_id."""
    noticia = _NOTICIA_MUESTRA.copy()
    resultado = Fase1Service._normalizar_noticia(noticia, 1)

    assert "fuente_nombre" not in resultado
    assert "fuente_id" not in resultado
    assert "fuente_tipo" not in resultado


def test_normalizar_noticia_con_fuente_incluye_metadata():
    """_normalizar_noticia con fuente agrega los tres campos de metadata."""
    fuente = {"nombre": "Test Source", "id": "test_src", "tipo": "rss"}
    noticia = _NOTICIA_MUESTRA.copy()
    resultado = Fase1Service._normalizar_noticia(noticia, 1, fuente)

    assert resultado["fuente_nombre"] == "Test Source"
    assert resultado["fuente_id"] == "test_src"
    assert resultado["fuente_tipo"] == "rss"
