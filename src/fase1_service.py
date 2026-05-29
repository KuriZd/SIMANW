from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from src.exportador import guardar_csv, guardar_json
from src.extractor import ExtractorNoticias
from src.fuentes_service import FuentesService
from src.html_demo import html_portal_noticias
from src.rastreador_paginado import RastreadorPaginado, crear_fetcher_simulado
from src.rastreador_rss import RastreadorRSS


FuenteFase1 = Literal["demo", "rss", "paginado", "predefinida"]


@dataclass
class ResultadoFase1:
    noticias: list[dict]
    fuente: FuenteFase1
    errores: list[str]
    evidencia: dict | None = None


class Fase1Service:
    """Orquesta solo la Fase 1: extraccion/rastreo y exportacion cruda."""

    def __init__(
        self,
        ruta_json: str | Path = "data/raw/noticias.json",
        ruta_csv: str | Path = "data/raw/noticias.csv",
    ) -> None:
        self.ruta_json = Path(ruta_json)
        self.ruta_csv = Path(ruta_csv)
        self.fuentes_service = FuentesService()
        self.noticias: list[dict] = []
        self.errores: list[str] = []
        self.ultima_evidencia: dict | None = None

    def ejecutar(self, fuente: FuenteFase1, url: str = "", limite_noticias: int | None = None) -> ResultadoFase1:
        """Ejecuta la fuente indicada y deja las noticias normalizadas en memoria."""
        fuente = self._normalizar_fuente(fuente)
        self.errores = []
        self.ultima_evidencia = None
        limite = max(int(limite_noticias or 0), 1) if limite_noticias else None

        if fuente == "demo":
            noticias = self._extraer_demo(limite_noticias=limite)
        elif fuente == "rss":
            noticias = self._extraer_rss(url, limite_noticias=limite)
        elif fuente == "paginado":
            noticias = self._rastrear_paginado(url)
        elif fuente == "predefinida":
            noticias = self.ejecutar_fuente_predefinida(url, limite_noticias=limite)
        else:
            raise ValueError(f"Fuente no soportada: {fuente}")

        if fuente == "predefinida":
            self.noticias = noticias
        else:
            self.noticias = [self._normalizar_noticia(noticia, idx) for idx, noticia in enumerate(noticias, start=1)]
        return ResultadoFase1(
            noticias=self.noticias,
            fuente=fuente,
            errores=self.errores,
            evidencia=self.ultima_evidencia,
        )

    def ejecutar_demo(self) -> ResultadoFase1:
        return self.ejecutar("demo")

    def ejecutar_rss(self, url: str) -> ResultadoFase1:
        return self.ejecutar("rss", url)

    def ejecutar_paginado(self, url: str = "") -> ResultadoFase1:
        return self.ejecutar("paginado", url)

    def ejecutar_paginado_configurado(self, config: dict) -> ResultadoFase1:
        self.errores = []
        self.ultima_evidencia = None
        noticias = self._rastrear_paginado_config(config)
        self.noticias = [self._normalizar_noticia(noticia, idx) for idx, noticia in enumerate(noticias, start=1)]
        return ResultadoFase1(
            noticias=self.noticias,
            fuente="paginado",
            errores=self.errores,
            evidencia=self.ultima_evidencia,
        )

    def ejecutar_fuente_predefinida(self, fuente_id: str, limite_noticias: int | None = None) -> list[dict]:
        fuente = self.fuentes_service.obtener_fuente(fuente_id)
        valida, errores = self.fuentes_service.validar_fuente(fuente)
        if not valida:
            raise ValueError(f"Fuente predefinida invalida: {'; '.join(errores)}")

        self.errores = []
        noticias_raw: list[dict] = []
        tipo = fuente["tipo"]
        limite_total = int(limite_noticias or fuente.get("limite_noticias", 20))
        urls = list(fuente.get("urls", []))

        if tipo == "rss":
            for url in urls:
                if len(noticias_raw) >= limite_total:
                    break
                rastreador = RastreadorRSS(
                    url,
                    categoria_default="sin_categoria",
                    max_noticias=max(limite_total - len(noticias_raw), 1),
                )
                noticias_url = rastreador.extraer()
                noticias_raw.extend(noticias_url)
                self.errores.extend(rastreador.errores)
        elif tipo == "html":
            for url in urls:
                if len(noticias_raw) >= limite_total:
                    break
                noticias_raw.extend(self._rastrear_paginado(url))
        else:
            raise ValueError(f"Tipo de fuente no soportado: {tipo}")

        noticias_norm = [
            self._normalizar_noticia(noticia, idx, fuente)
            for idx, noticia in enumerate(noticias_raw[:limite_total], start=1)
        ]
        self.noticias = noticias_norm
        return noticias_norm

    def exportar(self) -> tuple[Path, Path]:
        """Exporta el ultimo resultado normalizado a JSON y CSV."""
        return self.exportar_todo(self.noticias)

    def exportar_json(self, noticias: list[dict] | None = None) -> Path:
        self.noticias = noticias if noticias is not None else self.noticias
        return guardar_json(self.noticias, self.ruta_json)

    def exportar_csv(self, noticias: list[dict] | None = None) -> Path:
        self.noticias = noticias if noticias is not None else self.noticias
        return guardar_csv(self.noticias, self.ruta_csv)

    def exportar_todo(self, noticias: list[dict] | None = None) -> tuple[Path, Path]:
        self.noticias = noticias if noticias is not None else self.noticias
        json_path = self.exportar_json(self.noticias)
        csv_path = self.exportar_csv(self.noticias)
        return json_path, csv_path

    def _extraer_demo(self, limite_noticias: int | None = None) -> list[dict]:
        extractor = ExtractorNoticias()
        noticias = extractor.extraer_de_html(html_portal_noticias, url_base="https://portal-noticias.com")
        self.errores.extend(extractor.errores)
        return noticias[:limite_noticias] if limite_noticias else noticias

    def _extraer_rss(self, url: str, limite_noticias: int | None = None) -> list[dict]:
        if not url.strip():
            raise ValueError("La fuente RSS requiere una URL.")
        rastreador = RastreadorRSS(url.strip(), max_noticias=limite_noticias or 25)
        noticias = rastreador.extraer()
        self.errores.extend(rastreador.errores)
        return noticias

    def _rastrear_paginado(self, url: str) -> list[dict]:
        url = url.strip()
        if url:
            return self._rastrear_paginado_config({"url_base": url})
        else:
            rastreador = RastreadorPaginado(
                url_base="https://ejemplo-noticias.com/noticias?page=1",
                selector_articulos="article",
                selector_siguiente="a.next-page",
                delay=0,
                max_paginas=4,
                fetcher=crear_fetcher_simulado(noticias_por_pagina=5, total_paginas=4),
                respetar_robots=False,
            )

        noticias = rastreador.rastrear(minimo_noticias=20 if not url else None)
        self.ultima_evidencia = rastreador.evidencia()
        if not noticias:
            self.errores.append("No se extrajeron noticias del rastreo paginado.")
        self.errores.extend(rastreador.errores)
        return noticias

    def _rastrear_paginado_config(self, config: dict) -> list[dict]:
        url = str(config.get("url_base") or config.get("url") or "").strip()
        if not url:
            raise ValueError("La fuente paginada requiere una URL inicial.")
        delay = max(float(config.get("delay", 3) or 3), 3.0)
        max_paginas = int(config.get("max_paginas", 5) or 5)
        minimo_noticias = int(config.get("minimo_noticias", config.get("max_noticias", 20)) or 20)
        rastreador = RastreadorPaginado(
            url_base=url,
            fuente=str(config.get("fuente") or dominio_desde_url(url)),
            selector_articulos=str(config.get("selector_articulos") or "article"),
            selector_siguiente=str(config.get("selector_siguiente") or "a[rel='next'], a.next-page, .next a"),
            selector_titulo=config.get("selector_titulo") or None,
            selector_resumen=config.get("selector_resumen") or None,
            selector_url=config.get("selector_url") or None,
            selector_fecha=config.get("selector_fecha") or None,
            selector_autor=config.get("selector_autor") or None,
            selector_categoria=config.get("selector_categoria") or None,
            delay=delay,
            max_paginas=max_paginas,
            max_noticias=minimo_noticias,
            user_agent=str(config.get("user_agent") or "SIMANWBot/1.0 (proyecto-academico)"),
            respetar_robots=bool(config.get("respetar_robots", True)),
        )
        noticias = rastreador.rastrear(minimo_noticias=minimo_noticias)
        self.ultima_evidencia = rastreador.evidencia()
        if not noticias:
            self.errores.append("No se extrajeron noticias del rastreo paginado.")
            diagnostico = self.ultima_evidencia.get("diagnostico_paginas", []) if self.ultima_evidencia else []
            if diagnostico:
                primera = diagnostico[0]
                self.errores.append(
                    "Diagnostico paginado: "
                    f"{primera.get('articulos_detectados', 0)} articulos detectados, "
                    f"{primera.get('noticias_extraidas', 0)} noticias extraidas, "
                    f"siguiente detectado: {primera.get('siguiente_detectado', False)}."
                )
        if len(noticias) < minimo_noticias:
            self.errores.append(
                f"Rastreo paginado incompleto: {len(noticias)} de {minimo_noticias} noticias requeridas."
            )
        self.errores.extend(rastreador.errores)
        return noticias

    @staticmethod
    def _normalizar_noticia(noticia: dict, indice: int, fuente: dict | None = None) -> dict:
        titulo = str(noticia.get("titulo") or f"Noticia {indice}").strip()
        cuerpo = str(noticia.get("cuerpo") or noticia.get("resumen") or titulo).strip()
        fecha = str(noticia.get("fecha") or "").strip()[:10] or "sin_fecha"
        autor = str(noticia.get("autor") or "Autor desconocido").strip()
        categoria = str(
            noticia.get("categoria")
            or noticia.get("categoria_original")
            or noticia.get("category")
            or "sin_categoria"
        ).strip()
        url = str(noticia.get("url") or noticia.get("link") or "").strip()
        if not url:
            url = f"https://simanw.local/fase1/noticia/{indice}"

        normalizada = {
            "titulo": titulo,
            "cuerpo": cuerpo,
            "fecha": fecha,
            "autor": autor,
            "categoria": categoria,
            "url": url,
        }
        if fuente:
            normalizada.update(
                {
                    "fuente_nombre": fuente["nombre"],
                    "fuente_id": fuente["id"],
                    "fuente_tipo": fuente["tipo"],
                }
            )
        return normalizada

    @staticmethod
    def _normalizar_fuente(fuente: str) -> FuenteFase1:
        valor = fuente.strip().lower()
        alias = {
            "demo": "demo",
            "rss": "rss",
            "paginado": "paginado",
            "predefinida": "predefinida",
            "fuente predefinida": "predefinida",
            "rastreo paginado": "paginado",
        }
        if valor not in alias:
            raise ValueError("Fuente valida: demo, rss o paginado.")
        return alias[valor]  # type: ignore[return-value]


def dominio_desde_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url
