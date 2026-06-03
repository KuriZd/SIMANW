from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class MotorBusqueda:
    """Motor de busqueda del SIMANW con indice invertido y ranking TF-IDF."""

    def __init__(self) -> None:
        self.documentos: dict[int, dict] = {}
        self.indice_invertido = defaultdict(dict)
        self.doc_lengths: dict[int, int] = {}
        self.N = 0
        self.vectorizer = TfidfVectorizer(
            max_features=3000,
            ngram_range=(1, 2),
            strip_accents="unicode",
            lowercase=True,
        )
        self.matriz_busqueda = None

    def indexar(self, documentos: list[dict]) -> None:
        if not documentos:
            raise ValueError("Se necesita al menos un documento para construir el indice")

        self.documentos = {}
        self.indice_invertido = defaultdict(dict)
        self.doc_lengths = {}
        self.N = len(documentos)
        textos = []

        for doc_id, documento in enumerate(documentos):
            self.documentos[doc_id] = documento
            texto = self._texto_documento(documento)
            textos.append(texto)
            tokens = self._tokenizar(texto)
            tf = Counter(tokens)
            self.doc_lengths[doc_id] = len(tokens)

            for termino, frecuencia in tf.items():
                self.indice_invertido[termino][doc_id] = frecuencia

        self.matriz_busqueda = self.vectorizer.fit_transform(textos)

    def buscar_booleana(self, consulta: str, modo: str = "AND") -> list[int]:
        terminos = self._tokenizar(consulta)
        if not terminos:
            return []

        if modo.upper() == "AND":
            resultado = set(self.indice_invertido.get(terminos[0], {}).keys())
            for termino in terminos[1:]:
                resultado &= set(self.indice_invertido.get(termino, {}).keys())
        elif modo.upper() == "OR":
            resultado = set()
            for termino in terminos:
                resultado |= set(self.indice_invertido.get(termino, {}).keys())
        else:
            raise ValueError("Modo de busqueda booleana no soportado. Usa AND u OR")

        return sorted(resultado)

    def buscar_vectorial(self, consulta: str, top_k: int = 5) -> list[dict]:
        self._validar_indexado()
        consulta_vec = self.vectorizer.transform([consulta])
        similitudes = cosine_similarity(consulta_vec, self.matriz_busqueda)[0]
        candidatos = []
        for indice, relevancia in enumerate(similitudes):
            score = self._score_ajustado(consulta, self.documentos[int(indice)], float(relevancia))
            if score > 0:
                candidatos.append((int(indice), float(relevancia), score))
        candidatos.sort(key=lambda item: item[2], reverse=True)
        resultados = []

        for indice, relevancia, score in candidatos[:top_k]:
            documento = self.documentos[int(indice)]
            resultados.append(
                {
                    "doc_id": int(indice),
                    "titulo": documento["titulo"],
                    "relevancia": relevancia,
                    "score": score,
                    "categoria": documento.get("categoria_predicha", documento.get("categoria_original", "?")),
                    "sentimiento": documento.get("sentimiento", {}).get("etiqueta", "?"),
                    "snippet": self._snippet(documento["cuerpo"]),
                    "fecha": documento.get("fecha", ""),
                    "url": documento.get("url", ""),
                }
            )

        return resultados

    @classmethod
    def _score_ajustado(cls, consulta: str, documento: dict, relevancia: float) -> float:
        titulo = str(documento.get("titulo", ""))
        cuerpo = str(documento.get("cuerpo", ""))
        consulta_norm = cls._normalizar(consulta)
        titulo_norm = cls._normalizar(titulo)
        cuerpo_norm = cls._normalizar(cuerpo)

        score = relevancia
        if consulta_norm and consulta_norm in titulo_norm:
            score += 1.0

        tokens_consulta = cls._tokens_significativos(consulta_norm)
        if tokens_consulta:
            tokens_titulo = set(cls._tokens_significativos(titulo_norm))
            tokens_texto = set(cls._tokens_significativos(f"{titulo_norm} {cuerpo_norm}"))
            overlap_titulo = len(tokens_consulta & tokens_titulo) / len(tokens_consulta)
            overlap_texto = len(tokens_consulta & tokens_texto) / len(tokens_consulta)
            score += overlap_titulo * 0.7
            score += overlap_texto * 0.2

        return score

    def info_indice(self) -> dict:
        return {
            "documentos_indexados": self.N,
            "terminos_en_indice": len(self.indice_invertido),
            "tamano_promedio_posting": sum(len(v) for v in self.indice_invertido.values())
            / max(len(self.indice_invertido), 1),
        }

    @staticmethod
    def _texto_documento(documento: dict) -> str:
        return f"{documento['titulo']} {documento['cuerpo']}"

    @classmethod
    def _tokenizar(cls, texto: str) -> list[str]:
        normalizado = cls._normalizar(texto)
        return re.findall(r"\b\w+\b", normalizado)

    @staticmethod
    def _normalizar(texto: str) -> str:
        texto = texto.lower()
        texto = unicodedata.normalize("NFKD", texto)
        return "".join(caracter for caracter in texto if not unicodedata.combining(caracter))

    @classmethod
    def _tokens_significativos(cls, texto: str) -> set[str]:
        stopwords = {
            "a", "al", "asi", "con", "de", "del", "el", "en", "es", "fue",
            "la", "las", "lo", "los", "mas", "para", "por", "que", "se",
            "su", "sus", "un", "una", "y",
        }
        return {token for token in cls._tokenizar(texto) if len(token) >= 3 and token not in stopwords}

    @staticmethod
    def _snippet(texto: str, longitud: int = 500) -> str:
        return texto[:longitud] + ("..." if len(texto) > longitud else "")

    def _validar_indexado(self) -> None:
        if self.matriz_busqueda is None:
            raise ValueError("El motor debe indexar documentos antes de buscar")
