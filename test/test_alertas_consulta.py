from src.alertas_consulta import SistemaAlertasConsulta, consultas_demo, noticias_nuevas_demo


def test_persisten_cinco_consultas_guardadas(tmp_path):
    sistema = SistemaAlertasConsulta(consultas_demo())
    ruta = sistema.guardar_consultas(tmp_path / "consultas.json")

    cargado = SistemaAlertasConsulta()
    cargado.cargar_consultas(ruta)

    assert len(cargado.consultas) == 5
    assert cargado.consultas[0].fecha_creacion == "2026-05-25T09:00:00Z"


def test_ejecucion_sin_noticias_no_genera_alertas():
    sistema = SistemaAlertasConsulta(consultas_demo())

    alertas = sistema.procesar_noticias_nuevas([])

    assert alertas == []
    assert sistema.historial_alertas == []


def test_alertas_y_deduplicacion_por_consulta_noticia():
    sistema = SistemaAlertasConsulta(consultas_demo())

    primeras = sistema.procesar_noticias_nuevas(noticias_nuevas_demo())
    repetidas = sistema.procesar_noticias_nuevas(noticias_nuevas_demo())

    assert len(primeras) == 5
    assert repetidas == []
    assert len(sistema.historial_alertas) == 5


def test_documentacion_deduplicacion_menciona_llave_compuesta():
    sistema = SistemaAlertasConsulta(consultas_demo())

    texto = sistema.documentar_deduplicacion()

    assert "consulta" in texto.lower()
    assert "noticia" in texto.lower()


def test_reporte_markdown_documenta_consultas_alertas_y_deduplicacion(tmp_path):
    sistema = SistemaAlertasConsulta(consultas_demo())
    sistema.procesar_noticias_nuevas(noticias_nuevas_demo())

    ruta = sistema.guardar_reporte_markdown(tmp_path / "alertas_ac10.md")
    texto = ruta.read_text(encoding="utf-8")

    assert "Consultas activas" in texto
    assert "Alertas generadas" in texto
    assert "Mecanismo de deduplicación" in texto
    assert "consulta guardada" in texto
    assert "noticia" in texto
    assert "Ã" not in texto
    assert "â" not in texto
