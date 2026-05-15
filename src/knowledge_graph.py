from __future__ import annotations

import re
import unicodedata
from typing import Any

from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, XSD
from rdflib.namespace import DC, DCTERMS, FOAF


QUERY_NOTICIAS_METADATA = """
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?titulo ?autor ?categoria ?fecha
WHERE {
    ?noticia a simanw:Noticia ;
             dc:title ?titulo ;
             dc:date ?fecha ;
             simanw:tieneAutor ?autorURI ;
             simanw:tieneCategoria ?catURI .
    ?autorURI foaf:name ?autor .
    ?catURI rdfs:label ?categoria .
}
ORDER BY DESC(?fecha)
"""

QUERY_SENTIMIENTO_NEGATIVO = """
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?titulo ?score ?etiqueta
WHERE {
    ?noticia a simanw:Noticia ;
             dc:title ?titulo ;
             simanw:sentimientoScore ?score ;
             simanw:sentimientoEtiqueta ?etiqueta .
    FILTER(?score < -0.05)
}
ORDER BY ?score
"""

QUERY_CONTEO_CATEGORIA = """
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?categoria (COUNT(?noticia) as ?total)
WHERE {
    ?noticia a simanw:Noticia ;
             simanw:tieneCategoria ?catURI .
    ?catURI rdfs:label ?categoria .
}
GROUP BY ?categoria
ORDER BY DESC(?total)
"""

QUERY_AUTORES_PRODUCTIVIDAD = """
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?autor (COUNT(?n) as ?publicaciones) (GROUP_CONCAT(?titulo; separator="; ") as ?titulos)
WHERE {
    ?n a simanw:Noticia ;
       dc:title ?titulo ;
       simanw:tieneAutor ?a .
    ?a foaf:name ?autor .
}
GROUP BY ?autor
"""

QUERY_WIKIDATA_SOFTWARE_IA_PYTHON = """
SELECT ?item ?itemLabel ?description WHERE {
  ?item wdt:P31 wd:Q7397;
        wdt:P277 wd:Q28865;
        wdt:P366 wd:Q11660.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es". }
}
LIMIT 10
"""

QUERY_DBPEDIA_HERRAMIENTAS_NLP = """
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?descripcion WHERE {
  ?s dbo:genre dbr:Natural_language_processing ;
     rdfs:label ?nombre ;
     rdfs:comment ?descripcion .
  FILTER(LANG(?nombre) = 'es')
  FILTER(LANG(?descripcion) = 'es')
}
LIMIT 5
"""


