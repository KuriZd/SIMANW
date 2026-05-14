from __future__ import annotations

from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer


class RepresentacionVectorial:
    """Convierte documentos del SIMANW en vectores TF-IDF."""

    def __init__(self, max_features: int = 2000, ngram_range: tuple[int, int] = (1, 2)) -> None:
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            sublinear_tf=True,
        )
        self.matriz: csr_matrix | None = None
        self.documentos_texto: list[str] = []

    def construir_matriz(self, documentos: list[str]) -> csr_matrix:
        if not documentos:
            raise ValueError("Se necesita al menos un documento para construir la matriz TF-IDF")

        self.documentos_texto = documentos
        self.matriz = self.vectorizer.fit_transform(documentos)
        return self.matriz

    def vocabulario(self):
        return self.vectorizer.get_feature_names_out()

    def top_terminos_documento(self, doc_idx: int, n: int = 8) -> list[tuple[str, float]]:
        self._validar_matriz()
        vector = self.matriz[doc_idx].toarray().flatten()
        terminos = self.vocabulario()
        indices_top = vector.argsort()[::-1][:n]
        return [(terminos[indice], float(vector[indice])) for indice in indices_top if vector[indice] > 0]

    def info_matriz(self) -> dict:
        self._validar_matriz()
        filas, columnas = self.matriz.shape

        return {
            "documentos": filas,
            "features": columnas,
            "densidad": self.matriz.nnz / (filas * columnas),
            "terminos_promedio_doc": self.matriz.nnz / filas,
        }

    def _validar_matriz(self) -> None:
        if self.matriz is None:
            raise ValueError("La matriz TF-IDF aun no ha sido construida")
