from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


class RastreadorPaginado:
    """
    AC-1: Rastreador que navega paginacion de un sitio con respeto a robots.txt.

    Para pruebas y demostraciones puede recibir un `fetcher` que devuelva HTML
    simulado. En uso real, el fetcher por defecto usa requests.
    """

    def __init__(
        self,
        url_base: str,
        selector_articulos: str,
        selector_siguiente: str,
        delay: float = 3.0,
        max_paginas: int = 5,
        user_agent: str = "SIMANWBot/1.0",
        fetcher: Callable[[str], str] | None = None,
        respetar_robots: bool = True,
    ) -> None:
        if delay < 3 and fetcher is None:
            raise ValueError("El delay minimo para rastreo real debe ser de 3 segundos")

        self.url_base = url_base
        self.selector_articulos = selector_articulos
        self.selector_siguiente = selector_siguiente
        self.delay = delay
        self.max_paginas = max_paginas
        self.user_agent = user_agent
        self.fetcher = fetcher or self._fetch_real
        self.respetar_robots = respetar_robots
        self.resultados: list[dict] = []
        self.paginas_visitadas: list[str] = []
        self._robots: RobotFileParser | None = None

    def extraer_pagina(self, html: str, url_actual: str) -> list[dict]:
        """Extrae noticias desde una pagina HTML segun los selectores configurados."""
        soup = BeautifulSoup(html, "html.parser")
        articulos = soup.select(self.selector_articulos)
        noticias_pagina = []

        for articulo in articulos:
            titulo_elem = articulo.find(["h1", "h2", "h3"])
            parrafo_elem = articulo.find("p")
            enlace_elem = articulo.find("a")

            if not titulo_elem:
                continue

            noticias_pagina.append(
                {
                    "titulo": titulo_elem.get_text(strip=True),
                    "resumen": parrafo_elem.get_text(" ", strip=True) if parrafo_elem else "",
                    "url": urljoin(url_actual, enlace_elem["href"])
                    if enlace_elem and enlace_elem.get("href")
                    else url_actual,
                    "pagina_origen": url_actual,
                }
            )

        return noticias_pagina

    def obtener_siguiente_pagina(self, html: str, url_actual: str) -> str | None:
        """Encuentra el enlace a la siguiente pagina."""
        soup = BeautifulSoup(html, "html.parser")
        siguiente = soup.select_one(self.selector_siguiente)
        if siguiente and siguiente.get("href"):
            return urljoin(url_actual, siguiente["href"])
        return None

    def puede_rastrear(self, url: str) -> bool:
        """Valida si robots.txt permite rastrear la URL."""
        if not self.respetar_robots:
            return True

        parser = self._obtener_robots_parser()
        return parser.can_fetch(self.user_agent, url)

    def rastrear(self, minimo_noticias: int | None = None) -> list[dict]:
        """Ejecuta el rastreo completo con paginacion."""
        self.resultados = []
        self.paginas_visitadas = []
        url_actual: str | None = self.url_base

        while url_actual and len(self.paginas_visitadas) < self.max_paginas:
            if not self.puede_rastrear(url_actual):
                break

            html = self.fetcher(url_actual)
            self.paginas_visitadas.append(url_actual)
            self.resultados.extend(self.extraer_pagina(html, url_actual))

            if minimo_noticias is not None and len(self.resultados) >= minimo_noticias:
                break

            url_siguiente = self.obtener_siguiente_pagina(html, url_actual)
            if not url_siguiente or len(self.paginas_visitadas) >= self.max_paginas:
                break

            url_actual = url_siguiente
            self._esperar()

        return self.resultados

    def guardar_json(self, archivo: str | Path) -> int:
        ruta = Path(archivo)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", encoding="utf-8") as file:
            json.dump(self.resultados, file, ensure_ascii=False, indent=2)
        return len(self.resultados)

    def _fetch_real(self, url: str) -> str:
        response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=15)
        response.raise_for_status()
        return response.text

    def _esperar(self) -> None:
        if self.fetcher is self._fetch_real:
            time.sleep(self.delay)
        elif self.delay > 0:
            time.sleep(min(self.delay, 0.1))

    def _obtener_robots_parser(self) -> RobotFileParser:
        if self._robots is not None:
            return self._robots

        parsed = urlparse(self.url_base)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            parser.read()
        except Exception:
            # Si robots.txt no puede leerse, se evita bloquear demos locales.
            parser.parse(["User-agent: *", "Allow: /"])

        self._robots = parser
        return parser


def crear_fetcher_simulado(noticias_por_pagina: int = 5, total_paginas: int = 4) -> Callable[[str], str]:
    """Crea paginas simuladas suficientes para demostrar extraccion de 20 noticias."""

    def fetcher(url: str) -> str:
        parsed = urlparse(url)
        query = parsed.query
        pagina = 1
        if "page=" in query:
            try:
                pagina = int(query.split("page=", 1)[1].split("&", 1)[0])
            except ValueError:
                pagina = 1

        inicio = (pagina - 1) * noticias_por_pagina
        articulos = []
        for offset in range(1, noticias_por_pagina + 1):
            numero = inicio + offset
            articulos.append(
                f"""
                <article>
                  <h2>Noticia real simulada {numero}</h2>
                  <p>Contenido extraido de una pagina con paginacion.</p>
                  <a href="/noticia/{numero}">Leer</a>
                </article>
                """
            )

        siguiente = ""
        if pagina < total_paginas:
            siguiente = f'<a class="next-page" href="/noticias?page={pagina + 1}">Siguiente</a>'

        return f"<main>{''.join(articulos)}</main>{siguiente}"

    return fetcher