class KnowledgeGraphSIMANW:
    """Knowledge Graph semantico del sistema SIMANW."""

    def __init__(self) -> None:
        self.graph = Graph()
        self.NS = Namespace("http://simanw.org/ontology/")
        self.DATA = Namespace("http://simanw.org/data/")
        self.graph.bind("simanw", self.NS)
        self.graph.bind("data", self.DATA)
        self.graph.bind("dc", DC)
        self.graph.bind("dcterms", DCTERMS)
        self.graph.bind("foaf", FOAF)
        self._definir_ontologia()

    def _definir_ontologia(self) -> None:
        """Define la ontologia del SIMANW."""
        for clase in [self.NS.Noticia, self.NS.Autor, self.NS.Categoria, self.NS.Fuente]:
            self.graph.add((clase, RDF.type, OWL.Class))

        propiedades_objeto = [
            self.NS.tieneAutor,
            self.NS.tieneCategoria,
            self.NS.provieneDe,
            self.NS.relacionadaCon,
        ]
        for propiedad in propiedades_objeto:
            self.graph.add((propiedad, RDF.type, OWL.ObjectProperty))

        self.graph.add((self.NS.tieneAutor, RDFS.domain, self.NS.Noticia))
        self.graph.add((self.NS.tieneAutor, RDFS.range, self.NS.Autor))
        self.graph.add((self.NS.tieneCategoria, RDFS.domain, self.NS.Noticia))
        self.graph.add((self.NS.tieneCategoria, RDFS.range, self.NS.Categoria))
        self.graph.add((self.NS.provieneDe, RDFS.domain, self.NS.Noticia))
        self.graph.add((self.NS.provieneDe, RDFS.range, self.NS.Fuente))

        propiedades_datos = [
            self.NS.sentimientoScore,
            self.NS.sentimientoEtiqueta,
            self.NS.urlOriginal,
        ]
        for propiedad in propiedades_datos:
            self.graph.add((propiedad, RDF.type, OWL.DatatypeProperty))

    def agregar_noticia(self, noticia: dict, noticia_id: int) -> None:
        """Agrega una noticia procesada al knowledge graph."""
        uri = self.DATA[f"noticia_{noticia_id}"]
        self.graph.add((uri, RDF.type, self.NS.Noticia))
        self.graph.add((uri, DC.title, Literal(noticia["titulo"], lang="es")))
        self.graph.add((uri, DC.description, Literal(noticia["cuerpo"][:200], lang="es")))
        self.graph.add((uri, DC.date, Literal(noticia["fecha"], datatype=XSD.date)))

        autor = noticia.get("autor", "Autor desconocido")
        autor_uri = self.DATA[f"autor_{_slug(autor)}"]
        self.graph.add((autor_uri, RDF.type, self.NS.Autor))
        self.graph.add((autor_uri, FOAF.name, Literal(autor)))
        self.graph.add((uri, self.NS.tieneAutor, autor_uri))

        categoria = noticia.get("categoria_predicha", noticia.get("categoria_original", "general"))
        categoria_uri = self.DATA[f"categoria_{_slug(categoria)}"]
        self.graph.add((categoria_uri, RDF.type, self.NS.Categoria))
        self.graph.add((categoria_uri, RDFS.label, Literal(categoria, lang="es")))
        self.graph.add((uri, self.NS.tieneCategoria, categoria_uri))

        fuente = noticia.get("fuente")
        if fuente:
            fuente_uri = self.DATA[f"fuente_{_slug(fuente)}"]
            self.graph.add((fuente_uri, RDF.type, self.NS.Fuente))
            self.graph.add((fuente_uri, RDFS.label, Literal(fuente)))
            self.graph.add((uri, self.NS.provieneDe, fuente_uri))

        sentimiento = noticia.get("sentimiento")
        if sentimiento:
            self.graph.add(
                (uri, self.NS.sentimientoScore, Literal(sentimiento["compound"], datatype=XSD.float))
            )
            self.graph.add((uri, self.NS.sentimientoEtiqueta, Literal(sentimiento["etiqueta"])))

        if "url" in noticia:
            self.graph.add((uri, self.NS.urlOriginal, Literal(noticia["url"], datatype=XSD.anyURI)))

    def construir_desde_noticias(self, noticias: list[dict]) -> None:
        for indice, noticia in enumerate(noticias, start=1):
            self.agregar_noticia(noticia, indice)

    def consultar(self, sparql_query: str) -> list[Any]:
        """Ejecuta una consulta SPARQL."""
        return list(self.graph.query(sparql_query))

    def total_triples(self) -> int:
        return len(self.graph)

    def serializar(self, formato: str = "turtle") -> str:
        return self.graph.serialize(format=formato)


