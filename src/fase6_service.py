from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib.query import ResultRow

from src.knowledge_graph import (
    QUERY_CONTEO_CATEGORIA,
    QUERY_NOTICIAS_METADATA,
    KnowledgeGraphSIMANW,
)


class Fase6Service:
    """Capa de Knowledge Graph RDF/SPARQL."""

    def __init__(self) -> None:
        self.kg = KnowledgeGraphSIMANW()
        self.errores: list[str] = []

    def construir_grafo(self, corpus_procesado: list[dict], analisis: dict | None = None) -> dict:
        self.kg = KnowledgeGraphSIMANW()
        self.errores = []
        try:
            noticias = [_normalizar_doc(doc) for doc in corpus_procesado]
            self.kg.construir_desde_noticias(noticias)
            self.kg.agregar_enlaces_externos_basicos()
            consultas = [
                {"nombre": "Noticias con metadata", "resultados": self.ejecutar_sparql(QUERY_NOTICIAS_METADATA)[:5]},
                {"nombre": "Conteo por categoria", "resultados": self.ejecutar_sparql(QUERY_CONTEO_CATEGORIA)[:5]},
            ]
            entidades = {
                "noticias": len(corpus_procesado),
                "categorias": len((analisis or {}).get("categorias", {})),
                "sentimientos": len((analisis or {}).get("sentimientos", {})),
            }
            return {
                "total_triples": self.kg.total_triples(),
                "formatos_exportados": [],
                "entidades": entidades,
                "consultas_ejemplo": consultas,
                "errores": list(self.errores),
            }
        except Exception as exc:
            self.errores.append(str(exc))
            return {
                "total_triples": self.kg.total_triples(),
                "formatos_exportados": [],
                "entidades": {},
                "consultas_ejemplo": [],
                "errores": list(self.errores),
            }

    def ejecutar_sparql(self, query: str) -> list[dict]:
        try:
            resultados = self.kg.consultar(query)
            return [_row_to_dict(row) for row in resultados]
        except Exception as exc:
            self.errores.append(f"SPARQL: {exc}")
            return []

    def exportar_ttl(self) -> Path:
        return self.kg.exportar_rdf("outputs/grafo/simanw_graph")["turtle"]

    def exportar_jsonld(self) -> Path:
        return self.kg.exportar_rdf("outputs/grafo/simanw_graph")["json-ld"]


def _normalizar_doc(doc: dict) -> dict:
    normalizado = dict(doc)
    normalizado["cuerpo"] = doc.get("cuerpo") or doc.get("texto_original") or doc.get("texto_limpio") or ""
    normalizado["categoria_original"] = doc.get("categoria_original") or doc.get("categoria") or "sin_categoria"
    normalizado["fuente"] = doc.get("fuente") or doc.get("fuente_nombre") or doc.get("url", "")
    return normalizado


def _row_to_dict(row: Any) -> dict:
    if isinstance(row, ResultRow):
        labels = [str(label) for label in row.labels]
        return {label: str(row[label]) for label in labels}
    if hasattr(row, "asdict"):
        return {str(k): str(v) for k, v in row.asdict().items()}
    return {"valor": str(row)}
