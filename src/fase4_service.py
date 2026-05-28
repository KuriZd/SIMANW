from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.comparador_busqueda import ComparadorModelos, generar_consultas_desde_corpus
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

    def buscar_con_modelo(self, consulta: str, modelo: str = "natural", top_k: int = 10) -> list[dict]:
        if not consulta.strip():
            return []
        modelo_norm = (modelo or "natural").strip().lower()
        if modelo_norm == "booleano":
            ids = self.motor.buscar_booleana(consulta, modo="AND")
            return [
                self._enriquecer_resultado({"doc_id": doc_id, "score": 1.0, "relevancia": 1.0})
                for doc_id in ids[:top_k]
            ]
        if modelo_norm == "vectorial":
            return [self._enriquecer_resultado(r) for r in self.motor.buscar_vectorial(consulta, top_k=top_k)]
        return self.buscar(consulta, top_k=top_k)

    def evaluar_modelos_busqueda(
        self,
        ruta: str | Path = "data/resultados_ac5.json",
        ruta_consultas: str | Path = "config/consultas_ac5.json",
    ) -> dict:
        if not self.corpus:
            return {
                "estado": "pendiente",
                "observacion": "No hay corpus indexado para evaluar AC-5.",
                "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            }

        consultas = self._cargar_consultas_relevancia(ruta_consultas)
        origen_consultas = "config/consultas_ac5.json"
        criterio_relevancia = "Juicios configurados por categoria en config/consultas_ac5.json."
        if not consultas:
            consultas = generar_consultas_desde_corpus(self.corpus)
            origen_consultas = "generado_desde_corpus"
            criterio_relevancia = "Documentos relevantes generados por categoria del corpus real."
        if not consultas:
            return {
                "estado": "pendiente",
                "observacion": "No se pudieron generar consultas con juicios de relevancia desde el corpus.",
                "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
                "total_documentos": len(self.corpus),
            }

        comparador = ComparadorModelos(self.corpus)
        payload = comparador.guardar_json(ruta, consultas)
        payload.update(
            {
                "estado": "completo",
                "ultima_ejecucion": payload.get("fecha_generacion"),
                "ejecutado_desde": "Search & Q&A",
                "archivo_json": str(ruta),
                "origen_consultas": origen_consultas,
                "criterio_relevancia": criterio_relevancia,
            }
        )
        return payload

    def info(self) -> dict:
        return self.motor.info_indice()

    def _cargar_consultas_relevancia(self, ruta_consultas: str | Path) -> list[dict]:
        ruta = Path(ruta_consultas)
        if not ruta.exists():
            return []
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(datos, list):
            return []

        consultas = []
        for item in datos:
            if not isinstance(item, dict):
                continue
            consulta = str(item.get("consulta", "") or "").strip()
            if not consulta:
                continue
            relevantes = item.get("relevantes")
            if isinstance(relevantes, list):
                ids = [int(idx) for idx in relevantes if isinstance(idx, int) and 0 <= idx < len(self.corpus)]
            else:
                categoria = str(item.get("categoria_relevante", "") or "").strip()
                ids = [
                    idx
                    for idx, doc in enumerate(self.corpus)
                    if categoria and _categoria(doc) == categoria
                ]
            if not ids:
                continue
            consultas.append(
                {
                    "consulta": consulta,
                    "relevantes": ids,
                    "criterio_relevancia": item.get("criterio_relevancia", "Juicio configurado."),
                }
            )
        return consultas

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
