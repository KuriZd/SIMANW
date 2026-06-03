from rdflib import RDF
from rdflib.namespace import DC

from src.knowledge_graph import (
    QUERY_CONTEO_CATEGORIA,
    QUERY_DBPEDIA_HERRAMIENTAS_NLP,
    QUERY_NOTICIAS_METADATA,
    QUERY_SENTIMIENTO_NEGATIVO,
    QUERY_WIKIDATA_SOFTWARE_IA_PYTHON,
    ConectorDatosAbiertos,
    KnowledgeGraphSIMANW,
    cargar_datasets_demo,
    endpoints_sparql_disponibles,
)


def noticias_demo():
    return [
        {
            "titulo": "Inteligencia artificial en tecnologia",
            "cuerpo": "La IA transforma procesos digitales.",
            "fecha": "2026-05-10",
            "autor": "Maria Garcia",
            "categoria_predicha": "tecnologia",
            "url": "https://portal.test/ia",
            "fuente": "https://portal.test",
            "sentimiento": {"etiqueta": "positivo", "compound": 0.7},
        },
        {
            "titulo": "Mercados financieros y economia",
            "cuerpo": "La bolsa registra volatilidad.",
            "fecha": "2026-05-09",
            "autor": "Carlos Ruiz",
            "categoria_predicha": "economia",
            "url": "https://portal.test/mercados",
            "fuente": "https://portal.test",
            "sentimiento": {"etiqueta": "negativo", "compound": -0.6},
        },
        {
            "titulo": "Cambio climatico",
            "cuerpo": "Investigadores publican un estudio cientifico.",
            "fecha": "2026-05-08",
            "autor": "Ana Lopez",
            "categoria_predicha": "ciencia",
            "url": "https://portal.test/clima",
            "fuente": "https://portal.test",
            "sentimiento": {"etiqueta": "neutral", "compound": 0.0},
        },
    ]


def kg_demo():
    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(noticias_demo())
    return kg


def test_knowledge_graph_define_ontologia_y_agrega_noticias():
    kg = kg_demo()

    assert kg.total_triples() > 0
    assert (kg.NS.Noticia, RDF.type, None) in kg.graph
    assert (kg.DATA["noticia_1"], RDF.type, kg.NS.Noticia) in kg.graph
    assert (kg.DATA["noticia_1"], DC.title, None) in kg.graph


def test_knowledge_graph_consulta_metadatos_y_sentimiento_negativo():
    kg = kg_demo()

    metadatos = kg.consultar(QUERY_NOTICIAS_METADATA)
    negativos = kg.consultar(QUERY_SENTIMIENTO_NEGATIVO)

    assert len(metadatos) == 3
    assert str(metadatos[0].fecha) == "2026-05-10"
    assert len(negativos) == 1
    assert "Mercados financieros" in str(negativos[0].titulo)


def test_knowledge_graph_conteo_por_categoria():
    kg = kg_demo()

    conteos = {str(row.categoria): int(row.total) for row in kg.consultar(QUERY_CONTEO_CATEGORIA)}

    assert conteos == {"tecnologia": 1, "economia": 1, "ciencia": 1}


def test_conector_datos_abiertos_carga_y_filtra_datasets():
    kg = kg_demo()
    conector = ConectorDatosAbiertos(kg)
    cargar_datasets_demo(conector)

    datasets = conector.consultar_datos()
    tecnologia = conector.consultar_datos("tecnologia")

    assert len(datasets) == 3
    assert len(tecnologia) == 1
    assert str(tecnologia[0].titulo) == "Presupuesto TIC Federal 2026"
    assert kg.total_triples() > 60


def test_conector_datos_abiertos_enlaza_por_categoria_tema():
    kg = kg_demo()
    conector = ConectorDatosAbiertos(kg)
    cargar_datasets_demo(conector)

    enlaces = conector.enlazar_noticias_con_datos()
    pares = {(str(row.noticia_titulo), str(row.dataset_titulo)) for row in enlaces}

    assert ("Inteligencia artificial en tecnologia", "Presupuesto TIC Federal 2026") in pares
    assert ("Mercados financieros y economia", "Indicadores Economicos Mayo 2026") in pares
    assert ("Cambio climatico", "Emisiones CO2 por Sector 2025") in pares


def test_consultas_externas_quedan_preparadas_sin_ejecutar_red():
    endpoints = endpoints_sparql_disponibles()

    assert "Wikidata" in endpoints
    assert "DBpedia" in endpoints
    assert "wdt:P277" in QUERY_WIKIDATA_SOFTWARE_IA_PYTHON
    assert "Natural_language_processing" in QUERY_DBPEDIA_HERRAMIENTAS_NLP
