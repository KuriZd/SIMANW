from __future__ import annotations

import re
from collections import Counter

import nltk
from nltk import bigrams, trigrams
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import sent_tokenize, word_tokenize


class PipelineNLP:
    """Pipeline de procesamiento de lenguaje natural del SIMANW."""

    def __init__(self, idioma: str = "spanish") -> None:
        self.idioma = idioma
        self._asegurar_recursos_nltk()
        self.stemmer = SnowballStemmer(idioma)
        self.stop_words = set(stopwords.words(idioma))

    def limpiar(self, texto: str) -> str:
        """Normaliza texto para tokenizacion y calculos posteriores."""
        texto = texto.lower()
        texto = re.sub(r"[^\w\sáéíóúñü]", " ", texto)
        texto = re.sub(r"\d+", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto

    def tokenizar(self, texto: str) -> list[str]:
        return word_tokenize(texto, language=self.idioma)

    def eliminar_stopwords(self, tokens: list[str]) -> list[str]:
        return [token for token in tokens if token not in self.stop_words and len(token) > 2]

    def aplicar_stemming(self, tokens: list[str]) -> list[str]:
        return [self.stemmer.stem(token) for token in tokens]

    def procesar(self, texto: str) -> dict:
        limpio = self.limpiar(texto)
        tokens = self.tokenizar(limpio)
        sin_stopwords = self.eliminar_stopwords(tokens)
        stems = self.aplicar_stemming(sin_stopwords)

        bi = Counter(bigrams(sin_stopwords)).most_common(10)
        tri = Counter(trigrams(sin_stopwords)).most_common(5)

        return {
            "original": texto,
            "limpio": limpio,
            "tokens": tokens,
            "sin_stopwords": sin_stopwords,
            "stems": stems,
            "num_oraciones": len(sent_tokenize(texto, language=self.idioma)),
            "vocabulario_unico": len(set(sin_stopwords)),
            "riqueza_lexica": len(set(sin_stopwords)) / max(len(sin_stopwords), 1),
            "top_bigramas": [list(b) for b, _ in bi],
            "top_trigramas": [list(t) for t, _ in tri],
        }

    def procesar_noticias(self, noticias: list[dict]) -> list[dict]:
        resultados = []

        for noticia in noticias:
            texto_completo = f"{noticia['titulo']}. {noticia['cuerpo']}"
            resultado = self.procesar(texto_completo)
            noticia["nlp"] = resultado
            resultados.append(resultado)

        return resultados

    def estadisticas_corpus(self, textos_procesados: list[dict]) -> dict:
        todos_tokens = []
        todos_stems = []

        for texto_procesado in textos_procesados:
            todos_tokens.extend(texto_procesado["sin_stopwords"])
            todos_stems.extend(texto_procesado["stems"])

        return {
            "total_documentos": len(textos_procesados),
            "total_tokens": len(todos_tokens),
            "vocabulario_total": len(set(todos_tokens)),
            "stems_unicos": len(set(todos_stems)),
            "palabras_frecuentes": Counter(todos_tokens).most_common(10),
            "promedio_tokens_doc": len(todos_tokens) / max(len(textos_procesados), 1),
        }

    @staticmethod
    def _asegurar_recursos_nltk() -> None:
        recursos = {
            "tokenizers/punkt": "punkt",
            "tokenizers/punkt_tab": "punkt_tab",
            "corpora/stopwords": "stopwords",
        }

        for ruta, paquete in recursos.items():
            try:
                nltk.data.find(ruta)
            except LookupError:
                nltk.download(paquete, quiet=True)
