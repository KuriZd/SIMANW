from __future__ import annotations

import re
import unicodedata

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ComparadorModelos:
    """
    AC-5: Compara formalmente modelo booleano vs. vectorial.
    """

    def __init__(self, documentos: list[dict]) -> None:
        if not documentos:
            raise ValueError("Se necesita al menos un documento para comparar modelos")

        self.documentos = documentos
        self.textos = [f"{documento['titulo']} {documento['cuerpo']}" for documento in documentos]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode", lowercase=True)
        self.matriz = self.vectorizer.fit_transform(self.textos)
        self.indice: dict[str, set[int]] = {}
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
        booleano_result = self.busqueda_booleana(consulta)
        booleano_metricas = self._metricas(booleano_result, relevantes)

        vectorial_result = [indice for indice, _ in self.busqueda_vectorial(consulta, top_k=len(self.documentos))]
        vectorial_top_k = vectorial_result[: len(booleano_result)] if booleano_result else vectorial_result[:3]
        vectorial_metricas = self._metricas(vectorial_top_k, relevantes)

        return {
            "consulta": consulta,
            "booleano": {
                "recuperados": len(booleano_result),
                **booleano_metricas,
            },
            "vectorial": {
                "recuperados": len(vectorial_top_k),
                **vectorial_metricas,
            },
        }

    def evaluar_consultas(self, consultas_eval: list[dict]) -> dict:
        resultados = [self.evaluar_ambos(item["consulta"], item["relevantes"]) for item in consultas_eval]
        promedio_booleano = self._promedio(resultados, "booleano")
        promedio_vectorial = self._promedio(resultados, "vectorial")
        ganador = "vectorial" if promedio_vectorial["precision"] > promedio_booleano["precision"] else "booleano"

        return {
            "resultados": resultados,
            "promedio_booleano": promedio_booleano,
            "promedio_vectorial": promedio_vectorial,
            "ganador_precision": ganador,
        }

    def reporte(self, consultas_eval: list[dict]) -> str:
        evaluacion = self.evaluar_consultas(consultas_eval)
        lineas = [f"{'Consulta':<30} | {'Modelo':<10} | {'Recup':>5} | {'Prec':>6} | {'Recall':>6}"]
        lineas.append("-" * 75)

        for resultado in evaluacion["resultados"]:
            booleano = resultado["booleano"]
            vectorial = resultado["vectorial"]
            lineas.append(
                f"{resultado['consulta']:<30} | {'Booleano':<10} | {booleano['recuperados']:>5} | "
                f"{booleano['precision']:>6.3f} | {booleano['recall']:>6.3f}"
            )
            lineas.append(
                f"{'':30} | {'Vectorial':<10} | {vectorial['recuperados']:>5} | "
                f"{vectorial['precision']:>6.3f} | {vectorial['recall']:>6.3f}"
            )
            lineas.append("")

        promedio_bool = evaluacion["promedio_booleano"]
        promedio_vec = evaluacion["promedio_vectorial"]
        lineas.append("-" * 75)
        lineas.append(
            f"{'PROMEDIO':<30} | {'Booleano':<10} | {'':>5} | "
            f"{promedio_bool['precision']:>6.3f} | {promedio_bool['recall']:>6.3f}"
        )
        lineas.append(
            f"{'':30} | {'Vectorial':<10} | {'':>5} | "
            f"{promedio_vec['precision']:>6.3f} | {promedio_vec['recall']:>6.3f}"
        )
        lineas.append(
            f"\nConclusion: El modelo {evaluacion['ganador_precision']} tiene mejor precision promedio."
        )
        return "\n".join(lineas)

    def _construir_indice(self) -> None:
        for indice_doc, texto in enumerate(self.textos):
            for termino in self._tokenizar(texto):
                self.indice.setdefault(termino, set()).add(indice_doc)

    @staticmethod
    def _metricas(recuperados: list[int], relevantes: list[int]) -> dict:
        recuperados_set = set(recuperados)
        relevantes_set = set(relevantes)
        interseccion = recuperados_set & relevantes_set
        return {
            "precision": len(interseccion) / max(len(recuperados_set), 1),
            "recall": len(interseccion) / max(len(relevantes_set), 1),
        }

    @staticmethod
    def _promedio(resultados: list[dict], modelo: str) -> dict:
        total = max(len(resultados), 1)
        return {
            "precision": sum(resultado[modelo]["precision"] for resultado in resultados) / total,
            "recall": sum(resultado[modelo]["recall"] for resultado in resultados) / total,
        }

    @classmethod
    def _tokenizar(cls, texto: str) -> list[str]:
        texto = unicodedata.normalize("NFKD", texto.lower())
        texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
        return re.findall(r"\b\w+\b", texto)


CONSULTAS_EVAL_AC5 = [
    {"consulta": "inteligencia artificial", "relevantes": [0, 3]},
    {"consulta": "mercados volatilidad economia", "relevantes": [1]},
    {"consulta": "datos abiertos gobierno", "relevantes": [4]},
    {"consulta": "cambio climatico cientifico", "relevantes": [2]},
]
