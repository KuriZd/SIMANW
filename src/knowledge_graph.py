from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, XSD
from rdflib.namespace import DC, DCTERMS, FOAF, SKOS


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

QUERY_AC13_AUTORES_PRODUCTIVOS = """
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?autor (COUNT(?noticia) AS ?total)
WHERE {
    ?noticia a simanw:Noticia ;
             simanw:tieneAutor ?autor_uri .
    ?autor_uri foaf:name ?autor .
}
GROUP BY ?autor
ORDER BY DESC(?total)
"""

QUERY_AC13_SENTIMIENTO_POR_CATEGORIA = """
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?categoria (AVG(?score) AS ?sentimiento_promedio) (COUNT(?noticia) AS ?total)
WHERE {
    ?noticia a simanw:Noticia ;
             simanw:tieneCategoria ?cat ;
             simanw:sentimientoScore ?score .
    ?cat rdfs:label ?categoria .
}
GROUP BY ?categoria
ORDER BY ?categoria
"""

QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS = """
PREFIX simanw: <http://simanw.org/ontology/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT ?titulo ?fecha ?score
WHERE {
    ?noticia a simanw:Noticia ;
             dc:title ?titulo ;
             dc:date ?fecha ;
             simanw:sentimientoScore ?score .
    FILTER(?score < 0)
}
ORDER BY DESC(?fecha)
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
        self.SCHEMA = Namespace("https://schema.org/")
        self.WD = Namespace("http://www.wikidata.org/entity/")
        self.DBP = Namespace("http://dbpedia.org/resource/")
        self.graph.bind("simanw", self.NS)
        self.graph.bind("data", self.DATA)
        self.graph.bind("schema", self.SCHEMA)
        self.graph.bind("wd", self.WD)
        self.graph.bind("dbpedia", self.DBP)
        self.graph.bind("dc", DC)
        self.graph.bind("dcterms", DCTERMS)
        self.graph.bind("foaf", FOAF)
        self.graph.bind("skos", SKOS)
        self._definir_ontologia()

    def _definir_ontologia(self) -> None:
        """Define la ontologia del SIMANW."""
        for clase in [self.NS.Noticia, self.NS.Autor, self.NS.Categoria, self.NS.Fuente]:
            self.graph.add((clase, RDF.type, OWL.Class))

        self.graph.add((self.NS.Noticia, RDFS.subClassOf, self.SCHEMA.NewsArticle))
        self.graph.add((self.NS.Autor, RDFS.subClassOf, FOAF.Person))
        self.graph.add((self.NS.Fuente, RDFS.subClassOf, self.SCHEMA.Organization))

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
        self.graph.add((self.NS.tieneAutor, OWL.equivalentProperty, self.SCHEMA.author))
        self.graph.add((self.NS.provieneDe, OWL.equivalentProperty, self.SCHEMA.publisher))

        propiedades_datos = [
            self.NS.sentimientoScore,
            self.NS.sentimientoEtiqueta,
            self.NS.urlOriginal,
        ]
        for propiedad in propiedades_datos:
            self.graph.add((propiedad, RDF.type, OWL.DatatypeProperty))

        # dominio y rango de propiedades de datos
        self.graph.add((self.NS.sentimientoScore, RDFS.domain, self.NS.Noticia))
        self.graph.add((self.NS.sentimientoScore, RDFS.range, XSD.float))
        self.graph.add((self.NS.sentimientoEtiqueta, RDFS.domain, self.NS.Noticia))
        self.graph.add((self.NS.sentimientoEtiqueta, RDFS.range, XSD.string))
        self.graph.add((self.NS.urlOriginal, RDFS.domain, self.NS.Noticia))
        self.graph.add((self.NS.urlOriginal, RDFS.range, XSD.anyURI))

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
        """Ejecuta una consulta SPARQL sobre el grafo local."""
        return list(self.graph.query(sparql_query))

    def total_triples(self) -> int:
        return len(self.graph)

    def serializar(self, formato: str = "turtle") -> str:
        return self.graph.serialize(format=formato)

    def _serializar_jsonld_compacto(self) -> str:
        """Serializa el grafo en JSON-LD compacto con @context legible."""
        contexto = {
            "simanw": str(self.NS),
            "data": str(self.DATA),
            "schema": str(self.SCHEMA),
            "wd": str(self.WD),
            "dbpedia": str(self.DBP),
            "dc": "http://purl.org/dc/elements/1.1/",
            "foaf": str(FOAF),
            "owl": "http://www.w3.org/2002/07/owl#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "skos": str(SKOS),
        }
        return self.graph.serialize(format="json-ld", context=contexto, indent=2)

    def exportar_rdf(self, ruta_base: str | Path = "data/simanw") -> dict[str, Path]:
        """Exporta Turtle y JSON-LD compacto con @context para el volcado RDF."""
        base = Path(ruta_base)
        base.parent.mkdir(parents=True, exist_ok=True)
        rutas = {
            "turtle": base.with_suffix(".ttl"),
            "json-ld": base.with_suffix(".jsonld"),
        }
        rutas["turtle"].write_text(self.serializar("turtle"), encoding="utf-8")
        rutas["json-ld"].write_text(self._serializar_jsonld_compacto(), encoding="utf-8")
        return rutas

    def glosario_ontologia(self) -> dict[str, dict[str, str]]:
        return {
            "prefijos": {
                "simanw": str(self.NS),
                "data": str(self.DATA),
                "dc": "http://purl.org/dc/elements/1.1/",
                "foaf": str(FOAF),
                "schema": str(self.SCHEMA),
                "wd": str(self.WD),
                "dbpedia": str(self.DBP),
                "skos": str(SKOS),
                "owl": "http://www.w3.org/2002/07/owl#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
            },
            "clases": {
                "simanw:Noticia": "Documento periodistico monitoreado por el sistema.",
                "simanw:Autor": "Persona o entidad que firma una noticia.",
                "simanw:Categoria": "Tema asignado por clasificacion o por la fuente original.",
                "simanw:Fuente": "Medio o sitio desde donde se obtuvo la noticia.",
            },
            "propiedades": {
                "simanw:tieneAutor": "Relacion entre noticia y autor.",
                "simanw:tieneCategoria": "Relacion entre noticia y categoria tematica.",
                "simanw:provieneDe": "Relacion entre noticia y fuente.",
                "simanw:sentimientoScore": "Valor numerico del sentimiento calculado (xsd:float).",
                "simanw:sentimientoEtiqueta": "Etiqueta textual del sentimiento (positivo, negativo, neutro).",
                "simanw:urlOriginal": "URL original de la noticia rastreada (xsd:anyURI).",
            },
        }

    def agregar_enlaces_externos_basicos(self) -> list[dict[str, str]]:
        """Crea al menos cinco enlaces explicitos a vocabularios o datasets publicos.

        Clases: owl:equivalentClass (equivalencia entre clases OWL).
        Instancias categoria: skos:closeMatch (correspondencia aproximada con datasets externos).
        """
        enlaces = [
            (
                self.NS.Noticia,
                OWL.equivalentClass,
                self.SCHEMA.NewsArticle,
                "Clase Noticia equivalente a schema:NewsArticle (owl:equivalentClass).",
            ),
            (
                self.NS.Autor,
                OWL.equivalentClass,
                FOAF.Person,
                "Clase Autor equivalente a foaf:Person (owl:equivalentClass).",
            ),
            (
                self.NS.Fuente,
                OWL.equivalentClass,
                self.SCHEMA.Organization,
                "Clase Fuente equivalente a schema:Organization (owl:equivalentClass).",
            ),
            (
                self.DATA["categoria_tecnologia"],
                SKOS.closeMatch,
                self.WD.Q11016,
                "Categoria tecnologia ~ Wikidata Q11016 (skos:closeMatch, correspondencia aproximada).",
            ),
            (
                self.DATA["categoria_economia"],
                SKOS.closeMatch,
                self.DBP.Economics,
                "Categoria economia ~ DBpedia Economics (skos:closeMatch, correspondencia aproximada).",
            ),
            (
                self.DATA["categoria_ciencia"],
                SKOS.closeMatch,
                self.WD.Q336,
                "Categoria ciencia ~ Wikidata Q336 (skos:closeMatch, correspondencia aproximada).",
            ),
        ]
        salida: list[dict[str, str]] = []
        for sujeto, predicado, objeto, criterio in enlaces:
            self.graph.add((sujeto, predicado, objeto))
            salida.append(
                {
                    "local": str(sujeto),
                    "relacion": str(predicado).split("#")[-1],
                    "externo": str(objeto),
                    "criterio": criterio,
                }
            )
        return salida

    def validar_formas(self) -> dict[str, Any]:
        """Valida restricciones SHACL basicas sin dependencia externa."""
        violaciones: list[dict[str, str]] = []
        requeridos = [
            ("titulo", DC.title),
            ("fecha", DC.date),
            ("autor", self.NS.tieneAutor),
            ("categoria", self.NS.tieneCategoria),
            ("url", self.NS.urlOriginal),
        ]
        for noticia in self.graph.subjects(RDF.type, self.NS.Noticia):
            for nombre, predicado in requeridos:
                if (noticia, predicado, None) not in self.graph:
                    violaciones.append(
                        {
                            "recurso": str(noticia),
                            "forma": "NoticiaShape",
                            "propiedad": nombre,
                            "mensaje": f"Falta propiedad obligatoria {nombre}.",
                        }
                    )
        return {"conforme": not violaciones, "violaciones": violaciones}

    def validar_con_shacl(
        self, shapes_path: str | Path = "shapes/simanw_shapes.ttl"
    ) -> dict[str, Any]:
        """Valida el grafo usando pyshacl contra el archivo de shapes SHACL formal."""
        try:
            from pyshacl import validate  # type: ignore[import]
        except ImportError:
            return {"error": "pyshacl no instalado. Ejecuta: pip install pyshacl"}

        shapes_path = Path(shapes_path)
        if not shapes_path.exists():
            return {"error": f"Archivo de shapes no encontrado: {shapes_path}"}

        conforme, _resultado_graph, texto = validate(
            self.graph,
            shacl_graph=str(shapes_path),
            shacl_graph_format="turtle",
            inference="rdfs",
            serialize_report_graph=False,
        )
        return {
            "conforme": conforme,
            "texto": texto,
            "mecanismo": "pyshacl",
            "shapes_file": str(shapes_path),
        }

    def fragmento_jsonld_noticia(self, noticia_id: int = 1) -> dict[str, Any]:
        noticia_uri = self.DATA[f"noticia_{noticia_id}"]
        titulo = self.graph.value(noticia_uri, DC.title)
        fecha = self.graph.value(noticia_uri, DC.date)
        url = self.graph.value(noticia_uri, self.NS.urlOriginal)
        autor_uri = self.graph.value(noticia_uri, self.NS.tieneAutor)
        categoria_uri = self.graph.value(noticia_uri, self.NS.tieneCategoria)
        autor = self.graph.value(autor_uri, FOAF.name) if autor_uri else None
        categoria = self.graph.value(categoria_uri, RDFS.label) if categoria_uri else None
        sentimiento = self.graph.value(noticia_uri, self.NS.sentimientoEtiqueta)
        return {
            "@context": {
                "schema": str(self.SCHEMA),
                "simanw": str(self.NS),
                "dc": "http://purl.org/dc/elements/1.1/",
                "skos": str(SKOS),
                "title": "dc:title",
                "datePublished": "dc:date",
                "author": "schema:author",
                "articleSection": "schema:articleSection",
                "url": "simanw:urlOriginal",
                "sentiment": "simanw:sentimientoEtiqueta",
            },
            "@id": str(noticia_uri),
            "@type": "schema:NewsArticle",
            "title": str(titulo) if titulo else "",
            "datePublished": str(fecha) if fecha else "",
            "author": str(autor) if autor else "",
            "articleSection": str(categoria) if categoria else "",
            "url": str(url) if url else "",
            "sentiment": str(sentimiento) if sentimiento else "",
        }

    def nota_reutilizacion_datos(self) -> str:
        return (
            "Un agente externo puede descubrir y reutilizar los datos del SIMANW sin acceder al "
            "codigo fuente si recibe el volcado RDF, la documentacion de prefijos y el glosario "
            "de la ontologia. El agente identifica noticias como schema:NewsArticle mediante "
            "owl:equivalentClass, interpreta autores con FOAF y fechas/titulos con Dublin Core, "
            "y sigue enlaces skos:closeMatch hacia Wikidata o DBpedia para las categorias. "
            "Con esos elementos puede cargar el Turtle o JSON-LD en un triplestore local, "
            "ejecutar consultas SPARQL sobre categorias, autores, sentimiento y fechas, y "
            "combinar recursos locales con datasets publicos mediante URIs estables."
        )


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
