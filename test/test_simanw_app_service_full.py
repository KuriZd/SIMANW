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
    assert "AC-2" in result.evidencias_ac
    assert result.evidencias_ac["AC-2"]["archivo_json"].endswith("analisis_ac2.json")
    assert "AC-3" in result.evidencias_ac
    assert result.evidencias_ac["AC-3"]["estado"] in {"completo", "parcial", "pendiente"}
    assert "AC-5" in result.evidencias_ac
    assert result.evidencias_ac["AC-5"]["estado"] in {"completo", "pendiente"}
    assert "AC-7" in result.evidencias_ac
    assert result.evidencias_ac["AC-7"]["estado"] in {"completo", "parcial", "pendiente"}
    assert "Fase-7" in result.evidencias_ac
    assert result.evidencias_ac["Fase-7"]["estado"] == "completo"
    for ac in ("AC-4", "AC-8", "AC-9", "AC-10", "AC-11", "AC-12", "AC-13"):
        assert ac in result.evidencias_ac


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
    assert Path("outputs/reportes/reporte_final.json").exists()
    assert any(path.endswith("reporte_final.md") for path in result.archivos_generados)
    assert any(path.endswith("reporte_final.json") for path in result.archivos_generados)


def test_ac8_quality_runs_before_phase2_and_feeds_clean_corpus():
    service = SIMANWAppService()
    result = service.analizar_noticias("demo")

    ac8 = result.evidencias_ac["AC-8"]

    assert ac8["total_registros"] >= ac8["registros_validos"]
    assert ac8["registros_validos"] == len(result.corpus_procesado)
    assert result.rutas["ac8_informe_json"].endswith("ac8_informe_calidad.json")
    assert Path(result.rutas["ac8_corpus_depurado"]).exists()


def test_ac10_alerts_use_loaded_corpus_and_deduplicate():
    service = SIMANWAppService()
    result = service.analizar_noticias("demo")

    ac10 = result.evidencias_ac["AC-10"]
    rerun = service.ejecutar_alertas_guardadas()

    assert ac10["numero_consultas"] >= 5
    assert ac10["ejecucion_sin_noticias_nuevas"] == 0
    assert "historial" in ac10["archivos"]
    assert rerun["alertas_duplicadas_evitadas"] >= rerun["alertas_generadas"]


def test_ac11_ac12_ac13_evidence_and_artifacts_are_registered():
    service = SIMANWAppService()
    result = service.analizar_noticias("demo")

    ac11 = result.evidencias_ac["AC-11"]
    ac12 = result.evidencias_ac["AC-12"]
    ac13 = result.evidencias_ac["AC-13"]

    assert ac11["datos"] in {"demo", "reales_anonimizados"}
    assert ac11["estado"] in {"parcial", "completo"}
    assert ac12["archivos"]["manifest"].endswith("manifest.json")
    assert Path(ac12["archivos"]["checklist"]).exists()
    assert Path(ac12["archivos"]["limitaciones"]).exists()
    assert ac13["formatos_generados"] == ["turtle", "json-ld"]
    assert "resultado_shacl" in ac13
    assert Path(ac13["archivos"]["turtle"]).exists()
    assert Path(ac13["archivos"]["jsonld"]).exists()
    assert "ac13_validacion" in result.rutas


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
