from __future__ import annotations

import json
import time
from datetime import datetime, timezone
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
        fuente: str = "desconocida",
        selector_titulo: str | None = None,
        selector_resumen: str | None = None,
        selector_url: str | None = None,
        selector_fecha: str | None = None,
        selector_autor: str | None = None,
        selector_categoria: str | None = None,
        delay: float = 3.0,
        max_paginas: int = 5,
        max_noticias: int | None = None,
        user_agent: str = "SIMANWBot/1.0",
        fetcher: Callable[[str], str] | None = None,
        respetar_robots: bool = True,
    ) -> None:
        if delay < 3 and fetcher is None:
            raise ValueError("El delay minimo para rastreo real debe ser de 3 segundos")

        self.url_base = url_base
        self.fuente = fuente
        self.selector_articulos = selector_articulos
        self.selector_siguiente = selector_siguiente
        self.selector_titulo = selector_titulo
        self.selector_resumen = selector_resumen
        self.selector_url = selector_url
        self.selector_fecha = selector_fecha
        self.selector_autor = selector_autor
        self.selector_categoria = selector_categoria
        self.delay = delay
        self.max_paginas = max_paginas
        self.max_noticias = max_noticias
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self.fetcher = fetcher or self._fetch_real
        self.es_fetcher_real = fetcher is None
        self.respetar_robots = respetar_robots
        self.resultados: list[dict] = []
        self.paginas_visitadas: list[str] = []
        self.errores: list[str] = []
        self.diagnostico_paginas: list[dict] = []
        self.duplicados_omitidos = 0
        self.robots_verificado = False
        self.robots_permitido: bool | None = None
        self._robots: RobotFileParser | None = None

    def extraer_pagina(self, html: str, url_actual: str) -> list[dict]:
        """Extrae noticias desde una pagina HTML segun los selectores configurados."""
        soup = BeautifulSoup(html, "html.parser")
        articulos = soup.select(self.selector_articulos)
        noticias_pagina: list[dict] = []
        urls_vistos: set[str] = {n["url"] for n in self.resultados}
        fecha_extraccion = datetime.now(timezone.utc).isoformat()
        omitidas_sin_titulo = 0
        omitidas_duplicadas = 0

        for articulo in articulos:
            titulo = self._extraer_titulo(articulo)
            if not titulo:
                omitidas_sin_titulo += 1
                continue

            url = self._extraer_url(articulo, url_actual)
            if url in urls_vistos:
                self.duplicados_omitidos += 1
                omitidas_duplicadas += 1
                continue

            urls_vistos.add(url)
            noticias_pagina.append(
                {
                    "titulo": titulo,
                    "resumen": self._extraer_resumen(articulo),
                    "url": url,
                    "fecha": self._extraer_texto(articulo, self.selector_fecha),
                    "autor": self._extraer_texto(articulo, self.selector_autor),
                    "categoria": self._extraer_texto(articulo, self.selector_categoria),
                    "fuente": self.fuente,
                    "pagina_origen": url_actual,
                    "fecha_extraccion": fecha_extraccion,
                }
            )

        fallback_enlaces = False
        if not articulos:
            noticias_pagina = self._extraer_desde_enlaces(soup, url_actual, urls_vistos, fecha_extraccion)
            fallback_enlaces = bool(noticias_pagina)

        siguiente = self.obtener_siguiente_pagina(html, url_actual)
        self.diagnostico_paginas.append(
            {
                "url": url_actual,
                "selector_articulos": self.selector_articulos,
                "articulos_detectados": len(articulos),
                "noticias_extraidas": len(noticias_pagina),
                "fallback_enlaces": fallback_enlaces,
                "omitidas_sin_titulo": omitidas_sin_titulo,
                "omitidas_duplicadas": omitidas_duplicadas,
                "selector_siguiente": self.selector_siguiente,
                "siguiente_detectado": bool(siguiente),
                "url_siguiente": siguiente or "",
            }
        )
        if not articulos and not fallback_enlaces:
            self.errores.append(
                f"El selector de articulos '{self.selector_articulos}' no encontro coincidencias en {url_actual}."
            )
        elif not articulos and fallback_enlaces:
            self.errores.append(
                f"El selector de articulos '{self.selector_articulos}' no encontro coincidencias en {url_actual}; "
                "se uso fallback por enlaces de la pagina."
            )
        elif not noticias_pagina:
            self.errores.append(
                "Se encontraron "
                f"{len(articulos)} articulos en {url_actual}, pero no se extrajo ninguna noticia. "
                "Revisa el selector de titulo y el selector de URL."
            )

        return noticias_pagina

    def obtener_siguiente_pagina(self, html: str, url_actual: str) -> str | None:
        """Encuentra el enlace a la siguiente pagina."""
        soup = BeautifulSoup(html, "html.parser")
        siguiente = soup.select_one(self.selector_siguiente)
        if siguiente and siguiente.get("href"):
            return urljoin(url_actual, siguiente["href"])
        for enlace in soup.find_all("a", href=True):
            texto = enlace.get_text(" ", strip=True).casefold()
            aria = str(enlace.get("aria-label") or "").casefold()
            rel = " ".join(enlace.get("rel") or []).casefold()
            if (
                "next" in rel
                or texto in {"next", "siguiente", "older", "older posts", "mas", "más", ">", "›", "»"}
                or "next" in aria
                or "siguiente" in aria
            ):
                return urljoin(url_actual, enlace["href"])
        return None

    def puede_rastrear(self, url: str) -> bool:
        """Valida si robots.txt permite rastrear la URL."""
        if not self.respetar_robots:
            return True
        parser = self._obtener_robots_parser()
        permitido = parser.can_fetch(self.user_agent, url)
        self.robots_permitido = permitido
        return permitido

    def rastrear(self, minimo_noticias: int | None = None) -> list[dict]:
        """Ejecuta el rastreo completo con paginacion."""
        self.resultados = []
        self.paginas_visitadas = []
        self.errores = []
        self.diagnostico_paginas = []
        self.duplicados_omitidos = 0
        url_actual: str | None = self.url_base
        limite = minimo_noticias or self.max_noticias

        while url_actual and len(self.paginas_visitadas) < self.max_paginas:
            if not self.puede_rastrear(url_actual):
                self.errores.append(f"Bloqueado por robots.txt: {url_actual}")
                break

            try:
                html = self.fetcher(url_actual)
            except requests.RequestException as exc:
                self.errores.append(f"Error HTTP en {url_actual}: {exc}")
                break
            except Exception as exc:
                self.errores.append(f"Error al obtener {url_actual}: {exc}")
                break

            if not html or not html.strip():
                self.errores.append(f"Pagina vacia: {url_actual}")
                break

            self.paginas_visitadas.append(url_actual)
            self.resultados.extend(self.extraer_pagina(html, url_actual))

            if limite is not None and len(self.resultados) >= limite:
                self.resultados = self.resultados[:limite]
                break

            url_siguiente = self.diagnostico_paginas[-1]["url_siguiente"] if self.diagnostico_paginas else ""
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

    def _extraer_titulo(self, articulo) -> str:
        if self.selector_titulo:
            elem = articulo.select_one(self.selector_titulo)
            if elem:
                return elem.get_text(strip=True)
        elem = articulo.find(["h1", "h2", "h3"])
        return elem.get_text(strip=True) if elem else ""

    def _extraer_resumen(self, articulo) -> str:
        if self.selector_resumen:
            elem = articulo.select_one(self.selector_resumen)
            if elem:
                return elem.get_text(" ", strip=True)
        elem = articulo.find("p")
        return elem.get_text(" ", strip=True) if elem else ""

    def _extraer_url(self, articulo, url_actual: str) -> str:
        if self.selector_url:
            elem = articulo.select_one(self.selector_url)
            if elem and elem.get("href"):
                return urljoin(url_actual, elem["href"])
        elem = articulo.find("a")
        if elem and elem.get("href"):
            return urljoin(url_actual, elem["href"])
        return url_actual

    def _fetch_real(self, url: str) -> str:
        response = self.session.get(url, timeout=15, allow_redirects=True)
        response.raise_for_status()
        return response.text

    def _esperar(self) -> None:
        if self.es_fetcher_real:
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
            self.robots_verificado = True
        except Exception:
            self.robots_verificado = False
            self.errores.append(f"No se pudo verificar robots.txt: {robots_url}")
            parser.parse(["User-agent: *", "Disallow: /"])

        self._robots = parser
        return parser

    def evidencia(self, archivo_json: str | Path | None = None) -> dict:
        noticias = len(self.resultados)
        estado = "completo" if noticias >= 20 and self.robots_permitido is not False else "parcial"
        return {
            "ac": "AC-1",
            "estado": estado,
            "ejecutado_desde": "Load / Analyze News",
            "fuente": self.fuente,
            "url_base": self.url_base,
            "noticias_extraidas": noticias,
            "paginas_visitadas": len(self.paginas_visitadas),
            "robots_verificado": self.robots_verificado,
            "robots_permitido": self.robots_permitido if self.respetar_robots else True,
            "delay_segundos": self.delay if self.es_fetcher_real else 0,
            "duplicados_omitidos": self.duplicados_omitidos,
            "archivo_json": str(archivo_json) if archivo_json else "",
            "errores": list(self.errores),
            "diagnostico_paginas": list(self.diagnostico_paginas),
        }

    @staticmethod
    def _extraer_texto(articulo, selector: str | None) -> str:
        if not selector:
            return ""
        elem = articulo.select_one(selector)
        if elem:
            return elem.get_text(" ", strip=True)
        return ""

    def _extraer_desde_enlaces(
        self,
        soup: BeautifulSoup,
        url_actual: str,
        urls_vistos: set[str],
        fecha_extraccion: str,
    ) -> list[dict]:
        noticias: list[dict] = []
        base_domain = urlparse(url_actual).netloc
        for enlace in soup.find_all("a", href=True):
            titulo = enlace.get_text(" ", strip=True)
            if len(titulo) < 20:
                continue
            url = urljoin(url_actual, enlace["href"])
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc and parsed.netloc != base_domain and not parsed.netloc.endswith(base_domain):
                continue
            if url in urls_vistos:
                self.duplicados_omitidos += 1
                continue
            urls_vistos.add(url)
            noticias.append(
                {
                    "titulo": titulo,
                    "resumen": "",
                    "url": url,
                    "fecha": "",
                    "autor": "",
                    "categoria": "",
                    "fuente": self.fuente,
                    "pagina_origen": url_actual,
                    "fecha_extraccion": fecha_extraccion,
                }
            )
        return noticias


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
