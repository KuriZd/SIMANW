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


def test_rastreador_real_aplica_delay_minimo(monkeypatch):
    pausas = []
    monkeypatch.setattr("src.rastreador_paginado.time.sleep", lambda segundos: pausas.append(segundos))

    rastreador = RastreadorPaginado(
        url_base="https://ejemplo.test/noticias",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=3,
        respetar_robots=True,
    )

    rastreador._esperar()

    assert pausas == [3]


def test_rastreador_trunca_max_noticias():
    rastreador = RastreadorPaginado(
        url_base="https://ejemplo.test/noticias?page=1",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=0,
        max_paginas=4,
        max_noticias=7,
        fetcher=crear_fetcher_simulado(noticias_por_pagina=5, total_paginas=4),
        respetar_robots=False,
    )

    resultados = rastreador.rastrear()

    assert len(resultados) == 7
    assert resultados[-1]["titulo"] == "Noticia real simulada 7"


def test_rastreador_reporta_diagnostico_cuando_selector_no_coincide():
    def fetcher(_url):
        return "<main><section class='item'><h2>Noticia</h2></section></main>"

    rastreador = RastreadorPaginado(
        url_base="https://ejemplo.test/noticias",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=0,
        fetcher=fetcher,
        respetar_robots=False,
    )

    resultados = rastreador.rastrear()

    assert resultados == []
    assert rastreador.diagnostico_paginas[0]["articulos_detectados"] == 0
    assert "selector de articulos" in rastreador.errores[0]


def test_rastreador_reporta_diagnostico_cuando_falta_titulo():
    def fetcher(_url):
        return "<main><article><a href='/n/1'>Leer mas</a><p>Resumen</p></article></main>"

    rastreador = RastreadorPaginado(
        url_base="https://ejemplo.test/noticias",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        selector_titulo=".titulo",
        delay=0,
        fetcher=fetcher,
        respetar_robots=False,
    )

    resultados = rastreador.rastrear()

    assert resultados == []
    assert rastreador.diagnostico_paginas[0]["articulos_detectados"] == 1
    assert rastreador.diagnostico_paginas[0]["omitidas_sin_titulo"] == 1
    assert "selector de titulo" in rastreador.errores[0]


def test_rastreador_fallback_extrae_enlaces_largos_si_no_hay_articulos():
    def fetcher(_url):
        return """
        <main>
          <a href="/noticias/uno">NASA Develops Sensor to Improve Firefighter Safety</a>
          <a href="/about">About</a>
        </main>
        """

    rastreador = RastreadorPaginado(
        url_base="https://www.nasa.gov/news/recently-published/",
        selector_articulos="article",
        selector_siguiente="a.next-page",
        delay=0,
        fetcher=fetcher,
        respetar_robots=False,
    )

    resultados = rastreador.rastrear()

    assert len(resultados) == 1
    assert resultados[0]["titulo"] == "NASA Develops Sensor to Improve Firefighter Safety"
    assert resultados[0]["url"] == "https://www.nasa.gov/noticias/uno"
    assert rastreador.diagnostico_paginas[0]["fallback_enlaces"] is True


def test_rastreador_detecta_siguiente_por_texto_next_si_selector_no_coincide():
    paginas = {
        "https://example.test/news/": """
          <main><article><h2>Primera noticia paginada</h2><a href="/n/1">Leer</a></article></main>
          <a href="/news/page/2/">Next</a>
        """,
        "https://example.test/news/page/2/": """
          <main><article><h2>Segunda noticia paginada</h2><a href="/n/2">Leer</a></article></main>
        """,
    }

    rastreador = RastreadorPaginado(
        url_base="https://example.test/news/",
        selector_articulos="article",
        selector_siguiente=".no-existe",
        delay=0,
        max_paginas=2,
        fetcher=lambda url: paginas[url],
        respetar_robots=False,
    )

    resultados = rastreador.rastrear()

    assert len(resultados) == 2
    assert len(rastreador.paginas_visitadas) == 2
