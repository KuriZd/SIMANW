from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rdflib.query import ResultRow

from src.enriquecedor_kg import EnriquecedorKG
from src.knowledge_graph import (
    QUERY_AC13_AUTORES_PRODUCTIVOS,
    QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
    QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
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
            evidencia_ac7 = self.enriquecer_con_wikidata()
            consultas = [
                {"nombre": "Noticias con metadata", "resultados": self.ejecutar_sparql(QUERY_NOTICIAS_METADATA)[:5]},
                {"nombre": "Conteo por categoria", "resultados": self.ejecutar_sparql(QUERY_CONTEO_CATEGORIA)[:5]},
                {"nombre": "Enlaces Wikidata", "resultados": self.ejecutar_sparql(QUERY_ENLACES_WIKIDATA)[:5]},
            ]
            entidades = {
                "noticias": len(corpus_procesado),
                "categorias": len((analisis or {}).get("categorias", {})),
                "sentimientos": len((analisis or {}).get("sentimientos", {})),
                "enlaces_wikidata": evidencia_ac7.get("total_enlaces_externos", 0),
            }
            return {
                "total_triples": self.kg.total_triples(),
                "formatos_exportados": [],
                "entidades": entidades,
                "consultas_ejemplo": consultas,
                "evidencia_ac7": evidencia_ac7,
                "errores": list(self.errores),
            }
        except Exception as exc:
            self.errores.append(str(exc))
            return {
                "total_triples": self.kg.total_triples(),
                "formatos_exportados": [],
                "entidades": {},
                "consultas_ejemplo": [],
                "evidencia_ac7": {},
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

    def enriquecer_con_wikidata(self) -> dict:
        enriquecedor = EnriquecedorKG(self.kg)
        evidencia = enriquecedor.enriquecer_desde_wikidata()
        ruta_ttl = Path("data/kg_enriquecido_ac7.ttl")
        ruta_json = Path("data/enlaces_wikidata_ac7.json")
        enriquecedor.guardar_grafo(ruta_ttl)
        enriquecedor.guardar_reporte_json(ruta_json)
        evidencia["archivo_ttl"] = str(ruta_ttl)
        evidencia["archivo_json"] = str(ruta_json)
        if evidencia.get("errores") and not evidencia.get("total_enlaces_externos"):
            evidencia["observacion"] = "No se crearon enlaces porque Wikidata no respondio o no hubo coincidencias validadas."
        return evidencia

    def publicar_semanticamente(self) -> dict:
        rutas_rdf = self.kg.exportar_rdf("data/ac13_simanw")
        enlaces = self.kg.agregar_enlaces_externos_basicos()
        validacion = self.kg.validar_con_shacl()
        if validacion.get("error"):
            validacion = {
                **self.kg.validar_formas(),
                "mecanismo": "validacion_interna_equivalente",
                "observacion": validacion["error"],
            }

        consultas = {
            "autores_productivos": self.ejecutar_sparql(QUERY_AC13_AUTORES_PRODUCTIVOS),
            "sentimiento_por_categoria": self.ejecutar_sparql(QUERY_AC13_SENTIMIENTO_POR_CATEGORIA),
            "noticias_recientes_negativas": self.ejecutar_sparql(QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS),
        }
        glosario = self.kg.glosario_ontologia()
        fragmento = self.kg.fragmento_jsonld_noticia(1)

        ruta_glosario = Path("reports/glosario_ac13.json")
        ruta_fragmento = Path("data/ac13_fragmento_noticia.jsonld")
        ruta_validacion = Path("reports/validacion_shacl_ac13.json")
        ruta_consultas = Path("reports/consultas_sparql_ac13.json")
        ruta_reutilizacion = Path("reports/reutilizacion_datos_ac13.md")
        for ruta in (ruta_glosario, ruta_fragmento, ruta_validacion, ruta_consultas, ruta_reutilizacion):
            ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta_glosario.write_text(json.dumps(glosario, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_fragmento.write_text(json.dumps(fragmento, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_validacion.write_text(json.dumps(validacion, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        ruta_consultas.write_text(json.dumps(consultas, ensure_ascii=False, indent=2), encoding="utf-8")
        ruta_reutilizacion.write_text(
            "\n".join(
                [
                    "# AC-13: Descubrimiento y reutilizacion de datos",
                    "",
                    self.kg.nota_reutilizacion_datos(),
                    "",
                    "## Criterio de enlace externo",
                    "",
                    "Los enlaces de clases usan equivalencias con vocabularios ampliamente adoptados "
                    "cuando la semantica coincide, como schema:NewsArticle y foaf:Person. Los enlaces "
                    "de categorias usan skos:closeMatch porque representan correspondencias tematicas "
                    "aproximadas con Wikidata o DBpedia y no identidad estricta.",
                ]
            ),
            encoding="utf-8",
        )

        violaciones = validacion.get("violaciones", [])
        return {
            "actividad": "AC-13",
            "estado": "completo" if validacion.get("conforme") else "parcial",
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Knowledge Graph",
            "formatos_generados": ["turtle", "json-ld"],
            "resultado_shacl": validacion,
            "violaciones_encontradas": len(violaciones) if isinstance(violaciones, list) else 0,
            "correcciones_aplicadas": "Sin violaciones formales detectadas." if validacion.get("conforme") else "Revisar reporte de validacion.",
            "consultas_sparql_ejecutadas": {clave: len(valor) for clave, valor in consultas.items()},
            "enlaces_externos_creados": len(enlaces),
            "criterio_enlace": "owl:equivalentClass para clases equivalentes; skos:closeMatch para categorias tematicas aproximadas.",
            "fragmento_jsonld": fragmento,
            "glosario_generado": str(ruta_glosario),
            "nota_reutilizacion": str(ruta_reutilizacion),
            "archivos": {
                "turtle": str(rutas_rdf["turtle"]),
                "jsonld": str(rutas_rdf["json-ld"]),
                "validacion": str(ruta_validacion),
                "glosario": str(ruta_glosario),
                "fragmento_jsonld": str(ruta_fragmento),
                "consultas_sparql": str(ruta_consultas),
                "reutilizacion": str(ruta_reutilizacion),
            },
            "archivo_json": str(ruta_validacion),
        }


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


QUERY_ENLACES_WIKIDATA = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?local ?externo ?etiqueta
WHERE {
    { ?local skos:exactMatch ?externo . }
    UNION
    { ?local owl:sameAs ?externo . }
    OPTIONAL { ?externo rdfs:label ?etiqueta . }
}
ORDER BY ?local
"""
