from rdflib import RDF
from rdflib.namespace import DC, OWL
import json

from src.knowledge_graph import (
    QUERY_AC13_AUTORES_PRODUCTIVOS,
    QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
    QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
    KnowledgeGraphSIMANW,
)
from src.fase6_service import Fase6Service


def _kg_ac13():
    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(
        [
            {
                "titulo": "IA en salud",
                "cuerpo": "La inteligencia artificial apoya diagnosticos.",
                "fecha": "2026-05-20",
                "autor": "Ana",
                "categoria_predicha": "tecnologia",
                "url": "https://demo.test/ia",
                "fuente": "https://demo.test",
                "sentimiento": {"etiqueta": "positivo", "compound": 0.6},
            },
            {
                "titulo": "Mercados caen",
                "cuerpo": "Los mercados caen por inflacion.",
                "fecha": "2026-05-21",
                "autor": "Ana",
                "categoria_predicha": "economia",
                "url": "https://demo.test/eco",
                "fuente": "https://demo.test",
                "sentimiento": {"etiqueta": "negativo", "compound": -0.4},
            },
        ]
    )
    return kg


def test_exporta_turtle_y_jsonld(tmp_path):
    kg = _kg_ac13()

    rutas = kg.exportar_rdf(tmp_path / "simanw")

    assert rutas["turtle"].exists()
    assert rutas["json-ld"].exists()
    assert "@prefix" in rutas["turtle"].read_text(encoding="utf-8")


def test_glosario_y_enlaces_externos():
    kg = _kg_ac13()
    enlaces = kg.agregar_enlaces_externos_basicos()
    glosario = kg.glosario_ontologia()

    assert len(enlaces) >= 5
    assert (kg.NS.Noticia, OWL.equivalentClass, kg.SCHEMA.NewsArticle) in kg.graph
    assert "simanw:Noticia" in glosario["clases"]


def test_consultas_sparql_ac13_responden_preguntas_distintas():
    kg = _kg_ac13()

    autores = kg.consultar(QUERY_AC13_AUTORES_PRODUCTIVOS)
    sentimientos = kg.consultar(QUERY_AC13_SENTIMIENTO_POR_CATEGORIA)
    negativas = kg.consultar(QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS)

    assert int(autores[0].total) == 2
    assert len(sentimientos) == 2
    assert str(negativas[0].titulo) == "Mercados caen"


def test_validacion_detecta_y_reporta_violaciones():
    kg = _kg_ac13()
    assert kg.validar_formas()["conforme"] is True

    kg.graph.remove((kg.DATA["noticia_1"], DC.title, None))
    resultado = kg.validar_formas()

    assert resultado["conforme"] is False
    assert resultado["violaciones"][0]["propiedad"] == "titulo"


def test_fragmento_jsonld_coherente_con_grafo():
    kg = _kg_ac13()

    fragmento = kg.fragmento_jsonld_noticia(1)

    assert fragmento["@type"] == "schema:NewsArticle"
    assert fragmento["title"] == "IA en salud"
    assert (kg.DATA["noticia_1"], RDF.type, kg.NS.Noticia) in kg.graph


def test_fragmento_jsonld_se_puede_formatear_para_ui():
    kg = _kg_ac13()

    fragmento = kg.fragmento_jsonld_noticia(1)
    texto = json.dumps(fragmento, ensure_ascii=False, indent=2)

    assert isinstance(fragmento, dict)
    assert '"@type": "schema:NewsArticle"' in texto
    assert texto.splitlines()


def test_publicacion_semantica_exporta_nota_de_reutilizacion():
    service = Fase6Service()
    service.kg = _kg_ac13()

    evidencia = service.publicar_semanticamente()

    assert evidencia["enlaces_externos_creados"] >= 5
    assert "criterio_enlace" in evidencia
    assert "reutilizacion" in evidencia["archivos"]
    ruta = evidencia["archivos"]["reutilizacion"]
    texto = open(ruta, encoding="utf-8").read()
    assert "descubrir y reutilizar" in texto.lower()
    assert "criterio de enlace externo" in texto.lower()
