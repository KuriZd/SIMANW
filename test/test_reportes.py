from datetime import datetime

from src.knowledge_graph import KnowledgeGraphSIMANW
from src.reportes import GeneradorReportes, capacidades_simanw, resumen_pipeline_completo


def noticias_demo():
    return [
        {
            "titulo": "Inteligencia artificial en tecnologia",
            "cuerpo": "La IA transforma procesos digitales.",
            "fecha": "2026-05-10",
            "autor": "Maria Garcia",
            "fuente": "Portal SIMANW",
            "categoria_predicha": "tecnologia",
            "sentimiento": {"etiqueta": "positivo", "compound": 0.7},
        },
        {
            "titulo": "Mercados financieros y economia",
            "cuerpo": "La bolsa registra volatilidad.",
            "fecha": "2026-05-09",
            "autor": "Carlos Ruiz",
            "fuente": "Portal SIMANW",
            "categoria_predicha": "economia",
            "sentimiento": {"etiqueta": "negativo", "compound": -0.6},
        },
    ]


def kg_demo():
    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(noticias_demo())
    return kg


def test_generador_reportes_incluye_resumen_ejecutivo():
    reportero = GeneradorReportes(noticias_demo(), kg_demo())

    reporte = reportero.reporte_completo(datetime(2026, 5, 15, 10, 30, 0))

    assert "REPORTE AUTOMATICO - SISTEMA SIMANW" in reporte
    assert "Generado: 2026-05-15 10:30:00" in reporte
    assert "Noticias procesadas: 2" in reporte
    assert "Triples en Knowledge Graph:" in reporte
    assert "Categorias detectadas: 2" in reporte
    assert "Sentimiento promedio: +0.050" in reporte
    assert "Tono general: NEUTRAL" in reporte


def test_generador_reportes_detalla_categorias_sentimientos_y_catalogo():
    reportero = GeneradorReportes(noticias_demo(), kg_demo())

    reporte = reportero.reporte_completo(datetime(2026, 5, 15, 10, 30, 0))

    assert "DISTRIBUCION POR CATEGORIA" in reporte
    assert "tecnologia" in reporte
    assert "economia" in reporte
    assert "[+] positivo: 1 noticia(s)" in reporte
    assert "[-] negativo: 1 noticia(s)" in reporte
    assert "CATALOGO DE NOTICIAS" in reporte
    assert "Autor: Maria Garcia | Fuente: Portal SIMANW" in reporte


def test_capacidades_y_resumen_pipeline_final():
    capacidades = capacidades_simanw()
    resumen = resumen_pipeline_completo()

    assert len(capacidades) == 14
    assert ("Reportes", "Generacion automatica de resumenes") in capacidades
    assert "Fase 1: RASTREO WEB" in resumen
    assert "Fase 7: REPORTES + ENTREGA" in resumen


def test_reporte_markdown_incluye_pipeline_evidencias_y_metricas_integradas():
    reportero = GeneradorReportes(noticias_demo(), kg_demo())

    reporte = reportero.reporte_markdown(
        analisis={
            "clasificacion": {
                "ac3": {
                    "estado": "completo",
                    "mejor_modelo": "LinearSVC",
                    "accuracy_promedio": 0.82,
                    "accuracy_std": 0.03,
                    "archivo_json": "data/resultados_ac3.json",
                }
            },
            "evaluacion_busqueda": {
                "estado": "completo",
                "total_consultas": 3,
                "ganador_f1": "vectorial",
                "ganador_map": "vectorial",
                "map_booleano": 0.4,
                "map_vectorial": 0.7,
                "archivo_json": "data/resultados_ac5.json",
            },
        },
        grafo_info={
            "total_triples": 25,
            "evidencia_ac7": {
                "estado": "parcial",
                "entidades_evaluadas": 4,
                "total_enlaces_externos": 1,
                "endpoint": "https://query.wikidata.org/sparql",
                "archivo_ttl": "data/kg_enriquecido_ac7.ttl",
            },
        },
        evidencias_ac={"AC-5": {"estado": "completo", "ejecutado_desde": "Search & Q&A", "archivo_json": "data/resultados_ac5.json"}},
        estado_pipeline={"extraccion": "completed", "reportes": "completed"},
        archivos_generados=["outputs/reportes/reporte_final.md"],
        generado_en=datetime(2026, 5, 15, 10, 30, 0),
    )

    assert "Estado del pipeline" in reporte
    assert "Evidencia academica integrada" in reporte
    assert "Clasificacion multimodelo (AC-3)" in reporte
    assert "Evaluacion del motor de busqueda (AC-5)" in reporte
    assert "Knowledge Graph y Wikidata (AC-7)" in reporte
    assert "outputs/reportes/reporte_final.md" in reporte


def test_reportes_no_fallan_con_campos_faltantes():
    reportero = GeneradorReportes([{"titulo": "Noticia sin metadatos"}], kg_demo())

    texto = reportero.reporte_completo()
    markdown = reportero.reporte_markdown()

    assert "Noticia sin metadatos" in texto
    assert "Catalogo de noticias procesadas" in markdown
