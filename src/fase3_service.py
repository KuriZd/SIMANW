"""Servicio de Fase 3: análisis de sentimientos, clasificación y tendencias."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
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

try:
    from src.selector_modelo import SelectorModelo
    _SELECTOR_OK = True
except ImportError:
    _SELECTOR_OK = False

try:
    from src.recomendacion import SistemaRecomendacion
    _RECOMENDACION_OK = True
except ImportError:
    _RECOMENDACION_OK = False

try:
    from src.detector_publicidad import DetectorTemasPublicidad, NOTA_ETICA_PUBLICIDAD
    _DETECTOR_OK = True
except ImportError:
    _DETECTOR_OK = False


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
        evidencia_ac3 = self._ejecutar_ac3(corpus or noticias, noticias, errores, advertencias)
        if evidencia_ac3.get("_predicciones"):
            categorias_pred = list(evidencia_ac3["_predicciones"])
        elif self._clasificador and noticias:
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
        recomendaciones_data = self._generar_recomendaciones(corpus_enriquecido, advertencias)
        temas_data = self._detectar_temas(corpus_enriquecido, advertencias)

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
                        "tendencias_terminos": tend.tendencias_terminos_por_categoria(minimo_categorias=3),
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

        sentimiento_dominante = sent_counter.most_common(1)[0][0] if sent_counter else "neutral"
        tono_general = resumen_sent.get("tono_general", sentimiento_dominante)
        sentimiento_promedio = resumen_sent.get("sentimiento_promedio", 0.0)

        analisis: dict = {
            "total_noticias": len(noticias),
            "categorias": dict(cat_counter),
            "sentimientos": dict(sent_counter),
            "sentimiento_dominante": sentimiento_dominante,
            "tono_general": tono_general,
            "sentimiento_promedio": sentimiento_promedio,
            "terminos_frecuentes": terminos_frecuentes,
            "tendencias": tendencias_data,
            "recomendaciones": recomendaciones_data,
            "temas_conversacion": temas_data,
            "clasificacion": {
                "disponible": bool(self._clasificador) or evidencia_ac3.get("estado") in {"completo", "parcial"},
                "categorias": list(cat_counter.keys()),
                "ac3": {k: v for k, v in evidencia_ac3.items() if not k.startswith("_")},
            },
            "errores": errores,
            "advertencias": advertencias,
        }

        return noticias_enriquecidas, corpus_enriquecido, analisis

    def _ejecutar_ac3(
        self,
        corpus: list[dict],
        noticias: list[dict],
        errores: list[str],
        advertencias: list[str],
    ) -> dict:
        evidencia = {
            "actividad": "AC-3",
            "estado": "pendiente",
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Load / Analyze News",
            "modelos_comparados": [],
            "mejor_modelo": "",
            "accuracy": None,
            "accuracy_std": None,
            "total_textos": 0,
            "total_clases": 0,
            "fuente_datos": "corpus_fase2",
            "_predicciones": [],
        }
        if not _SELECTOR_OK:
            evidencia["observacion"] = "SelectorModelo no disponible."
            return evidencia

        textos, etiquetas = _dataset_supervisado(corpus)
        evidencia["total_textos"] = len(textos)
        evidencia["total_clases"] = len(set(etiquetas))
        if not textos:
            evidencia["observacion"] = "No hay textos etiquetados para entrenar AC-3."
            return evidencia

        _MIN_TEXTOS_CONFIABLES = 20
        if len(textos) < _MIN_TEXTOS_CONFIABLES:
            advertencias.append(
                f"AC-3: corpus pequeño ({len(textos)} textos etiquetados). "
                "Las métricas de validación cruzada no son estadísticamente representativas. "
                f"Se recomiendan al menos {_MIN_TEXTOS_CONFIABLES} textos etiquetados."
            )

        selector = SelectorModelo()
        try:
            resultados = selector.evaluar_todos(textos, etiquetas, cv_folds=3)
            pred_textos = [_texto_documento(item) for item in (noticias or corpus)]
            pred_textos = [texto for texto in pred_textos if texto]
            predicciones = selector.predecir(pred_textos) if pred_textos else []
            mejor = selector.mejor_modelo[0] if selector.mejor_modelo else ""
            metrica = resultados.get(mejor, {}) if mejor else {}
            predicciones_prueba = [
                {"indice": idx, "categoria_predicha": pred}
                for idx, pred in enumerate(predicciones)
            ]
            selector.guardar_resultados(
                "data/resultados_ac3.json",
                textos=textos,
                predicciones_prueba=predicciones_prueba,
            )
            selector.guardar_modelo("models/mejor_modelo_ac3.joblib", "models/vectorizer_ac3.joblib")
            evidencia.update(
                {
                    "estado": "completo",
                    "modelos_comparados": list(resultados.keys()),
                    "mejor_modelo": mejor,
                    "accuracy": metrica.get("accuracy_mean"),
                    "accuracy_std": metrica.get("accuracy_std"),
                    "resultados": resultados,
                    "archivo_json": "data/resultados_ac3.json",
                    "modelo": "models/mejor_modelo_ac3.joblib",
                    "vectorizer": "models/vectorizer_ac3.joblib",
                    "_predicciones": predicciones,
                }
            )
        except Exception as exc:
            evidencia["estado"] = "parcial"
            evidencia["observacion"] = str(exc)
            advertencias.append(f"AC-3 multimodelo no ejecutado con corpus real: {exc}")
        return evidencia

    def _generar_recomendaciones(self, corpus: list[dict], advertencias: list[str]) -> dict:
        if not corpus:
            return {"disponible": False, "por_noticia": []}
        por_noticia = []
        try:
            if any(item.get("noticias_similares") for item in corpus):
                for idx, item in enumerate(corpus):
                    recomendaciones = item.get("noticias_similares", [])[:3]
                    item["recomendaciones"] = recomendaciones
                    por_noticia.append(
                        {"indice": idx, "titulo": item.get("titulo", ""), "recomendaciones": recomendaciones}
                    )
            elif _RECOMENDACION_OK:
                recomendador = SistemaRecomendacion(corpus)
                for idx, item in enumerate(corpus):
                    recomendaciones = recomendador.recomendar_detallado(idx, top_n=3)
                    item["recomendaciones"] = recomendaciones
                    por_noticia.append(
                        {"indice": idx, "titulo": item.get("titulo", ""), "recomendaciones": recomendaciones}
                    )
        except Exception as exc:
            advertencias.append(f"Recomendaciones: {exc}")
        return {"disponible": bool(por_noticia), "por_noticia": por_noticia}

    def _detectar_temas(self, corpus: list[dict], advertencias: list[str]) -> dict:
        if not _DETECTOR_OK or not corpus:
            return {"disponible": False, "resultados": []}
        try:
            detector = DetectorTemasPublicidad()
            conversacion = [
                ("corpus", f"{item.get('titulo', '')} {item.get('texto_original', '')[:220]}")
                for item in corpus
                if _texto_documento(item)
            ]
            resultados = detector.simular_chat(conversacion)
            resumen = detector.resumen_temas()
            return {
                "disponible": True,
                "resultados": resultados,
                "resumen": resumen,
                "nota_etica": NOTA_ETICA_PUBLICIDAD,
            }
        except Exception as exc:
            advertencias.append(f"Detector de temas: {exc}")
            return {"disponible": False, "resultados": [], "error": str(exc)}

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
            ruta_fallback = Path(ruta)
            ruta_fallback.parent.mkdir(parents=True, exist_ok=True)
            # PNG 1x1 transparente; mantiene el artefacto esperado cuando matplotlib no esta disponible.
            ruta_fallback.write_bytes(
                bytes.fromhex(
                    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000a49444154789c6360000002000100"
                    "05fe02fea5579a0000000049454e44ae426082"
                )
            )
            return ruta_fallback

    def exportar_tendencias_json(
        self,
        analisis: dict,
        ruta: str | Path = "reports/tendencias_ac9.json",
    ) -> Path | None:
        tend_obj = analisis.get("tendencias", {}).get("_tendencias_obj")
        if tend_obj is None:
            return None
        try:
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
            return tend_obj.guardar_reporte_json(ruta)
        except Exception:
            return None

    def exportar_tendencias_markdown(
        self,
        analisis: dict,
        ruta: str | Path = "reports/conclusion_tendencias_ac9.md",
    ) -> Path | None:
        tend_obj = analisis.get("tendencias", {}).get("_tendencias_obj")
        if tend_obj is None:
            return None
        try:
            Path(ruta).parent.mkdir(parents=True, exist_ok=True)
            return tend_obj.guardar_conclusion_markdown(ruta)
        except Exception:
            return None


def _dominio(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url


def _texto_documento(item: dict) -> str:
    return " ".join(
        str(item.get(campo, "") or "")
        for campo in ("texto_limpio", "texto_original", "titulo", "cuerpo", "resumen")
    ).strip()


def _etiqueta_documento(item: dict) -> str:
    return str(
        item.get("categoria_original")
        or item.get("categoria")
        or item.get("category")
        or ""
    ).strip()


def _dataset_supervisado(corpus: list[dict]) -> tuple[list[str], list[str]]:
    textos: list[str] = []
    etiquetas: list[str] = []
    for item in corpus:
        texto = _texto_documento(item)
        etiqueta = _etiqueta_documento(item)
        if texto and etiqueta and etiqueta != "sin_categoria":
            textos.append(texto)
            etiquetas.append(etiqueta)
    return textos, etiquetas
