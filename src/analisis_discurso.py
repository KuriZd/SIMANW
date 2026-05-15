from __future__ import annotations

import re
from collections import Counter
from itertools import islice

import nltk
from nltk import bigrams, trigrams
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize


STOPWORDS_ES_FALLBACK = {
    "a",
    "al",
    "como",
    "con",
    "de",
    "del",
    "el",
    "en",
    "es",
    "la",
    "las",
    "lo",
    "los",
    "para",
    "por",
    "que",
    "se",
    "son",
    "su",
    "sus",
    "un",
    "una",
    "y",
}


class AnalisisDiscurso:
    """
    AC-2: Analisis estadistico profundo de textos.

    Calcula n-gramas, riqueza lexica por secciones, entidades nombradas
    heuristicas y comparativas entre multiples documentos.
    """

    def __init__(self, idioma: str = "spanish") -> None:
        self.idioma = idioma
        self.stop_words = self._cargar_stopwords(idioma)

    def analizar(self, texto: str, titulo: str = "Documento") -> dict:
        """Analisis completo de un texto."""
        oraciones = self._sent_tokenize(texto)
        tokens_original = self._word_tokenize(texto)
        tokens_lower = [token.lower() for token in tokens_original]
        tokens_alfa = [token for token in tokens_lower if self._es_palabra(token) and len(token) > 2]
        tokens_filtrados = [token for token in tokens_alfa if token not in self.stop_words]

        bigramas = list(bigrams(tokens_filtrados))
        trigramas = list(trigrams(tokens_filtrados))

        riqueza_secciones = self._riqueza_por_seccion(tokens_filtrados, secciones=4)
        posibles_entidades = self._extraer_entidades(tokens_original)

        return {
            "titulo": titulo,
            "oraciones": len(oraciones),
            "palabras_totales": len(tokens_alfa),
            "vocabulario_unico": len(set(tokens_filtrados)),
            "riqueza_lexica_global": len(set(tokens_filtrados)) / max(len(tokens_filtrados), 1),
            "riqueza_por_seccion": riqueza_secciones,
            "promedio_palabras_oracion": len(tokens_alfa) / max(len(oraciones), 1),
            "top_unigramas": Counter(tokens_filtrados).most_common(10),
            "top_bigramas": Counter(bigramas).most_common(7),
            "top_trigramas": Counter(trigramas).most_common(5),
            "posibles_entidades": Counter(posibles_entidades).most_common(8),
        }

    def comparar_textos(self, analisis_lista: list[dict]) -> list[dict]:
        """Compara estadisticas entre multiples textos."""
        return [
            {
                "titulo": analisis["titulo"],
                "palabras": analisis["palabras_totales"],
                "vocabulario": analisis["vocabulario_unico"],
                "riqueza": analisis["riqueza_lexica_global"],
                "promedio_oracion": analisis["promedio_palabras_oracion"],
            }
            for analisis in analisis_lista
        ]

    def _sent_tokenize(self, texto: str) -> list[str]:
        try:
            return sent_tokenize(texto, language=self.idioma)
        except LookupError:
            return [parte.strip() for parte in re.split(r"[.!?]+", texto) if parte.strip()]

    def _word_tokenize(self, texto: str) -> list[str]:
        try:
            return word_tokenize(texto, language=self.idioma)
        except LookupError:
            return re.findall(r"\b[\wáéíóúÁÉÍÓÚñÑüÜ]+\b", texto)

    def _extraer_entidades(self, tokens_original: list[str]) -> list[str]:
        entidades = []
        for token in tokens_original:
            if not token:
                continue
            if token[0].isupper() and self._es_palabra(token) and len(token) > 2:
                if token.lower() not in self.stop_words:
                    entidades.append(token)
        return entidades

    @staticmethod
    def _riqueza_por_seccion(tokens: list[str], secciones: int) -> list[float]:
        if not tokens:
            return []

        tamano = max(len(tokens) // secciones, 1)
        riqueza = []
        for indice in range(secciones):
            inicio = indice * tamano
            fin = len(tokens) if indice == secciones - 1 else (indice + 1) * tamano
            seccion = list(islice(tokens, inicio, fin))
            if seccion:
                riqueza.append(len(set(seccion)) / len(seccion))
        return riqueza

    @staticmethod
    def _es_palabra(token: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-záéíóúÁÉÍÓÚñÑüÜ]+", token))

    @staticmethod
    def _cargar_stopwords(idioma: str) -> set[str]:
        try:
            return set(stopwords.words(idioma))
        except LookupError:
            try:
                nltk.download("stopwords", quiet=True)
                return set(stopwords.words(idioma))
            except LookupError:
                return STOPWORDS_ES_FALLBACK
