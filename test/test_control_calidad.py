"""Tests para AC-8: Control de calidad del corpus rastreado."""
from src.control_calidad import ControlCalidadCorpus


def _noticia_valida(**kwargs) -> dict:
    base = {
        "titulo": "Avances en inteligencia artificial",
        "cuerpo": "Los nuevos modelos de IA están transformando múltiples industrias en todo el mundo.",
        "fecha": "2026-05-10",
        "autor": "María García",
        "categoria_original": "tecnologia",
        "url": "https://portal.com/noticias/ia-2026",
        "fuente": "https://portal.com",
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Corpus válido
# ---------------------------------------------------------------------------

def test_corpus_valido_no_genera_rechazados():
    corpus = [_noticia_valida(), _noticia_valida(url="https://portal.com/otra", titulo="Otra noticia diferente")]
    ctrl = ControlCalidadCorpus()
    depurado = ctrl.validar(corpus)
    assert len(depurado) == 2
    assert len(ctrl.registros_rechazados) == 0


def test_informe_totales_correctos():
    corpus = [_noticia_valida()]
    ctrl = ControlCalidadCorpus()
    ctrl.validar(corpus)
    informe = ctrl.generar_informe()
    assert informe["total_registros"] == 1
    assert informe["registros_validos"] == 1
    assert informe["registros_rechazados"] == 0


# ---------------------------------------------------------------------------
# Campos obligatorios
# ---------------------------------------------------------------------------

def test_rechaza_campo_faltante():
    registro = _noticia_valida()
    del registro["titulo"]
    ctrl = ControlCalidadCorpus()
    ctrl.validar([registro])
    assert len(ctrl.registros_rechazados) == 1
    assert any("titulo" in m for m in ctrl.registros_rechazados[0]["motivos"])


def test_rechaza_campo_vacio():
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida(autor="")])
    assert len(ctrl.registros_rechazados) == 1


# ---------------------------------------------------------------------------
# Longitudes mínimas
# ---------------------------------------------------------------------------

def test_rechaza_cuerpo_corto():
    ctrl = ControlCalidadCorpus(longitud_minima_cuerpo=50)
    ctrl.validar([_noticia_valida(cuerpo="Muy corto.")])
    assert len(ctrl.registros_rechazados) == 1
    assert any("cuerpo" in m for m in ctrl.registros_rechazados[0]["motivos"])


def test_rechaza_titulo_corto():
    ctrl = ControlCalidadCorpus(longitud_minima_titulo=5)
    ctrl.validar([_noticia_valida(titulo="IA")])
    assert len(ctrl.registros_rechazados) == 1
    assert any("título" in m for m in ctrl.registros_rechazados[0]["motivos"])


def test_acepta_cuerpo_en_el_limite():
    cuerpo_exacto = "x" * 50
    ctrl = ControlCalidadCorpus(longitud_minima_cuerpo=50)
    depurado = ctrl.validar([_noticia_valida(cuerpo=cuerpo_exacto)])
    assert len(depurado) == 1


# ---------------------------------------------------------------------------
# Formato de fecha
# ---------------------------------------------------------------------------

def test_rechaza_fecha_formato_incorrecto():
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida(fecha="10/05/2026")])
    assert len(ctrl.registros_rechazados) == 1
    assert any("fecha" in m for m in ctrl.registros_rechazados[0]["motivos"])


def test_acepta_fecha_iso():
    ctrl = ControlCalidadCorpus()
    depurado = ctrl.validar([_noticia_valida(fecha="2026-01-31")])
    assert len(depurado) == 1


# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------

def test_rechaza_url_sin_protocolo():
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida(url="portal.com/noticia")])
    assert len(ctrl.registros_rechazados) == 1
    assert any("url" in m for m in ctrl.registros_rechazados[0]["motivos"])


def test_rechaza_fuente_sin_protocolo():
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida(fuente="portal.com")])
    assert len(ctrl.registros_rechazados) == 1
    assert any("fuente" in m for m in ctrl.registros_rechazados[0]["motivos"])


# ---------------------------------------------------------------------------
# Duplicados exactos (URL)
# ---------------------------------------------------------------------------

def test_rechaza_duplicado_exacto_url():
    n1 = _noticia_valida()
    n2 = _noticia_valida(titulo="Otro título completamente distinto")  # misma URL
    ctrl = ControlCalidadCorpus()
    depurado = ctrl.validar([n1, n2])
    assert len(depurado) == 1
    assert len(ctrl.registros_rechazados) == 1
    assert any("duplicado exacto" in m for m in ctrl.registros_rechazados[0]["motivos"])


def test_duplicado_url_case_insensitive():
    n1 = _noticia_valida(url="https://PORTAL.COM/noticias/ia-2026")
    n2 = _noticia_valida(url="https://portal.com/noticias/ia-2026", titulo="Otro título largo")
    ctrl = ControlCalidadCorpus()
    depurado = ctrl.validar([n1, n2])
    assert len(depurado) == 1


# ---------------------------------------------------------------------------
# Duplicados casi idénticos (título)
# ---------------------------------------------------------------------------

def test_rechaza_duplicado_por_titulo_normalizado():
    n1 = _noticia_valida()
    n2 = _noticia_valida(
        url="https://portal.com/otra-url-diferente",
        titulo="  Avances en INTELIGENCIA ARTIFICIAL  ",  # mismo título, distinto case/espacios
    )
    ctrl = ControlCalidadCorpus()
    depurado = ctrl.validar([n1, n2])
    assert len(depurado) == 1
    assert any("duplicado por título" in m for m in ctrl.registros_rechazados[0]["motivos"])


# ---------------------------------------------------------------------------
# Informe detallado y párrafo resumen
# ---------------------------------------------------------------------------

def test_informe_contiene_detalle_rechazados():
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida(fecha="bad-date")])
    informe = ctrl.generar_informe()
    assert len(informe["detalle_rechazados"]) == 1
    assert "motivos" in informe["detalle_rechazados"][0]


def test_parrafo_sin_rechazados():
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida()])
    parrafo = ctrl.parrafo_resumen()
    assert len(parrafo.split()) <= 200
    assert "corpus depurado" in parrafo.lower()


def test_parrafo_con_rechazados():
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida(), _noticia_valida(fecha="01-01-2026")])
    parrafo = ctrl.parrafo_resumen()
    assert len(parrafo.split()) <= 200
    assert "descartaron" in parrafo


def test_guardar_informe_crea_archivo(tmp_path):
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida()])
    ruta = ctrl.guardar_informe(tmp_path / "informe.json")
    assert ruta.exists()
    import json
    data = json.loads(ruta.read_text(encoding="utf-8"))
    assert "total_registros" in data


# ---------------------------------------------------------------------------
# Reuso: validar() reinicia el estado
# ---------------------------------------------------------------------------

def test_segunda_llamada_reinicia_estado():
    ctrl = ControlCalidadCorpus()
    ctrl.validar([_noticia_valida(fecha="bad")])
    assert len(ctrl.registros_rechazados) == 1

    ctrl.validar([_noticia_valida()])
    assert len(ctrl.registros_rechazados) == 0
    assert len(ctrl.corpus_depurado) == 1
