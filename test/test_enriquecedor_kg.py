from rdflib import OWL, RDFS
from rdflib.namespace import SKOS

from src.enriquecedor_kg import EnriquecedorKG, enriquecer_categorias_demo
from src.knowledge_graph import KnowledgeGraphSIMANW


def kg_demo():
    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(
        [
            {
                "titulo": "IA en tecnologia",
                "cuerpo": "La inteligencia artificial transforma software.",
                "fecha": "2026-05-10",
                "autor": "Maria Garcia",
                "categoria_predicha": "tecnologia",
                "sentimiento": {"etiqueta": "positivo", "compound": 0.7},
            },
            {
                "titulo": "Mercados y economia",
                "cuerpo": "La economia enfrenta volatilidad.",
                "fecha": "2026-05-09",
                "autor": "Carlos Ruiz",
                "categoria_predicha": "economia",
                "sentimiento": {"etiqueta": "negativo", "compound": -0.4},
            },
        ]
    )
    return kg


def test_enriquecedor_enlaza_entidad_con_wikidata():
    kg = kg_demo()
    enriquecedor = EnriquecedorKG(kg)
    entidad = kg.DATA["categoria_tecnologia"]

    enriquecedor.enlazar_entidad(entidad, "Q11016", "Tecnologia de la informacion")

    assert (entidad, OWL.sameAs, enriquecedor.WD["Q11016"]) in kg.graph
    assert (entidad, SKOS.exactMatch, enriquecedor.WD["Q11016"]) in kg.graph
    assert (enriquecedor.WD["Q11016"], RDFS.label, None) in kg.graph
    assert enriquecedor.enlaces_externos[0]["wikidata"] == "Q11016"


def test_enriquecedor_agrega_datos_externos_y_consulta_enlaces():
    kg = kg_demo()
    enriquecedor = EnriquecedorKG(kg)
    entidad = kg.DATA["categoria_tecnologia"]

    enriquecedor.enlazar_entidad(entidad, "Q11016", "Tecnologia de la informacion")
    enriquecedor.agregar_datos_externos(entidad, {"P279": "Sector economico terciario"})

    enlaces = enriquecedor.consulta_enriquecimiento()

    assert len(enlaces) == 1
    assert str(enlaces[0].externo).endswith("Q11016")
    assert (entidad, enriquecedor.WDT["P279"], None) in kg.graph


def test_enriquecedor_demo_enlaza_categorias_existentes():
    kg = kg_demo()
    triples_antes = kg.total_triples()

    enriquecedor = enriquecer_categorias_demo(kg)

    assert kg.total_triples() > triples_antes
    assert len(enriquecedor.enlaces_externos) == 4
    assert len(enriquecedor.consulta_enriquecimiento()) == 4


def test_enriquecedor_genera_queries_wikidata():
    kg = kg_demo()
    enriquecedor = EnriquecedorKG(kg)

    query_tecnologia = enriquecedor.generar_query_wikidata("tecnologia")
    query_ciencia = enriquecedor.generar_query_wikidata("ciencia")
    query_desconocida = enriquecedor.generar_query_wikidata("deportes")

    assert "wdt:P366" in query_tecnologia
    assert "cambio climatico" in query_ciencia
    assert "No hay consulta" in query_desconocida
