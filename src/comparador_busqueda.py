from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.evaluador_irs import EvaluadorIRS


class ComparadorModelos:
    """
    AC-5: Compara formalmente modelo booleano vs. vectorial.
    """

    def __init__(self, documentos: list[dict]) -> None:
        if not documentos:
            raise ValueError("Se necesita al menos un documento para comparar modelos")

        self.documentos = [_normalizar_documento(documento) for documento in documentos]
        self.textos = [f"{documento['titulo']} {documento['cuerpo']}" for documento in self.documentos]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode", lowercase=True)
        self.matriz = self.vectorizer.fit_transform(self.textos)
        self.indice: dict[str, set[int]] = {}
        self.evaluador = EvaluadorIRS()
        self._construir_indice()

    def busqueda_booleana(self, consulta: str) -> list[int]:
        """Modelo booleano: AND de todos los terminos."""
        terminos = self._tokenizar(consulta)
        if not terminos:
            return []

        resultado = self.indice.get(terminos[0], set()).copy()
        for termino in terminos[1:]:
            resultado &= self.indice.get(termino, set())
        return sorted(resultado)

    def busqueda_vectorial(self, consulta: str, top_k: int = 5) -> list[tuple[int, float]]:
        """Modelo vectorial: ranking por similitud coseno."""
        consulta_vec = self.vectorizer.transform([consulta])
        similitudes = cosine_similarity(consulta_vec, self.matriz)[0]
        indices = similitudes.argsort()[::-1][:top_k]
        return [(int(indice), float(similitudes[indice])) for indice in indices if similitudes[indice] > 0]

    def evaluar_ambos(self, consulta: str, relevantes: list[int]) -> dict:
        """Evalua ambos modelos con la misma consulta y juicio de relevancia."""
        relevantes = [idx for idx in relevantes if 0 <= idx < len(self.documentos)]
        booleano_result = self.busqueda_booleana(consulta)
        booleano_metricas = self._metricas(booleano_result, relevantes)

        vectorial_result = [indice for indice, _ in self.busqueda_vectorial(consulta, top_k=len(self.documentos))]
        vectorial_metricas = self._metricas(vectorial_result, relevantes)

        return {
            "consulta": consulta,
            "relevantes": relevantes,
            "booleano": {
                "recuperados": len(booleano_result),
                "recuperados_ids": booleano_result,
                **booleano_metricas,
            },
            "vectorial": {
                "recuperados": len(vectorial_result),
                "recuperados_ids": vectorial_result,
                **vectorial_metricas,
            },
        }

    def evaluar_consultas(self, consultas_eval: list[dict]) -> dict:
        resultados = [self.evaluar_ambos(item["consulta"], item["relevantes"]) for item in consultas_eval]
        promedio_booleano = self._promedio(resultados, "booleano")
        promedio_vectorial = self._promedio(resultados, "vectorial")
        ganador_prec = "vectorial" if promedio_vectorial["precision"] > promedio_booleano["precision"] else "booleano"
        ganador_f1 = "vectorial" if promedio_vectorial["f1"] > promedio_booleano["f1"] else "booleano"
        ganador_map = (
            "vectorial"
            if promedio_vectorial["average_precision"] > promedio_booleano["average_precision"]
            else "booleano"
        )

        return {
            "resultados": resultados,
            "promedio_booleano": promedio_booleano,
            "promedio_vectorial": promedio_vectorial,
            "ganador_precision": ganador_prec,
            "ganador_f1": ganador_f1,
            "ganador_map": ganador_map,
            "map_booleano": promedio_booleano["average_precision"],
            "map_vectorial": promedio_vectorial["average_precision"],
        }

    def reporte(self, consultas_eval: list[dict]) -> str:
        evaluacion = self.evaluar_consultas(consultas_eval)
        lineas = [
            f"{'Consulta':<30} | {'Modelo':<10} | {'Recup':>5} | {'Prec':>6} | {'Recall':>6} | {'F1':>6} | {'P@5':>6} | {'AP':>6}"
        ]
        lineas.append("-" * 102)

        for resultado in evaluacion["resultados"]:
            booleano = resultado["booleano"]
            vectorial = resultado["vectorial"]
            lineas.append(
                f"{resultado['consulta']:<30} | {'Booleano':<10} | {booleano['recuperados']:>5} | "
                f"{booleano['precision']:>6.3f} | {booleano['recall']:>6.3f} | {booleano['f1']:>6.3f} | "
                f"{booleano['precision_at_k']:>6.3f} | {booleano['average_precision']:>6.3f}"
            )
            lineas.append(
                f"{'':30} | {'Vectorial':<10} | {vectorial['recuperados']:>5} | "
                f"{vectorial['precision']:>6.3f} | {vectorial['recall']:>6.3f} | {vectorial['f1']:>6.3f} | "
                f"{vectorial['precision_at_k']:>6.3f} | {vectorial['average_precision']:>6.3f}"
            )
            lineas.append("")

        promedio_bool = evaluacion["promedio_booleano"]
        promedio_vec = evaluacion["promedio_vectorial"]
        lineas.append("-" * 102)
        lineas.append(
            f"{'PROMEDIO':<30} | {'Booleano':<10} | {'':>5} | "
            f"{promedio_bool['precision']:>6.3f} | {promedio_bool['recall']:>6.3f} | {promedio_bool['f1']:>6.3f} | "
            f"{promedio_bool['precision_at_k']:>6.3f} | {promedio_bool['average_precision']:>6.3f}"
        )
        lineas.append(
            f"{'':30} | {'Vectorial':<10} | {'':>5} | "
            f"{promedio_vec['precision']:>6.3f} | {promedio_vec['recall']:>6.3f} | {promedio_vec['f1']:>6.3f} | "
            f"{promedio_vec['precision_at_k']:>6.3f} | {promedio_vec['average_precision']:>6.3f}"
        )
        lineas.append(
            f"\nConclusion: {self.generar_conclusion(evaluacion)}"
        )
        return "\n".join(lineas)

    def generar_conclusion(self, evaluacion: dict | None = None) -> str:
        """Genera conclusión textual basada en F1 promedio de ambos modelos."""
        if evaluacion is None:
            raise ValueError("Proporciona el dict de evaluar_consultas() o llama a reporte().")
        pb = evaluacion["promedio_booleano"]
        pv = evaluacion["promedio_vectorial"]
        ganador = evaluacion["ganador_f1"]
        diff = abs(pv["f1"] - pb["f1"])
        if diff < 0.05:
            return (
                f"Ambos modelos tienen rendimiento similar (F1 Booleano={pb['f1']:.3f}, "
                f"Vectorial={pv['f1']:.3f}). El modelo vectorial es preferible por su ranking graduado."
            )
        return (
            f"El modelo {ganador} supera al rival en F1 promedio "
            f"(Booleano={pb['f1']:.3f}, Vectorial={pv['f1']:.3f}). "
            f"{'El modelo vectorial captura similitud semantica parcial.' if ganador == 'vectorial' else 'El modelo booleano ofrece mayor exactitud en este corpus.'}"
        )

    def guardar_json(self, ruta: str | Path, consultas_eval: list[dict]) -> dict:
        """Exporta evaluación completa a JSON compatible con pipeline SIMANW."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        evaluacion = self.evaluar_consultas(consultas_eval)
        payload = {
            "actividad": "AC-5",
            "descripcion": "Evaluacion comparativa modelos booleano vs vectorial",
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "total_documentos": len(self.documentos),
            "total_consultas": len(consultas_eval),
            "ganador_precision": evaluacion["ganador_precision"],
            "ganador_f1": evaluacion["ganador_f1"],
            "ganador_map": evaluacion["ganador_map"],
            "conclusion": self.generar_conclusion(evaluacion),
            "promedio_booleano": evaluacion["promedio_booleano"],
            "promedio_vectorial": evaluacion["promedio_vectorial"],
            "map_booleano": evaluacion["map_booleano"],
            "map_vectorial": evaluacion["map_vectorial"],
            "resultados": evaluacion["resultados"],
        }
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(payload, archivo, ensure_ascii=False, indent=2)
        return payload

    def _construir_indice(self) -> None:
        for indice_doc, texto in enumerate(self.textos):
            for termino in self._tokenizar(texto):
                self.indice.setdefault(termino, set()).add(indice_doc)

    @staticmethod
    def _metricas(recuperados: list[int], relevantes: list[int]) -> dict:
        evaluador = EvaluadorIRS()
        precision = evaluador.precision(recuperados, relevantes)
        recall = evaluador.recall(recuperados, relevantes)
        f1 = evaluador.f1(precision, recall)
        k = min(5, max(len(recuperados), len(relevantes), 1))
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "precision_at_k": evaluador.precision_at_k(recuperados, relevantes, k),
            "average_precision": evaluador.average_precision(recuperados, relevantes),
            "k": k,
        }

    @staticmethod
    def _promedio(resultados: list[dict], modelo: str) -> dict:
        total = max(len(resultados), 1)
        return {
            "precision": sum(r[modelo]["precision"] for r in resultados) / total,
            "recall": sum(r[modelo]["recall"] for r in resultados) / total,
            "f1": sum(r[modelo]["f1"] for r in resultados) / total,
            "precision_at_k": sum(r[modelo]["precision_at_k"] for r in resultados) / total,
            "average_precision": sum(r[modelo]["average_precision"] for r in resultados) / total,
        }

    @classmethod
    def _tokenizar(cls, texto: str) -> list[str]:
        texto = unicodedata.normalize("NFKD", texto.lower())
        texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
        return re.findall(r"\b\w+\b", texto)


def cargar_documentos_desde_json(ruta: str | Path) -> list[dict]:
    """Carga documentos desde JSON SIMANW. Acepta noticias con titulo+cuerpo/resumen."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if not isinstance(datos, list):
        raise ValueError("El JSON debe contener una lista de documentos")
    documentos: list[dict] = []
    for item in datos:
        titulo = item.get("titulo", "")
        cuerpo = item.get("cuerpo") or item.get("resumen") or ""
        if titulo or cuerpo:
            documentos.append({"titulo": titulo, "cuerpo": cuerpo})
    if not documentos:
        raise ValueError("No se encontraron documentos válidos en el JSON")
    return documentos


