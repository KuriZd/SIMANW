import json

import pytest

from src.rastreador_paginado import RastreadorPaginado, crear_fetcher_simulado


def test_rastreador_extrae_paginacion_y_minimo_noticias():
    rastreador = RastreadorPaginado(
        url_base="https://ejemplo.test/noticias?page=1",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=0,
        max_paginas=4,
        fetcher=crear_fetcher_simulado(noticias_por_pagina=5, total_paginas=4),
        respetar_robots=False,
    )

    resultados = rastreador.rastrear(minimo_noticias=20)

    assert len(resultados) == 20
    assert len(rastreador.paginas_visitadas) == 4
    assert resultados[0]["titulo"] == "Noticia real simulada 1"
    assert resultados[-1]["titulo"] == "Noticia real simulada 20"
    assert resultados[0]["url"] == "https://ejemplo.test/noticia/1"


def test_rastreador_guarda_json(tmp_path):
    rastreador = RastreadorPaginado(
        url_base="https://ejemplo.test/noticias?page=1",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=0,
        max_paginas=1,
        fetcher=crear_fetcher_simulado(noticias_por_pagina=2, total_paginas=1),
        respetar_robots=False,
    )
    rastreador.rastrear()

    ruta = tmp_path / "noticias.json"
    total = rastreador.guardar_json(ruta)
    datos = json.loads(ruta.read_text(encoding="utf-8"))

    assert total == 2
    assert len(datos) == 2
    assert datos[1]["titulo"] == "Noticia real simulada 2"


def test_rastreador_real_requiere_delay_minimo():
    with pytest.raises(ValueError):
        RastreadorPaginado(
            url_base="https://ejemplo.test/noticias",
            selector_articulos="article",
            selector_siguiente="a.next-page",
            delay=1,
        )


def test_rastreador_respeta_robots_bloqueado():
    rastreador = RastreadorPaginado(
        url_base="https://ejemplo.test/noticias",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=0,
        fetcher=crear_fetcher_simulado(),
        respetar_robots=True,
    )

    class RobotsBloqueado:
        def can_fetch(self, user_agent, url):
            return False

    rastreador._robots = RobotsBloqueado()

    assert rastreador.rastrear() == []
