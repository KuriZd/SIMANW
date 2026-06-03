from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SistemaRecomendacion:
    """Recomienda noticias relacionadas basandose en similitud de contenido."""

    def __init__(self, noticias: list[dict], matriz_similitud=None) -> None:
        self.noticias = noticias
        self.sim_matrix = matriz_similitud if matriz_similitud is not None else self._construir_matriz_similitud(noticias)
        if len(self.sim_matrix) != len(noticias):
            raise ValueError("La matriz de similitud debe coincidir con el numero de noticias")

    def recomendar(
        self,
        noticia_idx: int,
        top_n: int = 2,
        excluir_misma_cat: bool = False,
    ) -> list[tuple[int, float]]:
        self._validar_indice(noticia_idx)
        similitudes = self.sim_matrix[noticia_idx]
        candidatos = []

        for indice, similitud in enumerate(similitudes):
            if indice == noticia_idx:
                continue
            if (
                excluir_misma_cat
                and self._categoria(self.noticias[indice]) == self._categoria(self.noticias[noticia_idx])
            ):
                continue
            candidatos.append((indice, float(similitud)))

        candidatos.sort(key=lambda item: item[1], reverse=True)
        return candidatos[:top_n]

    def recomendar_por_perfil(self, indices_leidos: list[int], top_n: int = 3) -> list[tuple[int, float]]:
        if not indices_leidos:
            return []
        for indice in indices_leidos:
            self._validar_indice(indice)

        sim_acumulada = np.zeros(len(self.noticias))

        for indice in indices_leidos:
            sim_acumulada += self.sim_matrix[indice]

        for indice in indices_leidos:
            sim_acumulada[indice] = 0

        mejores = sim_acumulada.argsort()[::-1][:top_n]
        return [(int(indice), float(sim_acumulada[indice])) for indice in mejores if sim_acumulada[indice] > 0]

    def recomendar_detallado(self, noticia_idx: int, top_n: int = 2) -> list[dict]:
        return [self._detalle(indice, similitud) for indice, similitud in self.recomendar(noticia_idx, top_n)]

    def recomendar_por_perfil_detallado(self, indices_leidos: list[int], top_n: int = 3) -> list[dict]:
        return [self._detalle(indice, similitud) for indice, similitud in self.recomendar_por_perfil(indices_leidos, top_n)]

    def _validar_indice(self, indice: int) -> None:
        if indice < 0 or indice >= len(self.noticias):
            raise IndexError(f"Indice de noticia fuera de rango: {indice}")

    def _detalle(self, indice: int, similitud: float) -> dict:
        noticia = self.noticias[indice]
        return {
            "indice": indice,
            "titulo": noticia.get("titulo", ""),
            "categoria": self._categoria(noticia),
            "similitud": float(similitud),
        }

    @staticmethod
    def _categoria(noticia: dict) -> str:
        return (
            noticia.get("categoria_original")
            or noticia.get("categoria")
            or noticia.get("categoria_predicha")
            or "sin_categoria"
        )

    @staticmethod
    def _texto(noticia: dict) -> str:
        return " ".join(
            str(noticia.get(campo, "") or "")
            for campo in ("titulo", "cuerpo", "resumen", "texto_original")
        ).strip()

    @classmethod
    def _construir_matriz_similitud(cls, noticias: list[dict]):
        if not noticias:
            return np.zeros((0, 0))
        documentos = [cls._texto(noticia) or "sin contenido" for noticia in noticias]
        matriz = TfidfVectorizer(max_features=2000, ngram_range=(1, 2)).fit_transform(documentos)
        return cosine_similarity(matriz)
