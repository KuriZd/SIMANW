from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from pprint import pformat
import re
import unicodedata
from urllib.parse import urlparse

from config.fuentes_noticias import FUENTES_NOTICIAS


class FuentesService:
    """Consulta y valida el catalogo local de fuentes periodisticas."""

    CAMPOS_REQUERIDOS = (
        "id",
        "nombre",
        "tipo",
        "pais",
        "idioma",
        "base_url",
        "urls",
        "dominios_permitidos",
        "activo",
        "limite_noticias",
        "delay_segundos",
        "requiere_parser_html",
        "notas",
    )

    TIPOS_VALIDOS = {"rss", "html"}

    def __init__(
        self,
        fuentes: list[dict] | None = None,
        ruta_catalogo: str | Path = "config/fuentes_noticias.py",
    ) -> None:
        self._fuentes = deepcopy(fuentes if fuentes is not None else FUENTES_NOTICIAS)
        self._ruta_catalogo = Path(ruta_catalogo)

    def listar_fuentes(self, activas: bool = True) -> list[dict]:
        fuentes = [f for f in self._fuentes if not activas or f.get("activo") is True]
        return deepcopy(fuentes)

    def obtener_fuente(self, fuente_id: str) -> dict:
        for fuente in self._fuentes:
            if fuente.get("id") == fuente_id:
                return deepcopy(fuente)
        raise KeyError(f"Fuente no encontrada: {fuente_id}")

    def obtener_urls(self, fuente_id: str) -> list[str]:
        fuente = self.obtener_fuente(fuente_id)
        return list(fuente.get("urls", []))

    def validar_fuente(self, fuente: dict) -> tuple[bool, list[str]]:
        errores: list[str] = []

        for campo in self.CAMPOS_REQUERIDOS:
            if campo not in fuente:
                errores.append(f"Campo requerido ausente: {campo}")

        tipo = fuente.get("tipo")
        if tipo not in self.TIPOS_VALIDOS:
            errores.append("tipo debe ser 'rss' o 'html'")

        urls = fuente.get("urls")
        if not isinstance(urls, list) or not urls:
            errores.append("urls debe ser una lista no vacia")
        elif any(not isinstance(url, str) or not url.startswith(("http://", "https://")) for url in urls):
            errores.append("todas las urls deben ser http(s)")

        dominios = fuente.get("dominios_permitidos")
        if not isinstance(dominios, list) or not dominios:
            errores.append("dominios_permitidos debe ser una lista no vacia")

        limite = fuente.get("limite_noticias")
        if not isinstance(limite, int) or limite <= 0:
            errores.append("limite_noticias debe ser un entero positivo")

        delay = fuente.get("delay_segundos")
        if not isinstance(delay, (int, float)) or delay < 0:
            errores.append("delay_segundos debe ser numerico y no negativo")

        return not errores, errores

    def listar_nombres_fuentes(self) -> list[str]:
        return [fuente["nombre"] for fuente in self.listar_fuentes(activas=True)]

    def obtener_por_nombre(self, nombre: str) -> dict:
        nombre_norm = nombre.strip().casefold()
        for fuente in self._fuentes:
            if str(fuente.get("nombre", "")).casefold() == nombre_norm:
                return deepcopy(fuente)
        raise KeyError(f"Fuente no encontrada: {nombre}")

    def guardar_fuente_personalizada(
        self,
        url: str,
        tipo: str = "rss",
        nombre: str | None = None,
        limite_noticias: int = 20,
    ) -> dict:
        """Agrega una URL personalizada al catalogo local de fuentes."""
        url = str(url or "").strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("La URL debe iniciar con http:// o https://.")

        tipo_norm = "rss" if str(tipo).strip().lower() == "rss" else "html"
        parsed = urlparse(url)
        dominio = parsed.netloc.strip()
        if not dominio:
            raise ValueError("La URL no contiene un dominio valido.")

        for fuente in self._fuentes:
            urls = [str(item).strip() for item in fuente.get("urls", [])]
            if url in urls:
                return deepcopy(fuente)

        nombre_fuente = (nombre or self._nombre_desde_dominio(dominio)).strip()
        fuente_id = self._id_unico(self._slug(nombre_fuente))
        fuente = {
            "id": fuente_id,
            "nombre": nombre_fuente,
            "tipo": tipo_norm,
            "pais": "Personalizada",
            "idioma": "es",
            "base_url": f"{parsed.scheme}://{dominio}",
            "urls": [url],
            "dominios_permitidos": list(dict.fromkeys([dominio, dominio.removeprefix("www.")])),
            "activo": True,
            "limite_noticias": max(int(limite_noticias or 20), 1),
            "delay_segundos": 3,
            "requiere_parser_html": tipo_norm == "html",
            "notas": "Fuente guardada desde Custom RSS/URL.",
        }

        valida, errores = self.validar_fuente(fuente)
        if not valida:
            raise ValueError(f"Fuente personalizada invalida: {'; '.join(errores)}")

        self._fuentes.append(deepcopy(fuente))
        self._persistir_catalogo()
        return deepcopy(fuente)

    def _persistir_catalogo(self) -> None:
        contenido = "FUENTES_NOTICIAS = " + pformat(
            self._fuentes,
            width=100,
            sort_dicts=False,
        )
        self._ruta_catalogo.write_text(contenido + "\n", encoding="utf-8")

    def _id_unico(self, base: str) -> str:
        base = base or "fuente_personalizada"
        existentes = {str(fuente.get("id")) for fuente in self._fuentes}
        if base not in existentes:
            return base
        indice = 2
        while f"{base}_{indice}" in existentes:
            indice += 1
        return f"{base}_{indice}"

    @staticmethod
    def _slug(texto: str) -> str:
        normalizado = unicodedata.normalize("NFKD", texto.lower())
        ascii_texto = "".join(c for c in normalizado if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9]+", "_", ascii_texto).strip("_")

    @staticmethod
    def _nombre_desde_dominio(dominio: str) -> str:
        nombre = dominio.removeprefix("www.").split(".")[0].replace("-", " ").replace("_", " ")
        return nombre.title() or "Fuente personalizada"
