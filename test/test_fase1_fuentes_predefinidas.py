from src import fase1_service as fase1_module
from src.fase1_service import Fase1Service
from src.fuentes_service import FuentesService


class RastreadorRSSFake:
    llamadas: list[str] = []

    def __init__(self, url: str, categoria_default: str = "", max_noticias: int = 20, **_kwargs):
        self.url = url
        self.categoria_default = categoria_default
        self.max_noticias = max_noticias
        self.errores: list[str] = []
        self.__class__.llamadas.append(url)

    def extraer(self) -> list[dict]:
        return [
            {
                "titulo": f"Titulo desde {self.url}",
                "cuerpo": "Cuerpo de prueba para una noticia RSS predefinida.",
                "fecha": "2026-05-27T10:00:00",
                "autor": "Redaccion",
                "categoria_original": self.categoria_default,
                "url": f"{self.url.rstrip('/')}/nota-prueba",
            }
        ]


def test_ejecutar_fuente_predefinida_rss_usa_urls_configuradas(monkeypatch):
    RastreadorRSSFake.llamadas = []
    monkeypatch.setattr(fase1_module, "RastreadorRSS", RastreadorRSSFake)
    service = Fase1Service()

    noticias = service.ejecutar_fuente_predefinida("aristegui_noticias")

    assert noticias
    assert len(RastreadorRSSFake.llamadas) == 3
    assert "https://editorial.aristeguinoticias.com/feed/" in RastreadorRSSFake.llamadas


def test_ejecutar_fuente_predefinida_preserva_metadatos(monkeypatch):
    RastreadorRSSFake.llamadas = []
    monkeypatch.setattr(fase1_module, "RastreadorRSS", RastreadorRSSFake)
    service = Fase1Service()

    noticia = service.ejecutar_fuente_predefinida("aristegui_noticias")[0]

    assert noticia["fuente_nombre"] == "Aristegui Noticias"
    assert noticia["fuente_id"] == "aristegui_noticias"
    assert noticia["fuente_tipo"] == "rss"
    assert {"titulo", "cuerpo", "fecha", "autor", "categoria", "url"} <= set(noticia)


def test_ejecutar_todas_fuentes_activas_agrega_metadata(monkeypatch):
    RastreadorRSSFake.llamadas = []
    monkeypatch.setattr(fase1_module, "RastreadorRSS", RastreadorRSSFake)
    service = Fase1Service()
    service.fuentes_service = FuentesService(
        [
            {
                "id": "fuente_uno",
                "nombre": "Fuente Uno",
                "tipo": "rss",
                "pais": "MX",
                "idioma": "es",
                "base_url": "https://uno.test",
                "urls": ["https://uno.test/feed"],
                "dominios_permitidos": ["uno.test"],
                "activo": True,
                "limite_noticias": 1,
                "delay_segundos": 0,
                "requiere_parser_html": False,
                "notas": "",
            },
            {
                "id": "fuente_dos",
                "nombre": "Fuente Dos",
                "tipo": "rss",
                "pais": "MX",
                "idioma": "es",
                "base_url": "https://dos.test",
                "urls": ["https://dos.test/feed"],
                "dominios_permitidos": ["dos.test"],
                "activo": True,
                "limite_noticias": 1,
                "delay_segundos": 0,
                "requiere_parser_html": False,
                "notas": "",
            },
        ]
    )

    noticias = service.ejecutar_todas_fuentes(limite_noticias=1)

    fuentes = {noticia["fuente_id"] for noticia in noticias}
    assert fuentes == {"fuente_uno", "fuente_dos"}
    assert all(noticia["fuente_nombre"] for noticia in noticias)
