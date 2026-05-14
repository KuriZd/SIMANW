from __future__ import annotations

from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import cross_val_score
from sklearn.svm import LinearSVC


TEXTOS_ENTRENAMIENTO = [
    "inteligencia artificial machine learning algoritmos redes neuronales deep learning",
    "nuevo procesador computadora software desarrollo programacion tecnologia",
    "startup tecnologica lanza aplicacion innovadora plataforma digital",
    "robot automatizacion industria software empresa tecnologia",
    "python programacion desarrolladores rendimiento optimizacion lenguaje software tecnologia",
    "mercados financieros bolsa acciones inversion capital rendimiento",
    "inflacion economia banco central tasas interes politica monetaria",
    "desempleo crisis economica recesion pib crecimiento producto interno",
    "comercio internacional exportaciones importaciones aranceles tratado",
    "volatilidad mercados inversionistas indices bursatiles finanzas globales",
    "estudio cientifico investigadores descubrimiento laboratorio publicacion",
    "cambio climatico calentamiento global temperatura emisiones carbono",
    "vacuna tratamiento medico salud enfermedad hospital pacientes",
    "espacio nasa cohete satelite mision exploracion astronauta",
    "datos cientificos estudio expertos predicciones cambio climatico investigacion",
    "elecciones candidato presidente congreso voto democracia partido",
    "gobierno ley reforma politica publica decreto legislacion",
    "seguridad publica policia crimen delito justicia tribunal",
    "presupuesto gasto publico programa social gobierno federal",
    "portal datos abiertos gobierno transparencia publica estadisticas presupuesto",
]

ETIQUETAS_ENTRENAMIENTO = [
    "tecnologia",
    "tecnologia",
    "tecnologia",
    "tecnologia",
    "tecnologia",
    "economia",
    "economia",
    "economia",
    "economia",
    "economia",
    "ciencia",
    "ciencia",
    "ciencia",
    "ciencia",
    "ciencia",
    "politica",
    "politica",
    "politica",
    "politica",
    "politica",
]


class ClasificadorNoticias:
    """Clasifica noticias automaticamente por categoria."""

    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
        self.clasificador = LinearSVC(max_iter=2000)
        self.categorias: list[str] = []
        self.entrenado = False

    def entrenar(self, textos: list[str], etiquetas: list[str]) -> dict:
        if len(textos) != len(etiquetas):
            raise ValueError("Textos y etiquetas deben tener la misma longitud")
        if len(set(etiquetas)) < 2:
            raise ValueError("Se necesitan al menos dos categorias para entrenar")

        matriz = self.vectorizer.fit_transform(textos)
        self.clasificador.fit(matriz, etiquetas)
        self.categorias = sorted(set(etiquetas))
        self.entrenado = True

        conteo_clases = Counter(etiquetas)
        cv = min(3, len(textos) // 2, min(conteo_clases.values()))
        scores = cross_val_score(self.clasificador, matriz, etiquetas, cv=cv) if cv >= 2 else np.array([1.0])

        return {
            "accuracy_cv": float(scores.mean()),
            "categorias": self.categorias,
            "n_muestras": len(textos),
        }

    def predecir(self, textos: list[str]) -> np.ndarray:
        self._validar_entrenado()
        matriz = self.vectorizer.transform(textos)
        return self.clasificador.predict(matriz)

    def predecir_con_confianza(self, texto: str) -> tuple[str, dict[str, float]]:
        self._validar_entrenado()
        matriz = self.vectorizer.transform([texto])
        decision = self.clasificador.decision_function(matriz)
        prediccion = self.clasificador.predict(matriz)[0]

        if decision.ndim == 1:
            puntajes = decision
        else:
            puntajes = decision[0]

        return str(prediccion), {
            str(categoria): float(score)
            for categoria, score in zip(self.clasificador.classes_, puntajes)
        }

    def clasificar_noticias(self, noticias: list[dict]) -> list[tuple[str, dict[str, float]]]:
        resultados = []

        for noticia in noticias:
            texto = f"{noticia['titulo']} {noticia['cuerpo']}"
            prediccion, scores = self.predecir_con_confianza(texto)
            noticia["categoria_predicha"] = prediccion
            noticia["scores_categoria"] = scores
            resultados.append((prediccion, scores))

        return resultados

    def _validar_entrenado(self) -> None:
        if not self.entrenado:
            raise ValueError("El clasificador debe entrenarse antes de predecir")
