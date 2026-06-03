"""Tests unitarios para Fase2Service."""
from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest

from src.fase2_service import Fase2Service, ResultadoFase2

# ── fixtures ─────────────────────────────────────────────────────────────────

NOTICIAS_PRUEBA = [
    {
        "titulo": "Avances en inteligencia artificial transforman industrias",
        "cuerpo": (
            "Los nuevos modelos de IA generativa están transformando múltiples "
            "industrias. Empresas de todo el mundo adoptan estas tecnologías."
        ),
        "fecha": "2026-05-10",
        "autor": "María García",
        "categoria": "tecnologia",
        "url": "https://ejemplo.com/noticia1",
    },
    {
        "titulo": "Crecimiento económico en México durante primer trimestre",
        "cuerpo": (
            "La economía mexicana creció un tres por ciento en el primer "
            "trimestre del año según reportes oficiales del gobierno."
        ),
        "fecha": "2026-05-11",
        "autor": "Juan López",
        "categoria": "economia",
        "url": "https://ejemplo.com/noticia2",
    },
]

CAMPOS_ESPERADOS = [
    "titulo", "fecha", "autor", "categoria", "url",
    "texto_original", "texto_limpio",
    "tokens", "terminos", "stems",
    "num_tokens", "num_terminos", "num_oraciones",
    "vocabulario_unico", "riqueza_lexica",
    "terminos_relevantes", "noticias_similares",
]


# ── tests ─────────────────────────────────────────────────────────────────────

def test_procesar_corpus_devuelve_dos_items():
    """Procesar 2 noticias produce corpus con exactamente 2 items."""
    service = Fase2Service()
    resultado = service.procesar_corpus(NOTICIAS_PRUEBA)

    assert isinstance(resultado, ResultadoFase2)
    assert len(resultado.corpus) == 2


def test_item_tiene_schema_completo():
    """Cada item del corpus tiene todos los campos esperados con tipos correctos."""
    service = Fase2Service()
    resultado = service.procesar_corpus(NOTICIAS_PRUEBA)
    item = resultado.corpus[0]

    for campo in CAMPOS_ESPERADOS:
        assert campo in item, f"Falta campo: {campo}"

    assert isinstance(item["titulo"], str)
    assert isinstance(item["tokens"], list)
    assert isinstance(item["terminos"], list)
    assert isinstance(item["stems"], list)
    assert isinstance(item["terminos_relevantes"], list)
    assert isinstance(item["noticias_similares"], list)
    assert isinstance(item["num_tokens"], int)
    assert isinstance(item["num_terminos"], int)
    assert isinstance(item["num_oraciones"], int)
    assert isinstance(item["vocabulario_unico"], int)
    assert isinstance(item["riqueza_lexica"], float)
    assert 0.0 <= item["riqueza_lexica"] <= 1.0


def test_originales_no_mutados():
    """procesar_corpus no debe añadir la clave 'nlp' a los dicts originales."""
    service = Fase2Service()
    snapshot = copy.deepcopy(NOTICIAS_PRUEBA)

    service.procesar_corpus(NOTICIAS_PRUEBA)

    for original, despues in zip(snapshot, NOTICIAS_PRUEBA):
        assert "nlp" not in despues, "La clave 'nlp' fue añadida al dict original"
        assert original == despues, "El dict original fue mutado"


def test_entrada_vacia_lanza_value_error():
    """Pasar lista vacía debe lanzar ValueError."""
    service = Fase2Service()
    with pytest.raises(ValueError, match="Fase 1"):
        service.procesar_corpus([])


def test_obtener_frecuencias_devuelve_terminos():
    """obtener_frecuencias devuelve lista de (str, int) no vacía."""
    service = Fase2Service()
    resultado = service.procesar_corpus(NOTICIAS_PRUEBA)
    frecuencias = service.obtener_frecuencias(resultado.corpus, top_n=5)

    assert len(frecuencias) > 0
    assert len(frecuencias) <= 5
    for termino, conteo in frecuencias:
        assert isinstance(termino, str)
        assert isinstance(conteo, int)
        assert conteo >= 1


def test_exportar_json_crea_archivo(tmp_path: Path):
    """exportar_json crea el archivo y es JSON válido con 2 items."""
    service = Fase2Service()
    resultado = service.procesar_corpus(NOTICIAS_PRUEBA)
    ruta = tmp_path / "corpus.json"

    path = service.exportar_json(resultado.corpus, ruta)

    assert path.exists()
    datos = json.loads(path.read_text(encoding="utf-8"))
    assert len(datos) == 2
    assert datos[0]["titulo"] == NOTICIAS_PRUEBA[0]["titulo"]


def test_exportar_csv_crea_archivo(tmp_path: Path):
    """exportar_csv crea el archivo CSV."""
    service = Fase2Service()
    resultado = service.procesar_corpus(NOTICIAS_PRUEBA)
    ruta = tmp_path / "corpus.csv"

    path = service.exportar_csv(resultado.corpus, ruta)

    assert path.exists()
    contenido = path.read_text(encoding="utf-8")
    assert len(contenido) > 0


def test_csv_serializa_listas_como_strings(tmp_path: Path):
    """El CSV no debe contener sintaxis de lista Python ('[', ']')."""
    service = Fase2Service()
    resultado = service.procesar_corpus(NOTICIAS_PRUEBA)
    ruta = tmp_path / "corpus.csv"
    path = service.exportar_csv(resultado.corpus, ruta)

    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        filas = list(reader)

    assert len(filas) == 2
    fila = filas[0]

    # tokens debe ser cadena de palabras separadas por espacios, no repr de lista
    assert isinstance(fila["tokens"], str)
    assert "[" not in fila["tokens"], "tokens contiene corchetes (lista sin aplanar)"
    assert "[" not in fila["terminos"], "terminos contiene corchetes"
    assert "[" not in fila["stems"], "stems contiene corchetes"

    # terminos_relevantes debe ser string (puede estar vacío si TF-IDF falla)
    assert isinstance(fila["terminos_relevantes"], str)


def test_tfidf_falla_corpus_valido(monkeypatch):
    """Si TF-IDF no está disponible el corpus se genera igual con terminos_relevantes=[]."""
    import src.fase2_service as f2
    monkeypatch.setattr(f2, "_TFIDF_DISPONIBLE", False)

    service = Fase2Service()
    resultado = service.procesar_corpus(NOTICIAS_PRUEBA)

    assert len(resultado.corpus) == 2
    for item in resultado.corpus:
        assert item["terminos_relevantes"] == []
    assert len(resultado.errores) > 0
    assert any("RepresentacionVectorial" in e or "TF-IDF" in e for e in resultado.errores)


def test_procesar_corpus_incluye_similitud_y_grupos():
    service = Fase2Service()
    resultado = service.procesar_corpus(NOTICIAS_PRUEBA)

    assert "grupos_similares" in resultado.estadisticas
    assert "pares_similares" in resultado.estadisticas
    assert len(resultado.estadisticas["pares_similares"]) == len(NOTICIAS_PRUEBA)
    assert all("noticias_similares" in item for item in resultado.corpus)
