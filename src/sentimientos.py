from __future__ import annotations

import re
from collections import Counter

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer


PALABRAS_POSITIVAS = {
    "avance",
    "avances",
    "celebra",
    "celebran",
    "crecimiento",
    "innovadora",
    "mejora",
    "mejoras",
    "mejoran",
    "nuevo",
    "nueva",
    "oportunidad",
    "optimiza",
    "positiva",
    "revolucionan",
    "significativas",
}

PALABRAS_NEGATIVAS = {
    "alarma",
    "bajaron",
    "caidas",
    "caídas",
    "crisis",
    "incertidumbre",
    "negativa",
    "peores",
    "preocupacion",
    "preocupante",
    "preocupantes",
    "riesgo",
    "tensiones",
    "volatilidad",
    "volatiles",
}


class AnalizadorSentimientos:
    """Analiza el sentimiento de las noticias del SIMANW."""

    def __init__(self) -> None:
        self._asegurar_recurso_vader()
        self.sia = SentimentIntensityAnalyzer()

    def analizar(self, texto: str) -> dict:
        scores = self.sia.polarity_scores(texto)
        compound = self._ajustar_compound_espanol(texto, scores["compound"])

        if compound >= 0.05:
            etiqueta = "positivo"
        elif compound <= -0.05:
            etiqueta = "negativo"
        else:
            etiqueta = "neutral"

        return {
            "positivo": float(scores["pos"]),
            "negativo": float(scores["neg"]),
            "neutral": float(scores["neu"]),
            "compound": float(compound),
            "etiqueta": etiqueta,
        }

    def analizar_corpus(self, documentos: list[str]) -> tuple[list[dict], dict]:
        if not documentos:
            return [], {
                "distribucion": {},
                "sentimiento_promedio": 0.0,
                "tono_general": "neutral",
            }

        resultados = [self.analizar(documento) for documento in documentos]
        distribucion = Counter(resultado["etiqueta"] for resultado in resultados)
        promedio = sum(resultado["compound"] for resultado in resultados) / len(resultados)

        if promedio > 0.05:
            tono_general = "positivo"
        elif promedio < -0.05:
            tono_general = "negativo"
        else:
            tono_general = "neutral"

        return resultados, {
            "distribucion": dict(distribucion),
            "sentimiento_promedio": float(promedio),
            "tono_general": tono_general,
        }

    def analizar_noticias(self, noticias: list[dict]) -> tuple[list[dict], dict]:
        documentos = [noticia["cuerpo"] for noticia in noticias]
        resultados, resumen = self.analizar_corpus(documentos)

        for noticia, sentimiento in zip(noticias, resultados):
            noticia["sentimiento"] = sentimiento

        return resultados, resumen

    @staticmethod
    def _asegurar_recurso_vader() -> None:
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)

    @staticmethod
    def _ajustar_compound_espanol(texto: str, compound_vader: float) -> float:
        if abs(compound_vader) >= 0.05:
            return compound_vader

        tokens = set(re.findall(r"\b[\wáéíóúñü]+\b", texto.lower()))
        positivos = len(tokens & PALABRAS_POSITIVAS)
        negativos = len(tokens & PALABRAS_NEGATIVAS)
        total = positivos + negativos

        if total == 0:
            return compound_vader

        return max(min((positivos - negativos) / total, 1.0), -1.0)
