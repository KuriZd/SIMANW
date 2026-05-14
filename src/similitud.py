from __future__ import annotations

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class CalculadorSimilitud:
    """Calcula similitudes entre documentos del SIMANW."""

    def __init__(self, matriz_tfidf) -> None:
        self.matriz = matriz_tfidf
        self.sim_matrix = cosine_similarity(matriz_tfidf)

    def similitud_par(self, doc_i: int, doc_j: int) -> float:
        return float(self.sim_matrix[doc_i][doc_j])

    def documentos_similares(self, doc_idx: int, top_n: int = 3) -> list[tuple[int, float]]:
        similitudes = self.sim_matrix[doc_idx]
        indices = np.argsort(similitudes)[::-1]
        indices = [indice for indice in indices if indice != doc_idx][:top_n]
        return [(int(indice), float(similitudes[indice])) for indice in indices]

    def agrupar_por_similitud(self, umbral: float = 0.15) -> list[list[int]]:
        grupos = []
        visitados = set()

        for indice in range(len(self.sim_matrix)):
            if indice in visitados:
                continue

            grupo = [indice]
            visitados.add(indice)

            for candidato in range(indice + 1, len(self.sim_matrix)):
                if candidato not in visitados and self.sim_matrix[indice][candidato] >= umbral:
                    grupo.append(candidato)
                    visitados.add(candidato)

            grupos.append(grupo)

        return grupos
