from __future__ import annotations

from rdflib import Literal, Namespace, RDFS, OWL
from rdflib.namespace import SKOS


class EnriquecedorKG:
    """
    AC-7: Enriquece el KG local conectando entidades con Wikidata/DBpedia.
    """

    def __init__(self, knowledge_graph) -> None:
        self.kg = knowledge_graph
        self.WD = Namespace("http://www.wikidata.org/entity/")
        self.WDT = Namespace("http://www.wikidata.org/prop/direct/")
        self.kg.graph.bind("wd", self.WD)
        self.kg.graph.bind("wdt", self.WDT)
        self.kg.graph.bind("skos", SKOS)
        self.enlaces_externos: list[dict] = []

    def enlazar_entidad(self, entidad_local, wikidata_id: str, etiqueta: str) -> None:
        """Enlaza una entidad local con su equivalente en Wikidata."""
        entidad_wikidata = self.WD[wikidata_id]
        self.kg.graph.add((entidad_local, OWL.sameAs, entidad_wikidata))
        self.kg.graph.add((entidad_local, SKOS.exactMatch, entidad_wikidata))
        self.kg.graph.add((entidad_wikidata, RDFS.label, Literal(etiqueta, lang="es")))
        self.enlaces_externos.append(
            {
                "local": str(entidad_local),
                "wikidata": wikidata_id,
                "etiqueta": etiqueta,
            }
        )

    def agregar_datos_externos(self, entidad_local, propiedades: dict[str, str]) -> None:
        """Agrega propiedades obtenidas de fuentes externas."""
        for propiedad, valor in propiedades.items():
            self.kg.graph.add((entidad_local, self.WDT[propiedad], Literal(valor)))

    def consulta_enriquecimiento(self) -> list:
        """Consulta SPARQL para verificar enlaces externos."""
        query = """
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?local ?externo ?etiqueta
        WHERE {
            ?local owl:sameAs ?externo .
            ?externo rdfs:label ?etiqueta .
        }
        ORDER BY ?local
        """
        return list(self.kg.graph.query(query))

    def generar_query_wikidata(self, tema: str) -> str:
        """Genera consultas SPARQL sugeridas para Wikidata segun el tema."""
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
        }
        return queries.get(tema, "# No hay consulta predefinida para este tema")


def enriquecer_categorias_demo(knowledge_graph) -> EnriquecedorKG:
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
