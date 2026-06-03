import json

from src.trazabilidad import TrazabilidadPipeline, trazabilidad_demo


def test_trazabilidad_demo_registra_ejecucion_completa():
    traza = trazabilidad_demo()

    etapas = [evento.etapa for evento in traza.eventos]

    assert etapas == ["rastreo", "procesamiento", "analisis", "busqueda", "grafo", "reporte"]


def test_guarda_manifiesto_y_log(tmp_path):
    traza = trazabilidad_demo()
    manifest = traza.guardar_manifiesto(tmp_path / "manifest.json", {"grafo": "data/simanw.ttl"})
    log = traza.guardar_log_jsonl(tmp_path / "log.jsonl")

    data = json.loads(manifest.read_text(encoding="utf-8"))
    lineas = log.read_text(encoding="utf-8").strip().splitlines()

    assert data["version_proyecto"] == "demo-ac12"
    assert data["documentos_por_etapa"]["grafo"] == 23
    assert len(lineas) == 6


def test_textos_reproducibilidad_checklist_y_limitaciones():
    traza = TrazabilidadPipeline("data/noticias.json", version_proyecto="abc123")

    assert "No se requiere HTML de demostracion" in traza.procedimiento_reproducible()
    assert "Firma del alumno" in traza.checklist_firmado("Alumno")
    assert "Limitaciones conocidas" in traza.anexo_limitaciones()
