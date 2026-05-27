from __future__ import annotations

from copy import deepcopy

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

    def __init__(self, fuentes: list[dict] | None = None) -> None:
        self._fuentes = deepcopy(fuentes if fuentes is not None else FUENTES_NOTICIAS)

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
