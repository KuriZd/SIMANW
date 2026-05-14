from __future__ import annotations

from dataclasses import dataclass, asdict
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass
class Noticia:
    titulo: str
    cuerpo: str
    fecha: str
    autor: str
    categoria_original: str
    url: str
    fuente: str


class ExtractorNoticias:
    """Extrae noticias desde HTML con estructura basada en artículos."""

    def __init__(self) -> None:
        self.noticias_extraidas: list[dict] = []
        self.errores: list[str] = []

    def extraer_de_html(self, html_content: str, url_base: str = "https://portal.com") -> list[dict]:
        soup = BeautifulSoup(html_content, "html.parser")
        articulos = soup.select("article.noticia")

        for indice, articulo in enumerate(articulos, start=1):
            try:
                noticia = self._extraer_articulo(articulo, url_base)
                self.noticias_extraidas.append(asdict(noticia))
            except Exception as error:
                self.errores.append(f"Artículo {indice}: {error}")

        return self.noticias_extraidas

    def _extraer_articulo(self, articulo, url_base: str) -> Noticia:
        titulo = self._texto_requerido(articulo, "h2")
        cuerpo = self._texto_requerido(articulo, "p.cuerpo")
        fecha = self._texto_requerido(articulo, "span.fecha")
        autor = self._texto_requerido(articulo, "span.autor")
        categoria = articulo.get("data-categoria", "sin_categoria")

        enlace = articulo.select_one("a.leer-mas")
        if enlace is None or not enlace.get("href"):
            raise ValueError("No se encontró la URL de la noticia")

        return Noticia(
            titulo=titulo,
            cuerpo=cuerpo,
            fecha=fecha,
            autor=autor,
            categoria_original=categoria,
            url=urljoin(url_base, enlace["href"]),
            fuente=url_base,
        )

    @staticmethod
    def _texto_requerido(elemento, selector: str) -> str:
        resultado = elemento.select_one(selector)
        if resultado is None:
            raise ValueError(f"No se encontró el campo requerido: {selector}")

        texto = resultado.get_text(" ", strip=True)
        if not texto:
            raise ValueError(f"El campo está vacío: {selector}")

        return " ".join(texto.split())

    def resumen_extraccion(self) -> dict:
        categorias = sorted({n["categoria_original"] for n in self.noticias_extraidas})
        fechas = [n["fecha"] for n in self.noticias_extraidas]

        return {
            "total_extraidas": len(self.noticias_extraidas),
            "errores": len(self.errores),
            "detalle_errores": self.errores,
            "categorias": categorias,
            "rango_fechas": (min(fechas), max(fechas)) if fechas else None,
        }
