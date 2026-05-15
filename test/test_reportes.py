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