def generar_consultas_desde_corpus(documentos: list[dict], max_consultas: int = 5) -> list[dict]:
    """Genera consultas y juicios de relevancia reproducibles desde categorias del corpus.

    Los juicios se consideran academicos/simulados: documentos de la misma categoria
    son relevantes para una consulta formada con terminos frecuentes de esa categoria.
    """
    por_categoria: dict[str, list[int]] = defaultdict(list)
    terminos_categoria: dict[str, Counter] = defaultdict(Counter)

    for idx, doc in enumerate(documentos):
        categoria = (
            doc.get("categoria_predicha")
            or doc.get("categoria_original")
            or doc.get("categoria")
            or "sin_categoria"
        )
        if categoria == "sin_categoria":
            continue
        por_categoria[str(categoria)].append(idx)
        terminos = doc.get("terminos_relevantes") or doc.get("terminos") or []
        if not terminos:
            terminos = ComparadorModelos._tokenizar(f"{doc.get('titulo', '')} {doc.get('cuerpo', '')}")
        terminos_categoria[str(categoria)].update(str(t) for t in terminos if len(str(t)) > 3)

    consultas = []
    for categoria, indices in sorted(por_categoria.items(), key=lambda item: (-len(item[1]), item[0])):
        if not indices:
            continue
        terminos = [termino for termino, _ in terminos_categoria[categoria].most_common(3)]
        if not terminos:
            terminos = [categoria]
        consultas.append(
            {
                "consulta": " ".join(terminos),
                "relevantes": indices,
                "criterio_relevancia": f"categoria={categoria}",
            }
        )
        if len(consultas) >= max_consultas:
            break
    return consultas


def _normalizar_documento(documento: dict) -> dict:
    normalizado = dict(documento)
    normalizado["titulo"] = str(documento.get("titulo", "") or "")
    normalizado["cuerpo"] = str(
        documento.get("cuerpo")
        or documento.get("texto_original")
        or documento.get("resumen")
        or documento.get("texto_limpio")
        or ""
    )
    return normalizado


CONSULTAS_EVAL_AC5 = [
    {"consulta": "inteligencia artificial", "relevantes": [0, 3]},
    {"consulta": "mercados volatilidad economia", "relevantes": [1]},
    {"consulta": "datos abiertos gobierno", "relevantes": [4]},
    {"consulta": "cambio climatico cientifico", "relevantes": [2]},
]
