from __future__ import annotations

from src.motor_busqueda import MotorBusqueda

try:
    from src.busqueda_natural import BusquedaNatural
except ImportError:  # pragma: no cover - fallback defensivo
    BusquedaNatural = None  # type: ignore[assignment]


class Fase4Service:
    """Capa de busqueda: indice TF-IDF, ranking y busqueda natural."""

    def __init__(self) -> None:
        self.motor = MotorBusqueda()
        self.busqueda_natural = None
        self.corpus: list[dict] = []

    def construir_indice(self, corpus_procesado: list[dict]) -> None:
        if not corpus_procesado:
            raise ValueError("No hay corpus procesado para indexar.")
        self.corpus = [_normalizar_documento(doc) for doc in corpus_procesado]
        self.motor.indexar(self.corpus)
        if BusquedaNatural is not None:
            self.busqueda_natural = BusquedaNatural(self.motor)

    def buscar(self, consulta: str, top_k: int = 10) -> list[dict]:
        if not consulta.strip():
            return []
        if self.busqueda_natural is not None:
            resultados = self.busqueda_natural.buscar_natural(consulta, top_k=top_k)
        else:
            resultados = self.motor.buscar_vectorial(consulta, top_k=top_k)
        return [self._enriquecer_resultado(resultado) for resultado in resultados]

    def info(self) -> dict:
        return self.motor.info_indice()

    def _enriquecer_resultado(self, resultado: dict) -> dict:
        doc = self.corpus[resultado.get("doc_id", -1)] if resultado.get("doc_id", -1) in range(len(self.corpus)) else {}
        score = resultado.get("score", resultado.get("relevancia", 0.0))
        return {
            "titulo": resultado.get("titulo", doc.get("titulo", "")),
            "categoria": resultado.get("categoria", _categoria(doc)),
            "sentimiento": resultado.get("sentimiento", _sentimiento(doc)),
            "fecha": resultado.get("fecha", doc.get("fecha", "")),
            "url": resultado.get("url", doc.get("url", "")),
            "score": float(score or 0.0),
            "snippet": resultado.get("snippet", _snippet(doc.get("cuerpo", ""))),
            "doc_id": resultado.get("doc_id"),
        }


def _normalizar_documento(doc: dict) -> dict:
    normalizado = dict(doc)
    normalizado["cuerpo"] = doc.get("cuerpo") or doc.get("texto_original") or doc.get("texto_limpio") or ""
    normalizado["categoria_original"] = doc.get("categoria_original") or doc.get("categoria") or "sin_categoria"
    return normalizado


def _categoria(doc: dict) -> str:
    return doc.get("categoria_predicha", doc.get("categoria_original", doc.get("categoria", "?")))


def _sentimiento(doc: dict) -> str:
    return doc.get("sentimiento", {}).get("etiqueta", "?")


def _snippet(texto: str, longitud: int = 120) -> str:
    return texto[:longitud] + ("..." if len(texto) > longitud else "")
