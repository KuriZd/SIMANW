import json
from pathlib import Path

from src.enriquecedor_kg import EnriquecedorKG
from src.knowledge_graph import KnowledgeGraphSIMANW
from src.simanw_app_service import SIMANWAppService
from src.ui.seccion_exportar import artifact_info
from src.ui.seccion_explorador import _fmt_score, _sentimiento_label, _similares_texto
from src.ui_theme import SECTIONS


def test_sidebar_no_expone_rutas_ac():
    labels = [label for _, label, _ in SECTIONS]

    assert labels == [
        "Dashboard",
        "Load / Analyze News",
        "Smart Results",
        "News Explorer",
        "Search & Q&A",
        "Knowledge Graph",
        "Reports & Exports",
        "Academic Evidence",
    ]
    assert not any(label.startswith("AC-") for label in labels)


def test_ui_principal_no_contiene_mojibake_visible():
    archivos = [
        "src/ui/seccion_cargar.py",
        "src/ui/seccion_resultados.py",
        "src/ui/seccion_explorador.py",
        "src/ui/seccion_busqueda.py",
        "src/ui/seccion_grafo.py",
        "src/ui/seccion_exportar.py",
        "src/ui/seccion_evidencia.py",
    ]
    tokens_rotos = ["Ã", "Â", "â€”", "â€“", "â€¦", "â€œ", "â€", "�"]

    for archivo in archivos:
        texto = Path(archivo).read_text(encoding="utf-8")
        assert not any(token in texto for token in tokens_rotos), archivo


def test_ac10_carga_consultas_configurables(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("config").mkdir()
    Path("config/consultas_ac10.json").write_text(
        json.dumps(
            [
                {
                    "nombre": "Consulta real",
                    "expresion": "energia renovable",
                    "fecha_creacion": "2026-05-28T10:00:00Z",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    consultas, origen = SIMANWAppService._cargar_consultas_ac10()

    assert origen == "archivo_configurado"
    assert consultas[0].nombre == "Consulta real"
    assert consultas[0].expresion == "energia renovable"


def test_ac10_marca_plantilla_demo_si_no_hay_consultas_configuradas(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    consultas, origen = SIMANWAppService._cargar_consultas_ac10()

    assert origen == "plantilla_demo"
    assert len(consultas) >= 5


def test_ac11_demo_no_se_marca_como_real(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    estudio, origen = SIMANWAppService._cargar_estudio_usabilidad()

    assert origen == "demo"
    assert len(estudio.participantes) == 3


def test_ac11_json_real_con_tres_participantes_es_evidencia_real(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("data").mkdir()
    base_service = SIMANWAppService()
    items = base_service._cargar_estudio_usabilidad()[0].items
    participantes = []
    for idx in range(3):
        participantes.append(
            {
                "participante": f"U{idx + 1}",
                "respuestas": {item: 4 for item in items},
                "problemas": ["Observacion anonimizada"],
            }
        )
    Path("data/usabilidad_participantes.json").write_text(
        json.dumps(participantes, ensure_ascii=False),
        encoding="utf-8",
    )

    estudio, origen = SIMANWAppService._cargar_estudio_usabilidad()

    assert origen == "archivo_real"
    assert len(estudio.participantes) == 3


def test_ac4_deriva_hilo_desde_corpus_y_lo_marca_parcial(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("data").mkdir()
    service = SIMANWAppService()
    corpus = [
        {
            "titulo": "Debate sobre energia renovable",
            "cuerpo": "Los participantes discuten inversion en energia solar y eolica.",
            "autor": "Analista 1",
            "fecha": "2026-05-01",
        },
        {
            "titulo": "Respuesta ciudadana",
            "cuerpo": "La comunidad pregunta por costos y beneficios de la transicion energetica.",
            "autor": "Analista 2",
            "fecha": "2026-05-02",
        },
    ]

    evidencia = service._generar_evidencia_ac4(corpus)

    assert evidencia["estado"] == "parcial"
    assert evidencia["origen_datos"] == "corpus_derivado"
    assert evidencia["total_mensajes"] == 2
    assert Path(evidencia["archivo_json"]).exists()


def test_ac4_archivo_real_con_ocho_mensajes_es_completo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("data").mkdir()
    mensajes = [
        {
            "usuario": f"usuario_{idx % 3}",
            "texto": f"Mensaje {idx} sobre seguridad digital, privacidad y tecnologia responsable.",
            "timestamp": f"2026-05-{idx + 1:02d}",
        }
        for idx in range(8)
    ]
    Path("data/hilo_discusion.json").write_text(json.dumps(mensajes, ensure_ascii=False), encoding="utf-8")

    evidencia = SIMANWAppService()._generar_evidencia_ac4([])

    assert evidencia["estado"] == "completo"
    assert evidencia["origen_datos"] == "archivo_real"
    assert evidencia["total_mensajes"] == 8
    assert evidencia["subtemas_detectados"] >= 1


def test_wikidata_offline_queda_explicito(monkeypatch):
    monkeypatch.delenv("SIMANW_WIKIDATA_ONLINE", raising=False)
    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(
        [
            {
                "titulo": "Noticia de tecnologia",
                "cuerpo": "Texto",
                "categoria_predicha": "tecnologia",
                "autor": "Autor",
                "fecha": "2026-05-28",
                "url": "https://example.test/noticia",
                "fuente": "https://example.test",
                "sentimiento": {"etiqueta": "neutral", "compound": 0.0},
            }
        ]
    )

    evidencia = EnriquecedorKG(kg).enriquecer_desde_wikidata()

    assert evidencia["wikidata_online"] is False
    assert evidencia["modo"] == "offline"
    assert evidencia["estado"] == "parcial"


def test_fase7_no_usa_consulta_demo_en_reporte():
    service = SIMANWAppService()
    result = service.analizar_noticias("demo")
    reporte = Path(result.rutas["reporte_final"]).read_text(encoding="utf-8")

    assert "### demo" not in reporte
    assert "noticias tecnologia economia" in reporte or "sin consulta registrada" in reporte


def test_artifact_info_detecta_existente_y_faltante(tmp_path):
    archivo = tmp_path / "artefacto.json"
    archivo.write_text("{}", encoding="utf-8")

    existente = artifact_info("artefacto", archivo)
    faltante = artifact_info("faltante", tmp_path / "no_existe.json")

    assert existente["exists"] is True
    assert "[OK]" in existente["display"]
    assert faltante["exists"] is False
    assert "[faltante]" in faltante["display"]


def test_explorer_helpers_muestran_datos_enriquecidos():
    noticia = {"sentimiento": {"etiqueta": "positivo", "compound": 0.42}}
    similares = [{"titulo": "Noticia relacionada", "similitud": 0.81}]

    assert _sentimiento_label(noticia) == "positivo"
    assert _fmt_score(0.42) == "(+0.420)"
    assert "Noticia relacionada" in _similares_texto(similares)
