import numpy as np

from src.recomendacion import SistemaRecomendacion


def test_recomendador_ordena_por_similitud():
    noticias = [
        {"categoria_original": "tecnologia", "titulo": "N1"},
        {"categoria_original": "ciencia", "titulo": "N2"},
        {"categoria_original": "economia", "titulo": "N3"},
    ]
    matriz = np.array(
        [
            [1.0, 0.7, 0.2],
            [0.7, 1.0, 0.1],
            [0.2, 0.1, 1.0],
        ]
    )
    recomendador = SistemaRecomendacion(noticias, matriz)

    recomendaciones = recomendador.recomendar(0, top_n=2)

    assert recomendaciones == [(1, 0.7), (2, 0.2)]


def test_recomendador_excluye_misma_categoria_si_se_indica():
    noticias = [
        {"categoria_original": "tecnologia", "titulo": "N1"},
        {"categoria_original": "tecnologia", "titulo": "N2"},
        {"categoria_original": "economia", "titulo": "N3"},
    ]
    matriz = np.array(
        [
            [1.0, 0.9, 0.4],
            [0.9, 1.0, 0.1],
            [0.4, 0.1, 1.0],
        ]
    )
    recomendador = SistemaRecomendacion(noticias, matriz)

    recomendaciones = recomendador.recomendar(0, top_n=2, excluir_misma_cat=True)

    assert recomendaciones == [(2, 0.4)]


def test_recomendador_por_perfil_suma_similitudes():
    noticias = [
        {"categoria_original": "tecnologia", "titulo": "N1"},
        {"categoria_original": "tecnologia", "titulo": "N2"},
        {"categoria_original": "ciencia", "titulo": "N3"},
    ]
    matriz = np.array(
        [
            [1.0, 0.3, 0.8],
            [0.3, 1.0, 0.2],
            [0.8, 0.2, 1.0],
        ]
    )
    recomendador = SistemaRecomendacion(noticias, matriz)

    recomendaciones = recomendador.recomendar_por_perfil([0, 1], top_n=1)

    assert recomendaciones == [(2, 1.0)]