class ConectorDatosAbiertos:
    """Conecta el SIMANW con fuentes de datos abiertos."""

    def __init__(self, knowledge_graph: KnowledgeGraphSIMANW) -> None:
        self.kg = knowledge_graph
        self.DCAT = Namespace("http://www.w3.org/ns/dcat#")
        self.GOB = Namespace("http://datos.gob.mx/")
        self.kg.graph.bind("dcat", self.DCAT)
        self.kg.graph.bind("gob", self.GOB)

    def cargar_dataset_gobierno(
        self,
        nombre: str,
        datos: list[dict],
        publicador: str,
        tema: str,
    ) -> None:
        """Integra un dataset de datos abiertos al knowledge graph."""
        ds_uri = self.GOB[f"dataset/{_slug(nombre)}"]
        self.kg.graph.add((ds_uri, RDF.type, self.DCAT.Dataset))
        self.kg.graph.add((ds_uri, DC.title, Literal(nombre, lang="es")))
        self.kg.graph.add((ds_uri, DC.publisher, Literal(publicador)))
        self.kg.graph.add((ds_uri, self.GOB.tema, Literal(tema)))

        for indice, registro in enumerate(datos):
            reg_uri = self.GOB[f"registro/{_slug(nombre)}_{indice}"]
            self.kg.graph.add((ds_uri, self.GOB.tieneRegistro, reg_uri))
            for campo, valor in registro.items():
                predicado = self.GOB[_slug(campo)]
                if isinstance(valor, (int, float)):
                    self.kg.graph.add((reg_uri, predicado, Literal(valor, datatype=XSD.float)))
                else:
                    self.kg.graph.add((reg_uri, predicado, Literal(str(valor), lang="es")))

    def consultar_datos(self, tema: str | None = None) -> list[Any]:
        """Consulta los datos abiertos cargados."""
        filtro = f'FILTER(?tema = "{tema}")' if tema else ""
        query = f"""
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX gob: <http://datos.gob.mx/>

        SELECT ?titulo ?publicador ?tema
        WHERE {{
            ?ds a dcat:Dataset ;
                dc:title ?titulo ;
                dc:publisher ?publicador ;
                gob:tema ?tema .
            {filtro}
        }}
        ORDER BY ?titulo
        """
        return list(self.kg.graph.query(query))

    def enlazar_noticias_con_datos(self) -> list[Any]:
        """Enlaza noticias con datasets relacionados semanticamente."""
        query = """
        PREFIX simanw: <http://simanw.org/ontology/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX gob: <http://datos.gob.mx/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?noticia_titulo ?dataset_titulo ?tema
        WHERE {
            ?noticia a simanw:Noticia ;
                     dc:title ?noticia_titulo ;
                     simanw:tieneCategoria ?cat .
            ?cat rdfs:label ?cat_label .
            ?ds a dcat:Dataset ;
                dc:title ?dataset_titulo ;
                gob:tema ?tema .
            FILTER(CONTAINS(LCASE(STR(?tema)), LCASE(STR(?cat_label))))
        }
        ORDER BY ?tema ?noticia_titulo
        """
        return list(self.kg.graph.query(query))


def cargar_datasets_demo(conector: ConectorDatosAbiertos) -> None:
    conector.cargar_dataset_gobierno(
        "Presupuesto TIC Federal 2026",
        [
            {"dependencia": "SEP", "monto_mdp": 12500, "concepto": "Infraestructura digital educativa"},
            {"dependencia": "SALUD", "monto_mdp": 8900, "concepto": "Expediente clinico electronico"},
            {"dependencia": "SAT", "monto_mdp": 15600, "concepto": "Plataformas de recaudacion"},
        ],
        publicador="Secretaria de Hacienda",
        tema="tecnologia",
    )
    conector.cargar_dataset_gobierno(
        "Indicadores Economicos Mayo 2026",
        [
            {"indicador": "Inflacion anual", "valor": 4.2, "unidad": "porcentaje"},
            {"indicador": "Tipo de cambio", "valor": 18.5, "unidad": "pesos por dolar"},
            {"indicador": "Tasa de desempleo", "valor": 3.1, "unidad": "porcentaje"},
        ],
        publicador="INEGI / Banco de Mexico",
        tema="economia",
    )
    conector.cargar_dataset_gobierno(
        "Emisiones CO2 por Sector 2025",
        [
            {"sector": "Energia", "emisiones_mtco2": 450, "variacion": -2.1},
            {"sector": "Transporte", "emisiones_mtco2": 180, "variacion": 1.5},
            {"sector": "Industria", "emisiones_mtco2": 120, "variacion": -3.8},
        ],
        publicador="SEMARNAT",
        tema="ciencia",
    )


def endpoints_sparql_disponibles() -> dict[str, str]:
    return {
        "Wikidata": "https://query.wikidata.org/sparql",
        "DBpedia": "http://dbpedia.org/sparql",
        "datos.gob": "https://datos.gob.mx/",
    }


def _slug(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", str(texto).lower())
    sin_acentos = "".join(caracter for caracter in normalizado if not unicodedata.combining(caracter))
    slug = re.sub(r"[^a-z0-9]+", "_", sin_acentos).strip("_")
    return slug or "sin_valor"
