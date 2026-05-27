"""Servicio de Fase 3: análisis de sentimientos, clasificación y tendencias."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

try:
    from src.sentimientos import AnalizadorSentimientos
    _SENTIMIENTOS_OK = True
except ImportError:
    _SENTIMIENTOS_OK = False

try:
    from src.clasificador_noticias import (
        ClasificadorNoticias,
        TEXTOS_ENTRENAMIENTO,
        ETIQUETAS_ENTRENAMIENTO,
    )
    _CLASIFICADOR_OK = True
except ImportError:
    _CLASIFICADOR_OK = False

try:
    from src.tendencias_temporales import TendenciasTemporales
    _TENDENCIAS_OK = True
except ImportError:
    _TENDENCIAS_OK = False


class Fase3Service:
    """Orquesta sentimientos, clasificación y tendencias sobre el corpus."""

    def __init__(self) -> None:
        self._analizador = AnalizadorSentimientos() if _SENTIMIENTOS_OK else None
        self._clasificador: ClasificadorNoticias | None = None
        if _CLASIFICADOR_OK:
            try:
                clf = ClasificadorNoticias()
                clf.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)
                self._clasificador = clf
            except Exception:
                self._clasificador = None

    # ─────────────────────────────────────────────────────────────────────────

    def analizar(
        self,
        noticias: list[dict],
        corpus: list[dict],
        on_progreso: Callable[[str], None] | None = None,
    ) -> tuple[list[dict], list[dict], dict]:
        """Enriquece noticias y corpus con sentimiento/categoría. Retorna
        (noticias_enriquecidas, corpus_enriquecido, analisis_dict).
        """
        errores: list[str] = []
        advertencias: list[str] = []

        def _log(msg: str) -> None:
            if on_progreso:
                on_progreso(msg)

        # ── 1. Sentimiento ────────────────────────────────────────────────────
        sentimientos_lista: list[dict] = []
        resumen_sent: dict = {}
        if self._analizador and noticias:
            try:
                noticias_copia = [dict(n) for n in noticias]
                sentimientos_lista, resumen_sent = self._analizador.analizar_noticias(noticias_copia)
            except Exception as exc:
                errores.append(f"Sentimientos: {exc}")

        _sent_default = {"positivo": 0.0, "negativo": 0.0, "neutral": 1.0, "compound": 0.0, "etiqueta": "neutral"}

        # ── 2. Clasificación ──────────────────────────────────────────────────
        categorias_pred: list[str] = []
        scores_lista: list[dict] = []
        if self._clasificador and noticias:
            try:
                noticias_clf = [dict(n) for n in noticias]
                self._clasificador.clasificar_noticias(noticias_clf)
                categorias_pred = [n.get("categoria_predicha", n.get("categoria", "sin_categoria")) for n in noticias_clf]
                scores_lista    = [n.get("scores_categoria", {}) for n in noticias_clf]
            except Exception as exc:
                errores.append(f"Clasificación: {exc}")

        # ── 3. Noticias enriquecidas (para chatbot y KG) ──────────────────────
        noticias_enriquecidas: list[dict] = []
        for i, n in enumerate(noticias):
            enr = dict(n)
            enr["sentimiento"] = sentimientos_lista[i] if i < len(sentimientos_lista) else _sent_default
            enr["categoria_predicha"] = categorias_pred[i] if i < len(categorias_pred) else n.get("categoria", "sin_categoria")
            enr["scores_categoria"] = scores_lista[i] if i < len(scores_lista) else {}
            enr["categoria_original"] = n.get("categoria", "sin_categoria")
            enr["fuente"] = n.get("fuente_nombre") or _dominio(n.get("url", ""))
            noticias_enriquecidas.append(enr)

        # ── 4. Corpus enriquecido (para motor_busqueda y UI) ──────────────────
        corpus_enriquecido: list[dict] = []
        for i, item in enumerate(corpus):
            enr = dict(item)
            enr["cuerpo"] = item.get("texto_original", item.get("cuerpo", ""))
            enr["sentimiento"] = sentimientos_lista[i] if i < len(sentimientos_lista) else _sent_default
            enr["categoria_predicha"] = categorias_pred[i] if i < len(categorias_pred) else item.get("categoria", "sin_categoria")
            enr["scores_categoria"] = scores_lista[i] if i < len(scores_lista) else {}
            corpus_enriquecido.append(enr)

        # ── 5. Tendencias ─────────────────────────────────────────────────────
        tendencias_data: dict = {}
        if _TENDENCIAS_OK and noticias_enriquecidas:
            try:
                tend = TendenciasTemporales()
                tend.cargar_noticias(noticias_enriquecidas)
                tabla = tend.tabla_resumen()
                if tabla:
                    tendencias_data = {
                        "granularidad": tend.granularidad,
                        "tabla": tabla,
                        "conclusion": tend.conclusion(),
                        "pico": tend.pico_notable(),
                        "texto_visual": tend.visualizacion_texto(),
                        "_tendencias_obj": tend,
                    }
            except Exception as exc:
                advertencias.append(f"Tendencias: {exc}")

        # ── 6. Métricas agregadas ─────────────────────────────────────────────
        cat_counter: Counter[str] = Counter(n.get("categoria_predicha", "sin_categoria") for n in noticias_enriquecidas)
        sent_counter: Counter[str] = Counter(
            s.get("etiqueta", "neutral") for s in sentimientos_lista
        ) if sentimientos_lista else Counter({"neutral": len(noticias)})

        termino_counter: Counter[str] = Counter()
        for item in corpus_enriquecido:
            termino_counter.update(item.get("terminos", []))
        terminos_frecuentes = [{"termino": t, "frecuencia": c} for t, c in termino_counter.most_common(20)]

        sentimiento_dominante = resumen_sent.get("tono_general", sent_counter.most_common(1)[0][0] if sent_counter else "neutral")

        analisis: dict = {
            "total_noticias": len(noticias),
            "categorias": dict(cat_counter),
            "sentimientos": dict(sent_counter),
            "sentimiento_dominante": sentimiento_dominante,
            "terminos_frecuentes": terminos_frecuentes,
            "tendencias": tendencias_data,
            "clasificacion": {
                "disponible": bool(self._clasificador),
                "categorias": list(cat_counter.keys()),
            },
            "errores": errores,
            "advertencias": advertencias,
        }

        return noticias_enriquecidas, corpus_enriquecido, analisis

    def exportar(
        self,
        analisis: dict,
        ruta_dir: str | Path = "outputs/analisis",
    ) -> Path:
        ruta = Path(ruta_dir)
        ruta.mkdir(parents=True, exist_ok=True)
        archivo = ruta / "reporte_analisis.json"
        exportable = {k: v for k, v in analisis.items() if not k.startswith("_")}
        archivo.write_text(json.dumps(exportable, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return archivo

    def exportar_tendencias_csv(
        self,
        analisis: dict,
        ruta: str | Path = "outputs/tendencias.csv",
    ) -> Path | None:
        tend_data = analisis.get("tendencias", {})
        tend_obj = tend_data.get("_tendencias_obj")
        if tend_obj is None:
            return None
        try:
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
            return tend_obj.exportar_csv(ruta)
        except Exception:
            return None

    def exportar_tendencias_png(
        self,
        analisis: dict,
        ruta: str | Path = "outputs/tendencias.png",
    ) -> Path | None:
        tend_obj = analisis.get("tendencias", {}).get("_tendencias_obj")
        if tend_obj is None:
            return None
        try:
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
            return tend_obj.exportar_png(ruta)
        except Exception:
            return None


def _dominio(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url
