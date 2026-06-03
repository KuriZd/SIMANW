from __future__ import annotations

from src.tendencias_temporales import TendenciasTemporales, NOTICIAS_AC9_DEMO


def _noticias_basicas():
    return [
        {"titulo": "Noticia A sobre IA", "cuerpo": "inteligencia artificial aprendizaje automatico redes neuronales", "fecha": "2026-01-10", "categoria_predicha": "tecnologia"},
        {"titulo": "Noticia B sobre IA avanzada", "cuerpo": "modelos de lenguaje transformers inteligencia artificial generativa", "fecha": "2026-02-15", "categoria_predicha": "tecnologia"},
        {"titulo": "Mercados en calma", "cuerpo": "inflacion tasas interes economia banco central finanzas", "fecha": "2026-01-20", "categoria_predicha": "economia"},
        {"titulo": "Alza bursátil récord", "cuerpo": "bolsa mercados acciones inversiones finanzas economia crecimiento", "fecha": "2026-02-22", "categoria_predicha": "economia"},
    ]


def test_cargar_noticias_filtra_fechas_invalidas():
    analizador = TendenciasTemporales()
    noticias = _noticias_basicas() + [
        {"titulo": "Sin fecha", "cuerpo": "texto", "fecha": "", "categoria_predicha": "otro"},
        {"titulo": "Fecha mala", "cuerpo": "texto", "fecha": "99/99/9999", "categoria_predicha": "otro"},
    ]
    analizador.cargar_noticias(noticias)
    assert len(analizador.noticias) == 4


def test_conteo_por_periodo_agrupa_correctamente():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(_noticias_basicas())
    conteos = analizador.conteo_por_periodo()

    assert conteos["tecnologia"]["2026-01"] == 1
    assert conteos["tecnologia"]["2026-02"] == 1
    assert conteos["economia"]["2026-01"] == 1
    assert conteos["economia"]["2026-02"] == 1


def test_conteo_periodos_ordenados():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(_noticias_basicas())
    conteos = analizador.conteo_por_periodo()
    for periodos in conteos.values():
        claves = list(periodos.keys())
        assert claves == sorted(claves)


def test_tendencia_terminos_detecta_cambios():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(_noticias_basicas())
    tend = analizador.tendencia_terminos("tecnologia")

    assert tend["primer_periodo"] == "2026-01"
    assert tend["ultimo_periodo"] == "2026-02"
    assert isinstance(tend["aumentan"], list)
    assert isinstance(tend["disminuyen"], list)


def test_tendencias_terminos_cubre_al_menos_tres_categorias():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(NOTICIAS_AC9_DEMO)

    tendencias = analizador.tendencias_terminos_por_categoria(minimo_categorias=3)

    assert len(tendencias) >= 3
    assert all({"aumentan", "disminuyen", "primer_periodo", "ultimo_periodo"} <= set(data) for data in tendencias.values())


def test_tendencia_terminos_categoria_inexistente():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(_noticias_basicas())
    tend = analizador.tendencia_terminos("inexistente")
    assert tend["aumentan"] == []
    assert tend["disminuyen"] == []


def test_pico_notable_identifica_maximo():
    analizador = TendenciasTemporales(granularidad="mes")
    noticias = _noticias_basicas() + [
        {"titulo": "Tercera noticia tecnologia", "cuerpo": "software desarrollo programacion", "fecha": "2026-02-10", "categoria_predicha": "tecnologia"},
    ]
    analizador.cargar_noticias(noticias)
    pico = analizador.pico_notable()

    assert pico["categoria"] == "tecnologia"
    assert pico["periodo"] == "2026-02"
    assert pico["count"] == 2
    assert len(pico["titulos"]) == 2


def test_tabla_resumen_contiene_todas_filas():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(_noticias_basicas())
    tabla = analizador.tabla_resumen()

    assert len(tabla) == 4
    assert all({"categoria", "periodo", "noticias"}.issubset(fila.keys()) for fila in tabla)


def test_exportar_csv_crea_archivo(tmp_path):
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(_noticias_basicas())
    ruta = analizador.exportar_csv(tmp_path / "tendencias.csv")

    assert ruta.exists()
    contenido = ruta.read_text(encoding="utf-8")
    assert "categoria" in contenido
    assert "tecnologia" in contenido
    assert "terminos_aumentan" in contenido
    assert "terminos_disminuyen" in contenido


def test_exporta_reporte_json_y_conclusion_markdown(tmp_path):
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(NOTICIAS_AC9_DEMO)

    ruta_json = analizador.guardar_reporte_json(tmp_path / "tendencias.json")
    ruta_md = analizador.guardar_conclusion_markdown(tmp_path / "conclusion.md")

    contenido_json = ruta_json.read_text(encoding="utf-8")
    contenido_md = ruta_md.read_text(encoding="utf-8")
    assert "tendencias_terminos" in contenido_json
    assert "CONCLUSIÓN" in contenido_md
    assert "pico más notable" in contenido_md


def test_visualizacion_texto_no_vacia():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(_noticias_basicas())
    viz = analizador.visualizacion_texto()

    assert "TECNOLOGIA" in viz
    assert "#" in viz


def test_conclusion_menciona_pico():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(NOTICIAS_AC9_DEMO)
    conclusion = analizador.conclusion()

    assert "pico" in conclusion.lower()
    assert "mensual" in conclusion.lower()


def test_granularidad_semana():
    analizador = TendenciasTemporales(granularidad="semana")
    analizador.cargar_noticias(_noticias_basicas())
    conteos = analizador.conteo_por_periodo()

    for periodos in conteos.values():
        for clave in periodos:
            assert "-W" in clave


def test_demo_data_tres_categorias():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(NOTICIAS_AC9_DEMO)
    conteos = analizador.conteo_por_periodo()

    assert len(conteos) >= 3
    assert "tecnologia" in conteos
    assert "economia" in conteos
    assert "ciencia" in conteos


def test_demo_data_tres_periodos():
    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(NOTICIAS_AC9_DEMO)
    conteos = analizador.conteo_por_periodo()

    periodos = {p for ps in conteos.values() for p in ps}
    assert len(periodos) >= 3
