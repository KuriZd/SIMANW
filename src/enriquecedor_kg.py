from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from rdflib import Graph, Literal, Namespace, RDFS, OWL, URIRef
from rdflib.namespace import DCTERMS, SKOS, XSD


class EnriquecedorKG:
    """
    AC-7: Enriquece el KG local conectando entidades con Wikidata.

    Acepta una instancia KnowledgeGraphSIMANW (que expone .graph)
    o directamente un rdflib.Graph.
    """

    def __init__(self, knowledge_graph, wikidata_client: Callable[[str], list[dict]] | None = None) -> None:
        if isinstance(knowledge_graph, Graph):
            self._graph_obj = knowledge_graph
            self.kg = None
        else:
            self._graph_obj = knowledge_graph.graph
            self.kg = knowledge_graph

        self.WD = Namespace("http://www.wikidata.org/entity/")
        self.WDT = Namespace("http://www.wikidata.org/prop/direct/")
        self.DATA = Namespace("http://simanw.org/data/")
        self.SCHEMA = Namespace("http://schema.org/")
        self.SIMANW = Namespace("http://simanw.org/ontology/")
        self.PROV = Namespace("http://www.w3.org/ns/prov#")
        self.ENDPOINT = "https://query.wikidata.org/sparql"
        self._wikidata_client = wikidata_client

        self._graph_obj.bind("wd", self.WD)
        self._graph_obj.bind("wdt", self.WDT)
        self._graph_obj.bind("skos", SKOS)
        self._graph_obj.bind("owl", OWL)
        self._graph_obj.bind("data", self.DATA)
        self._graph_obj.bind("schema", self.SCHEMA)
        self._graph_obj.bind("simanw", self.SIMANW)
        self._graph_obj.bind("prov", self.PROV)

        self.enlaces_externos: list[dict] = []
        self.errores: list[str] = []

    # ------------------------------------------------------------------
    # Enlace y enriquecimiento
    # ------------------------------------------------------------------

    def enlazar_entidad(self, entidad_local, wikidata_id: str, etiqueta: str, usar_same_as: bool = True) -> None:
        """Agrega owl:sameAs, skos:exactMatch y rdfs:label para la entidad Wikidata."""
        if not wikidata_id or not wikidata_id.strip():
            return
        wikidata_id = wikidata_id.strip()
        if not re.fullmatch(r"Q\d+", wikidata_id):
            raise ValueError(f"QID Wikidata invalido: {wikidata_id}")
        entidad_wikidata = self.WD[wikidata_id]
        if usar_same_as:
            self._graph_obj.add((entidad_local, OWL.sameAs, entidad_wikidata))
        self._graph_obj.add((entidad_local, SKOS.exactMatch, entidad_wikidata))
        self._graph_obj.add((entidad_wikidata, RDFS.label, Literal(etiqueta or wikidata_id, lang="es")))
        self._graph_obj.add((entidad_local, self.SIMANW.wikidataQID, Literal(wikidata_id)))
        self._graph_obj.add((entidad_local, DCTERMS.source, URIRef(self.ENDPOINT)))
        self._graph_obj.add((entidad_local, self.PROV.wasDerivedFrom, entidad_wikidata))
        self._graph_obj.add((entidad_local, DCTERMS.modified, Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime)))
        self.enlaces_externos.append({
            "local": str(entidad_local),
            "wikidata": wikidata_id,          # clave preservada para compatibilidad con tests
            "wikidata_id": wikidata_id,
            "wikidata_uri": str(entidad_wikidata),
            "etiqueta": etiqueta,
            "relacion": "owl:sameAs" if usar_same_as else "skos:exactMatch",
            "procedencia": self.ENDPOINT,
        })

    def agregar_datos_externos(self, entidad_local, propiedades: dict[str, str]) -> None:
        """Agrega propiedades Wikidata (wdt:Pxxx) al grafo como literales."""
        for propiedad, valor in (propiedades or {}).items():
            self._graph_obj.add((entidad_local, self.WDT[propiedad], Literal(str(valor))))

    # ------------------------------------------------------------------
    # Consultas SPARQL locales
    # ------------------------------------------------------------------

    def consulta_enriquecimiento(self) -> list:
        """SPARQL local: retorna tripletas (local, externo, etiqueta) enlazadas."""
        query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT DISTINCT ?local ?externo ?etiqueta
        WHERE {
            { ?local owl:sameAs ?externo . }
            UNION
            { ?local skos:exactMatch ?externo . }
            ?externo rdfs:label ?etiqueta .
        }
        ORDER BY ?local
        """
        return list(self._graph_obj.query(query))

    def entidades_locales_enriquecibles(self, limite: int = 8) -> list[dict]:
        """Extrae categorias/autores/fuentes reales del KG local para enlazar."""
        query = """
        PREFIX simanw: <http://simanw.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>

        SELECT DISTINCT ?entidad ?tipo ?label WHERE {
            {
                ?entidad a simanw:Categoria ;
                         rdfs:label ?label .
                BIND("categoria" AS ?tipo)
            }
            UNION
            {
                ?entidad a simanw:Fuente ;
                         rdfs:label ?label .
                BIND("fuente" AS ?tipo)
            }
        }
        ORDER BY ?tipo ?label
        """
        entidades = []
        for row in self._graph_obj.query(query):
            entidades.append({"uri": row.entidad, "tipo": str(row.tipo), "label": str(row.label)})
            if len(entidades) >= limite:
                break
        return entidades

    def enriquecer_desde_wikidata(self, limite_entidades: int = 8) -> dict:
        """Busca entidades reales del KG local en Wikidata y agrega enlaces validados."""
        triples_antes = len(self._graph_obj)
        entidades = self.entidades_locales_enriquecibles(limite=limite_entidades)
        evaluadas = 0
        rechazadas: list[dict] = []

        for entidad in entidades:
            evaluadas += 1
            candidatos = self.consultar_wikidata(self.buscar_entidad_wikidata(entidad["label"]))
            if not candidatos:
                rechazadas.append({"label": entidad["label"], "motivo": "sin_resultados"})
                continue
            candidato = self._seleccionar_candidato_validado(entidad["label"], candidatos)
            if not candidato:
                rechazadas.append({"label": entidad["label"], "motivo": "sin_candidato_validado"})
                continue
            self.enlazar_entidad(
                entidad["uri"],
                candidato["qid"],
                candidato["label"],
                usar_same_as=candidato["confianza"] >= 0.98,
            )
            if candidato.get("description"):
                self._graph_obj.add((self.WD[candidato["qid"]], self.SCHEMA.description, Literal(candidato["description"], lang="es")))

        return {
            "actividad": "AC-7",
            "estado": "completo" if self.enlaces_externos else "parcial",
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "endpoint": self.ENDPOINT,
            "entidades_evaluadas": evaluadas,
            "total_enlaces_externos": len(self.enlaces_externos),
            "triples_antes": triples_antes,
            "triples_despues": len(self._graph_obj),
            "enlaces_externos": self.enlaces_externos,
            "rechazadas": rechazadas,
            "errores": self.errores,
            "validacion": "Etiqueta local normalizada debe coincidir con etiqueta Wikidata normalizada.",
        }

    # ------------------------------------------------------------------
    # Generacion de consultas para Wikidata
    # ------------------------------------------------------------------

    def generar_query_wikidata(self, tema: str) -> str:
        """Devuelve SPARQL sugerida para el tema dado. Tema desconocido retorna aviso."""
        queries = {
            "tecnologia": """
