import pytest

from src.fuentes_service import FuentesService


def test_listar_fuentes_activas_incluye_catalogo_inicial():
    service = FuentesService()

    fuentes = service.listar_fuentes()
    nombres = {fuente["nombre"] for fuente in fuentes}

    assert len(fuentes) >= 5
    assert "La Jornada" in nombres
    assert "Aristegui Noticias" in nombres
    assert all(fuente["activo"] is True for fuente in fuentes)


def test_obtener_fuente_por_id():
    service = FuentesService()

    fuente = service.obtener_fuente("aristegui_noticias")

    assert fuente["nombre"] == "Aristegui Noticias"
    assert fuente["tipo"] == "rss"
    assert "https://editorial.aristeguinoticias.com/feed/" in fuente["urls"]


def test_validar_fuente_detecta_campos_requeridos():
    service = FuentesService()

    valida, errores = service.validar_fuente({"id": "incompleta"})

    assert valida is False
    assert any("Campo requerido ausente" in error for error in errores)


def test_obtener_fuente_inexistente_lanza_key_error():
    service = FuentesService()

    with pytest.raises(KeyError):
        service.obtener_fuente("no_existe")


def test_listar_nombres_fuentes_devuelve_lista_de_strings():
    service = FuentesService()

    nombres = service.listar_nombres_fuentes()

    assert isinstance(nombres, list)
    assert all(isinstance(n, str) for n in nombres)
    assert "La Jornada" in nombres
    assert "Aristegui Noticias" in nombres


def test_obtener_por_nombre_encuentra_fuente_existente():
    service = FuentesService()

    fuente = service.obtener_por_nombre("Aristegui Noticias")

    assert fuente["id"] == "aristegui_noticias"
    assert fuente["tipo"] == "rss"
    assert fuente["activo"] is True


def test_obtener_por_nombre_inexistente_lanza_key_error():
    service = FuentesService()

    with pytest.raises(KeyError):
        service.obtener_por_nombre("Fuente Que No Existe")


def test_validar_fuente_tipo_invalido_reporta_error():
    service = FuentesService()
    fuente_invalida = {
        "id": "test", "nombre": "Test", "tipo": "ftp",
        "pais": "MX", "idioma": "es", "base_url": "https://test.com",
        "urls": ["https://test.com/rss"], "dominios_permitidos": ["test.com"],
        "activo": True, "limite_noticias": 10, "delay_segundos": 1,
        "requiere_parser_html": False, "notas": "",
    }

    valida, errores = service.validar_fuente(fuente_invalida)

    assert valida is False
    assert any("tipo" in e for e in errores)


def test_obtener_urls_devuelve_lista_con_https():
    service = FuentesService()

    urls = service.obtener_urls("la_jornada")

    assert isinstance(urls, list)
    assert len(urls) >= 1
    assert all(u.startswith("https://") for u in urls)


def test_fuente_inegi_es_tipo_html():
    service = FuentesService()

    fuente = service.obtener_fuente("inegi_sala_prensa")

    assert fuente["tipo"] == "html"
    assert fuente["requiere_parser_html"] is True


def test_listar_fuentes_todas_incluye_inactivas():
    fuentes_con_inactiva = [
        {
            "id": "inactiva", "nombre": "Fuente Inactiva", "tipo": "rss",
            "pais": "MX", "idioma": "es", "base_url": "https://inactiva.com",
            "urls": ["https://inactiva.com/rss"], "dominios_permitidos": ["inactiva.com"],
            "activo": False, "limite_noticias": 10, "delay_segundos": 1,
            "requiere_parser_html": False, "notas": "",
        }
    ]
    service = FuentesService(fuentes=fuentes_con_inactiva)

    activas = service.listar_fuentes(activas=True)
    todas   = service.listar_fuentes(activas=False)

    assert len(activas) == 0
    assert len(todas) == 1


def test_guardar_fuente_personalizada_agrega_fuente_valida(tmp_path):
    ruta_catalogo = tmp_path / "fuentes_noticias.py"
    service = FuentesService(fuentes=[], ruta_catalogo=ruta_catalogo)

    fuente = service.guardar_fuente_personalizada(
        "https://example.com/rss.xml",
        tipo="rss",
        nombre="Example RSS",
    )

    assert fuente["id"] == "example_rss"
    assert fuente["nombre"] == "Example RSS"
    assert fuente["tipo"] == "rss"
    assert fuente["urls"] == ["https://example.com/rss.xml"]
    assert fuente["activo"] is True
    assert service.obtener_fuente("example_rss")["nombre"] == "Example RSS"
    assert "FUENTES_NOTICIAS" in ruta_catalogo.read_text(encoding="utf-8")


def test_guardar_fuente_personalizada_no_duplica_url(tmp_path):
    ruta_catalogo = tmp_path / "fuentes_noticias.py"
    service = FuentesService(fuentes=[], ruta_catalogo=ruta_catalogo)

    primera = service.guardar_fuente_personalizada("https://example.com/feed", nombre="Example")
    segunda = service.guardar_fuente_personalizada("https://example.com/feed", nombre="Duplicada")

    assert segunda["id"] == primera["id"]
    assert len(service.listar_fuentes()) == 1
