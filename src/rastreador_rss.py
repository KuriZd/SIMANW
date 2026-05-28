"""Rastreador de noticias mediante feeds RSS/Atom."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
from bs4 import BeautifulSoup


FEEDS_DEMO: dict[str, str] = {
    "BBC Mundo":          "https://feeds.bbci.co.uk/mundo/rss.xml",
    "El Universal":       "https://www.eluniversal.com.mx/arc/outboundfeeds/rss/?outputType=xml",
    "Proceso":            "https://www.proceso.com.mx/rss",
    "La Jornada":         "https://www.jornada.com.mx/rss/edicion.xml",
    "Expansión":          "https://expansion.mx/rss",
    "Milenio Tecnología": "https://www.milenio.com/rss/tecnologia",
    "Milenio Economía":   "https://www.milenio.com/rss/negocios",
    "Excélsior":          "https://www.excelsior.com.mx/rss.xml",
    "Reuters ES":         "https://feeds.reuters.com/reuters/MXeconomicsNews",
    "NASA":               "https://www.nasa.gov/rss/dyn/breaking_news.rss",
}


class RastreadorRSS:
    """Extrae noticias desde un feed RSS/Atom y las convierte al formato estándar SIMANW."""

    def __init__(
        self,
        url_feed: str,
        categoria_default: str = "sin_categoria",
        max_noticias: int = 20,
        timeout: int = 15,
    ) -> None:
        self.url_feed = url_feed
        self.categoria_default = categoria_default
        self.max_noticias = max_noticias
        self.timeout = timeout
        self.fuente = urlparse(url_feed).netloc or url_feed
        self.noticias: list[dict] = []
        self.errores: list[str] = []

    def extraer(self) -> list[dict]:
        """Descarga el feed y devuelve noticias en formato SIMANW."""
        self.noticias = []
        self.errores = []

        try:
            feed = feedparser.parse(
                self.url_feed,
                request_headers={
                    "User-Agent": "SIMANWBot/1.0 (+https://simanw.org)",
                    "Accept": "application/rss+xml, application/xml, text/xml",
                },
            )
        except Exception as exc:
            self.errores.append(f"Error de red: {exc}")
            return []

        if not feed.entries:
            msg = str(getattr(feed, "bozo_exception", "Sin entradas en el feed"))
            self.errores.append(f"Feed vacío o inaccesible: {msg}")
            return []

        for idx, entry in enumerate(feed.entries[: self.max_noticias]):
            try:
                self.noticias.append(self._convertir(entry))
            except Exception as exc:
                self.errores.append(f"Entrada {idx + 1}: {exc}")

        return self.noticias

    def resumen(self) -> dict:
        return {
            "feed": self.url_feed,
            "fuente": self.fuente,
            "total_extraidas": len(self.noticias),
            "errores": len(self.errores),
            "detalle_errores": self.errores,
        }

    # ── conversión ──────────────────────────────────────────────────────────

    def _convertir(self, entry) -> dict:
        titulo = (getattr(entry, "title", "") or "").strip()
        if not titulo:
            raise ValueError("Entrada sin título")

        cuerpo = self._limpiar_html(
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
            or titulo
        )

        return {
            "titulo": titulo,
            "cuerpo": cuerpo or titulo,
            "fecha": self._fecha(entry),
            "autor": self._autor(entry),
            "categoria_original": self._categoria(entry),
            "url": getattr(entry, "link", self.url_feed) or self.url_feed,
            "fuente": f"https://{self.fuente}",
        }

    def _fecha(self, entry) -> str:
        for attr in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    return datetime(*parsed[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d")
                except Exception:
                    pass
        for attr in ("published", "updated"):
            raw = getattr(entry, attr, "") or ""
            for fmt in (
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(raw[:25].strip(), fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
        return datetime.now().strftime("%Y-%m-%d")

    def _autor(self, entry) -> str:
        autor = (getattr(entry, "author", "") or "").strip()
        if not autor:
            authors = getattr(entry, "authors", [])
            if authors:
                autor = (authors[0].get("name", "") or "").strip()
        return autor or "Redacción"

    def _categoria(self, entry) -> str:
        tags = getattr(entry, "tags", [])
        if tags:
            term = (tags[0].get("term", "") or "").lower().strip()
            if term:
                return term
        categoria_url = self._categoria_desde_url(getattr(entry, "link", "") or "")
        if categoria_url:
            return categoria_url
        return self.categoria_default

    @staticmethod
    def _categoria_desde_url(url: str) -> str:
        """Infiere una categoria editorial basica desde segmentos comunes de URL."""
        categorias_validas = {
            "ciencia": "ciencia",
            "ciencias": "ciencia",
            "deportes": "deportes",
            "economia": "economia",
            "economía": "economia",
            "estados": "estados",
            "espectaculos": "espectaculos",
            "espectáculos": "espectaculos",
            "mundo": "mundo",
            "opinion": "opinion",
            "opinión": "opinion",
            "politica": "politica",
            "política": "politica",
            "tecnologia": "tecnologia",
            "tecnología": "tecnologia",
        }
        path = urlparse(url).path.lower()
        for segmento in path.split("/"):
            limpio = segmento.strip()
            if limpio in categorias_validas:
                return categorias_validas[limpio]
        return ""

    @staticmethod
    def _limpiar_html(texto: str) -> str:
        if not texto:
            return ""
        limpio = BeautifulSoup(texto, "html.parser").get_text(" ", strip=True)
        return re.sub(r"\s+", " ", limpio).strip()
