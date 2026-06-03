"""Capa de servicio para la Fase 2 de SIMANW — NLP.

Orquesta PipelineNLP y RepresentacionVectorial sobre las noticias
normalizadas producidas por Fase1Service. No duplica lógica NLP:
toda la transformación vive en los módulos src/pipeline_nlp.py y
src/representacion_vectorial.py.

Schema de cada item del corpus procesado:
    titulo, fecha, autor, categoria, url,
    texto_original, texto_limpio,
    tokens, terminos, stems,
    num_tokens, num_terminos, num_oraciones,
    vocabulario_unico, riqueza_lexica,
    terminos_relevantes
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from src.exportador import guardar_csv, guardar_json

try:
    from src.pipeline_nlp import PipelineNLP
    _PIPELINE_NLP_DISPONIBLE = True
except Exception:
    PipelineNLP = None  # type: ignore[assignment]
    _PIPELINE_NLP_DISPONIBLE = False

try:
    from src.representacion_vectorial import RepresentacionVectorial
    from src.similitud import CalculadorSimilitud
    _TFIDF_DISPONIBLE = True
except Exception:
    _TFIDF_DISPONIBLE = False

RUTA_JSON_DEFAULT = "data/processed/corpus_procesado.json"
RUTA_CSV_DEFAULT  = "data/processed/corpus_procesado.csv"

_TOP_TERMINOS = 8


@dataclass
class ResultadoFase2:
    corpus:       list[dict]
    estadisticas: dict
    errores:      list[str] = field(default_factory=list)


class Fase2Service:
    """Orquesta la Fase 2: NLP, TF-IDF y exportación del corpus procesado."""

    # ── procesamiento ─────────────────────────────────────────────────────────

    def procesar_corpus(self, noticias: list[dict]) -> ResultadoFase2:
        """Procesa las noticias de Fase 1 y devuelve el corpus enriquecido.

        No muta la lista original: trabaja sobre copias internas.
        Instancia PipelineNLP aquí para que la descarga de NLTK ocurra
        en el hilo worker y no bloquee la UI.
        """
        if not noticias:
            raise ValueError("No hay noticias para procesar. Ejecute la Fase 1 primero.")

        errores: list[str] = []

        # Copiar para no mutar los dicts de Fase 1
        copias = [dict(n) for n in noticias]

        # NLP: limpiar, tokenizar, stopwords, stemming
        if _PIPELINE_NLP_DISPONIBLE and PipelineNLP is not None:
            pipeline = PipelineNLP()
            nlp_results = pipeline.procesar_noticias(copias)
        else:
            pipeline = None
            errores.append("PipelineNLP no disponible; se usa tokenizacion simple sin NLTK.")
            nlp_results = [_nlp_basico(copia.get("cuerpo", "")) for copia in copias]
        # nlp_results[i] contiene: limpio, tokens, sin_stopwords, stems,
        #                           num_oraciones, vocabulario_unico, riqueza_lexica
        # copias[i]["nlp"] ha sido mutado por procesar_noticias (en la copia, no en el original)

        # TF-IDF: términos relevantes por documento
        repr_vectorial = None
        tfidf_ok = False
        if _TFIDF_DISPONIBLE:
            try:
                textos_limpios = [r["limpio"] for r in nlp_results]
                repr_vectorial = RepresentacionVectorial(max_features=1000)
                repr_vectorial.construir_matriz(textos_limpios)
                tfidf_ok = True
            except Exception as exc:
                errores.append(f"TF-IDF no disponible: {exc}")
        else:
            errores.append(
                "RepresentacionVectorial no disponible (scipy no instalado). "
                "terminos_relevantes quedará vacío."
            )

        # Construir corpus enriquecido
        corpus: list[dict] = []
        for idx, (copia, nlp) in enumerate(zip(copias, nlp_results)):
            terminos_relevantes: list[str] = []
            if tfidf_ok and repr_vectorial is not None:
                try:
                    terminos_relevantes = [
                        t for t, _ in repr_vectorial.top_terminos_documento(idx, n=_TOP_TERMINOS)
                    ]
                except Exception:
                    pass

            corpus.append({
                "titulo":            copia.get("titulo", ""),
                "fecha":             copia.get("fecha", ""),
                "autor":             copia.get("autor", ""),
                "categoria":         copia.get("categoria", ""),
                "url":               copia.get("url", ""),
                "texto_original":    copia.get("cuerpo", ""),
                "texto_limpio":      nlp["limpio"],
                "tokens":            nlp["tokens"],
                "terminos":          nlp["sin_stopwords"],
                "stems":             nlp["stems"],
                "num_tokens":        len(nlp["tokens"]),
                "num_terminos":      len(nlp["sin_stopwords"]),
                "num_oraciones":     nlp["num_oraciones"],
                "vocabulario_unico": nlp["vocabulario_unico"],
                "riqueza_lexica":    round(nlp["riqueza_lexica"], 4),
                "terminos_relevantes": terminos_relevantes,
            })

        # Estadísticas: pasar nlp_results (no corpus) a estadisticas_corpus
        if pipeline is not None:
            estadisticas = pipeline.estadisticas_corpus(nlp_results)
        else:
            estadisticas = _estadisticas_basicas(nlp_results)
        if tfidf_ok and repr_vectorial is not None:
            estadisticas.update(repr_vectorial.info_matriz())
            try:
                calculador = CalculadorSimilitud(repr_vectorial.matriz)
                grupos = calculador.agrupar_por_similitud(umbral=0.15)
                pares_similares = []
                for idx, item in enumerate(corpus):
                    similares = [
                        {
                            "indice": sim_idx,
                            "titulo": corpus[sim_idx]["titulo"],
                            "similitud": round(score, 4),
                        }
                        for sim_idx, score in calculador.documentos_similares(idx, top_n=3)
                        if score > 0
                    ]
                    item["noticias_similares"] = similares
                    pares_similares.append({"indice": idx, "titulo": item["titulo"], "similares": similares})
                estadisticas["grupos_similares"] = grupos
                estadisticas["pares_similares"] = pares_similares
            except Exception as exc:
                errores.append(f"Similitud coseno no disponible: {exc}")
                estadisticas["grupos_similares"] = []
                estadisticas["pares_similares"] = []
        else:
            for item in corpus:
                item["noticias_similares"] = []
            estadisticas["grupos_similares"] = []
            estadisticas["pares_similares"] = []

        return ResultadoFase2(corpus=corpus, estadisticas=estadisticas, errores=errores)

    # ── estadísticas y frecuencias ────────────────────────────────────────────

    def obtener_estadisticas(self, corpus: list[dict]) -> dict:
        """Recomputa estadísticas a partir del corpus ya procesado."""
        if not corpus:
            return {}
        total_tokens   = sum(item["num_tokens"]   for item in corpus)
        total_terminos = sum(item["num_terminos"]  for item in corpus)
        vocab: set[str] = set()
        for item in corpus:
            vocab.update(item["terminos"])
        avg_riqueza = sum(item["riqueza_lexica"] for item in corpus) / len(corpus)
        return {
            "total_documentos":       len(corpus),
            "total_tokens":           total_tokens,
            "total_terminos":         total_terminos,
            "vocabulario_total":      len(vocab),
            "promedio_riqueza_lexica": round(avg_riqueza, 4),
            "promedio_tokens_doc":    round(total_tokens / len(corpus), 1),
        }

    def obtener_frecuencias(
        self, corpus: list[dict], top_n: int = 20
    ) -> list[tuple[str, int]]:
        """Devuelve los N términos más frecuentes del corpus."""
        contador: Counter[str] = Counter()
        for item in corpus:
            contador.update(item["terminos"])
        return contador.most_common(top_n)

    # ── exportación ───────────────────────────────────────────────────────────

    def exportar_json(
        self, corpus: list[dict], ruta: str | Path | None = None
    ) -> Path:
        return guardar_json(corpus, Path(ruta or RUTA_JSON_DEFAULT))

    def exportar_csv(
        self, corpus: list[dict], ruta: str | Path | None = None
    ) -> Path:
        filas = [_aplanar_fila(item) for item in corpus]
        return guardar_csv(filas, Path(ruta or RUTA_CSV_DEFAULT))

    def exportar_todo(self, corpus: list[dict]) -> dict[str, Path]:
        return {
            "json": self.exportar_json(corpus),
            "csv":  self.exportar_csv(corpus),
        }


# ── helpers ───────────────────────────────────────────────────────────────────

def _aplanar_fila(item: dict) -> dict:
    """Convierte listas a strings legibles antes de escribir el CSV."""
    return {
        "titulo":             item["titulo"],
        "fecha":              item["fecha"],
        "autor":              item["autor"],
        "categoria":          item["categoria"],
        "url":                item["url"],
        "texto_original":     item["texto_original"],
        "texto_limpio":       item["texto_limpio"],
        "tokens":             " ".join(item["tokens"][:50]),
        "terminos":           " | ".join(item["terminos"][:30]),
        "stems":              " | ".join(item["stems"][:30]),
        "num_tokens":         item["num_tokens"],
        "num_terminos":       item["num_terminos"],
        "num_oraciones":      item["num_oraciones"],
        "vocabulario_unico":  item["vocabulario_unico"],
        "riqueza_lexica":     item["riqueza_lexica"],
        "terminos_relevantes": ", ".join(item["terminos_relevantes"]),
    }


def _nlp_basico(texto: str) -> dict:
    limpio = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]", " ", str(texto).lower())
    limpio = re.sub(r"\s+", " ", limpio).strip()
    tokens = re.findall(r"\b[\wáéíóúñü]+\b", limpio, flags=re.IGNORECASE)
    stop = {
        "de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "que",
        "con", "por", "para", "del", "al", "se", "es", "son", "como",
    }
    terminos = [token for token in tokens if len(token) > 2 and token not in stop]
    return {
        "limpio": limpio,
        "tokens": tokens,
        "sin_stopwords": terminos,
        "stems": terminos,
        "num_oraciones": max(len(re.findall(r"[.!?]+", str(texto))), 1 if texto else 0),
        "vocabulario_unico": len(set(terminos)),
        "riqueza_lexica": len(set(terminos)) / max(len(terminos), 1),
    }


def _estadisticas_basicas(nlp_results: list[dict]) -> dict:
    total_tokens = sum(len(item.get("tokens", [])) for item in nlp_results)
    vocab = set()
    stems = set()
    for item in nlp_results:
        vocab.update(item.get("sin_stopwords", []))
        stems.update(item.get("stems", []))
    total_docs = len(nlp_results)
    return {
        "total_documentos": total_docs,
        "total_tokens": total_tokens,
        "vocabulario_total": len(vocab),
        "stems_unicos": len(stems),
        "promedio_tokens_doc": round(total_tokens / max(total_docs, 1), 1),
    }
