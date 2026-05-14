from __future__ import annotations

import numpy as np


class SistemaRecomendacion:
    """Recomienda noticias relacionadas basandose en similitud de contenido."""

    def __init__(self, noticias: list[dict], matriz_similitud) -> None:
        self.noticias = noticias
        self.sim_matrix = matriz_similitud

    def recomendar(
        self,
        noticia_idx: int,
        top_n: int = 2,
        excluir_misma_cat: bool = False,
    ) -> list[tuple[int, float]]:
        similitudes = self.sim_matrix[noticia_idx]
        candidatos = []

        for indice, similitud in enumerate(similitudes):
            if indice == noticia_idx:
                continue
            if (
                excluir_misma_cat
                and self.noticias[indice]["categoria_original"] == self.noticias[noticia_idx]["categoria_original"]
            ):
                continue
            candidatos.append((indice, float(similitud)))

        candidatos.sort(key=lambda item: item[1], reverse=True)
        return candidatos[:top_n]

    def recomendar_por_perfil(self, indices_leidos: list[int], top_n: int = 3) -> list[tuple[int, float]]:
        if not indices_leidos:
            return []

        sim_acumulada = np.zeros(len(self.noticias))

        for indice in indices_leidos:
            sim_acumulada += self.sim_matrix[indice]

        for indice in indices_leidos:
            sim_acumulada[indice] = 0

        mejores = sim_acumulada.argsort()[::-1][:top_n]
        return [(int(indice), float(sim_acumulada[indice])) for indice in mejores if sim_acumulada[indice] > 0]