# Consulta: Herramientas de NLP en Wikidata
SELECT ?item ?itemLabel ?description WHERE {
  ?item wdt:P31 wd:Q7397 .
  ?item wdt:P366 wd:Q30642 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
LIMIT 10""",
            "ciencia": """
# Consulta: Investigaciones sobre cambio climatico
SELECT ?item ?itemLabel ?date WHERE {
  ?item wdt:P31 wd:Q13442814 .
  ?item wdt:P921 wd:Q7942 .
  ?item wdt:P577 ?date .
  FILTER(YEAR(?date) >= 2024)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
LIMIT 10""",
            "economia": """
# Consulta: Conceptos economicos relacionados
SELECT ?item ?itemLabel ?description WHERE {
  ?item wdt:P279* wd:Q159810 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
LIMIT 10""",
            "gobierno": """
# Consulta: Entidades gubernamentales y politica publica
SELECT ?item ?itemLabel ?pais WHERE {
  ?item wdt:P31 wd:Q7188 .
  OPTIONAL { ?item wdt:P17 ?pais . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
LIMIT 10""",
            "salud": """
# Consulta: Enfermedades y tratamientos medicos
SELECT ?item ?itemLabel ?description WHERE {
  ?item wdt:P279* wd:Q12136 .
  OPTIONAL { ?item schema:description ?description FILTER(LANG(?description) = "es") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
LIMIT 10""",
            "medio_ambiente": """
# Consulta: Problemas medioambientales y cambio climatico
SELECT ?item ?itemLabel ?description WHERE {
  ?item wdt:P279* wd:Q2001 .
  OPTIONAL { ?item schema:description ?description FILTER(LANG(?description) = "es") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }
}
LIMIT 10""",
        }
        return queries.get(
            tema.lower().strip(),
            f"# No hay consulta predefinida para este tema: {tema}",
        )

    # ------------------------------------------------------------------
    # Consulta opcional al endpoint real de Wikidata
    # ------------------------------------------------------------------

    def consultar_wikidata(self, query: str) -> list[dict]:
        """Consulta Wikidata via SPARQLWrapper. Retorna [] si no hay conexion o modulo."""
        if self._wikidata_client is not None:
            return self._wikidata_client(query)
        if os.environ.get("SIMANW_WIKIDATA_ONLINE") != "1":
            self.errores.append("Consulta Wikidata online deshabilitada; define SIMANW_WIKIDATA_ONLINE=1 para ejecutar el endpoint real.")
            return []
        try:
            from SPARQLWrapper import JSON, SPARQLWrapper  # type: ignore[import]
        except ImportError:
            self.errores.append("SPARQLWrapper no instalado")
            return []

        try:
            sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(5)
            sparql.addCustomHTTPHeader("User-Agent", "SIMANW-AC7/1.0 (educational)")
            resultados = sparql.query().convert()
            bindings = resultados.get("results", {}).get("bindings", [])
            return [{var: b[var]["value"] for var in b} for b in bindings]
        except Exception as exc:
            self.errores.append(f"Wikidata: {exc}")
            return []

    def buscar_entidad_wikidata(self, nombre_entidad: str, idioma: str = "es") -> str:
        """Genera SPARQL para buscar candidatos Wikidata por etiqueta de texto."""
        nombre_escapado = nombre_entidad.replace('"', '\\"')
        return (
            f'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n'
            f'PREFIX schema: <http://schema.org/>\n'
            f'SELECT ?item ?itemLabel ?description WHERE {{\n'
            f'  ?item rdfs:label "{nombre_escapado}"@{idioma} .\n'
            f'  OPTIONAL {{\n'
            f'    ?item schema:description ?description\n'
            f'    FILTER(LANG(?description) = "{idioma}")\n'
            f'  }}\n'
            f'  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{idioma},en". }}\n'
            f'}}\n'
            f'LIMIT 10'
        )

    @staticmethod
    def _seleccionar_candidato_validado(nombre_local: str, candidatos: list[dict]) -> dict | None:
        objetivo = _normalizar_texto(nombre_local)
        for candidato in candidatos:
            item = candidato.get("item", "")
            qid = item.rsplit("/", 1)[-1]
            label = candidato.get("itemLabel", "") or candidato.get("label", "")
            if not re.fullmatch(r"Q\d+", qid):
                continue
            normalizado = _normalizar_texto(label)
            if normalizado == objetivo:
                return {
                    "qid": qid,
                    "label": label,
                    "description": candidato.get("description", ""),
                    "confianza": 1.0,
                }
        return None

    # ------------------------------------------------------------------
    # Exportacion
    # ------------------------------------------------------------------

    def guardar_grafo(self, ruta: str | Path) -> None:
        """Serializa el grafo enriquecido a Turtle."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(self._graph_obj.serialize(format="turtle"), encoding="utf-8")

    def guardar_reporte_json(self, ruta: str | Path) -> None:
        """Exporta reporte JSON con enlaces externos y consultas SPARQL sugeridas."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temas = ["tecnologia", "ciencia", "economia", "gobierno", "salud", "medio_ambiente"]
        payload = {
            "actividad": "AC-7",
            "descripcion": "Enriquecimiento del Knowledge Graph local con Wikidata",
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "total_triples": len(self._graph_obj),
            "total_enlaces_externos": len(self.enlaces_externos),
            "enlaces_externos": self.enlaces_externos,
            "endpoint": self.ENDPOINT,
            "errores": self.errores,
            "consultas_sugeridas": {t: self.generar_query_wikidata(t).strip() for t in temas},
        }
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(payload, archivo, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------
# Funciones de modulo
# ------------------------------------------------------------------

def crear_uri_entidad(nombre: str) -> str:
    """Convierte un nombre libre en una URI estable del espacio DATA de SIMANW."""
    DATA = Namespace("http://simanw.org/data/")
    return str(DATA[_slug(nombre)])


def cargar_grafo_desde_turtle(ruta: str | Path) -> Graph:
    """Carga un grafo RDF existente desde Turtle."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo Turtle no encontrado: {ruta}")
    g = Graph()
    g.parse(str(ruta), format="turtle")
    return g


def crear_grafo_demo() -> Graph:
    """Crea un rdflib.Graph minimo con noticias de demostración para AC-7."""
    from rdflib import RDF, XSD
    from rdflib.namespace import DC, FOAF

    g = Graph()
    NS = Namespace("http://simanw.org/ontology/")
    DATA = Namespace("http://simanw.org/data/")
    g.bind("simanw", NS)
    g.bind("data", DATA)
    g.bind("dc", DC)
    g.bind("foaf", FOAF)
    g.bind("owl", OWL)
    g.bind("skos", SKOS)

    noticias = [
        ("noticia_1", "IA en tecnologia", "tecnologia", "2026-05-10", "Maria Garcia"),
        ("noticia_2", "Mercados y economia", "economia", "2026-05-09", "Carlos Ruiz"),
        ("noticia_3", "Ciencia y clima", "ciencia", "2026-05-08", "Ana Torres"),
        ("noticia_4", "Gobierno y datos abiertos", "gobierno", "2026-05-07", "Luis Perez"),
    ]
    for nid, titulo, categoria, fecha, autor in noticias:
        uri = DATA[nid]
        g.add((uri, RDF.type, NS.Noticia))
        g.add((uri, DC.title, Literal(titulo, lang="es")))
        g.add((uri, DC.date, Literal(fecha, datatype=XSD.date)))

        autor_uri = DATA[f"autor_{_slug(autor)}"]
        g.add((autor_uri, RDF.type, NS.Autor))
        g.add((autor_uri, FOAF.name, Literal(autor)))
        g.add((uri, NS.tieneAutor, autor_uri))

        cat_uri = DATA[f"categoria_{_slug(categoria)}"]
        g.add((cat_uri, RDF.type, NS.Categoria))
        g.add((cat_uri, RDFS.label, Literal(categoria, lang="es")))
        g.add((uri, NS.tieneCategoria, cat_uri))

    return g


def enriquecer_categorias_demo(knowledge_graph) -> "EnriquecedorKG":
    """Enlaza las cuatro categorias principales del KG con Wikidata."""
    enriquecedor = EnriquecedorKG(knowledge_graph)
    data = knowledge_graph.DATA

    enriquecedor.enlazar_entidad(data["categoria_tecnologia"], "Q11016", "Tecnologia de la informacion")
    enriquecedor.enlazar_entidad(data["categoria_economia"], "Q159810", "Economia")
    enriquecedor.enlazar_entidad(data["categoria_ciencia"], "Q336", "Ciencia")
    enriquecedor.enlazar_entidad(data["categoria_politica"], "Q7163", "Politica")

    enriquecedor.agregar_datos_externos(
        data["categoria_tecnologia"],
        {
            "P279": "Sector economico terciario",
            "P910": "Categoria: Tecnologia de la informacion",
        },
    )
    return enriquecedor


def _slug(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", str(texto).lower())
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "_", sin_acentos).strip("_")
    return slug or "sin_valor"


def _normalizar_texto(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", str(texto).lower())
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]+", " ", sin_acentos)).strip()
