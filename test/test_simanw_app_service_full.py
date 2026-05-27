from pathlib import Path

import pytest

from src.fase4_service import Fase4Service
from src.fase5_service import Fase5Service
from src.fase6_service import Fase6Service
from src.simanw_app_service import SIMANWAppService


def test_simanw_app_service_demo_pipeline_runs_successfully():
    service = SIMANWAppService()

    result = service.analizar_noticias("demo")

    assert result.noticias
    assert result.corpus_procesado
    assert result.analisis
    assert result.estado_pipeline.extraction == "completed"
    assert result.estado_pipeline.nlp == "completed"
    assert result.estado_pipeline.search == "completed"


def test_search_service_returns_enriched_results_after_index():
    service = SIMANWAppService()
    result = service.analizar_noticias("demo")

    results = service.buscar(result.noticias[0]["titulo"])

    assert results
    assert {"titulo", "categoria", "sentimiento", "fecha", "url", "score", "snippet"} <= set(results[0])


def test_qa_service_returns_string():
    service = SIMANWAppService()
    service.analizar_noticias("demo")

    answer = service.preguntar("Cuantas noticias tienes?")

    assert isinstance(answer, str)
    assert answer


def test_graph_service_exports_files_or_reports_warning(tmp_path):
    app_service = SIMANWAppService()
    result = app_service.analizar_noticias("demo")

    graph = Fase6Service()
    info = graph.construir_grafo(result.corpus_procesado, result.analisis)
    ttl = graph.exportar_ttl()
    jsonld = graph.exportar_jsonld()

    assert info["total_triples"] > 0 or info["errores"]
    assert ttl.exists()
    assert jsonld.exists()


def test_report_service_creates_final_report():
    service = SIMANWAppService()
    result = service.analizar_noticias("demo")

    assert Path("outputs/reportes/reporte_final.md").exists()
    assert any(path.endswith("reporte_final.md") for path in result.archivos_generados)


def test_pipeline_keeps_partial_result_when_optional_search_fails(monkeypatch):
    def fail_index(self, corpus):
        raise RuntimeError("forced search failure")

    monkeypatch.setattr(Fase4Service, "construir_indice", fail_index)
    service = SIMANWAppService()

    result = service.analizar_noticias("demo")

    assert result.noticias
    assert result.corpus_procesado
    assert result.estado_pipeline.search == "error"
    assert any("Search:" in error for error in result.errores)
