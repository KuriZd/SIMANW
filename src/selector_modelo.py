from __future__ import annotations

from collections import Counter

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC


class SelectorModelo:
    """
    AC-3: Entrena multiples modelos y selecciona automaticamente el mejor.
    """

    def __init__(self) -> None:
        self.modelos = {
            "Naive Bayes": MultinomialNB(alpha=0.1),
            "SVM Lineal": LinearSVC(max_iter=3000, C=1.0),
            "Logistic Regression": LogisticRegression(max_iter=1000, C=1.0),
            "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        }
        self.vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
        self.mejor_modelo: tuple[str, object] | None = None
        self.resultados: dict[str, dict] = {}

    def evaluar_todos(self, textos: list[str], etiquetas: list[str], cv_folds: int = 3) -> dict[str, dict]:
        """Evalua todos los modelos con validacion cruzada."""
        self._validar_datos(textos, etiquetas, cv_folds)

        x_vectorizado = self.vectorizer.fit_transform(textos)
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        self.resultados = {}
        self.mejor_modelo = None

        for nombre, modelo in self.modelos.items():
            try:
                scores = cross_val_score(modelo, x_vectorizado, etiquetas, cv=cv, scoring="accuracy")
                self.resultados[nombre] = {
                    "accuracy_mean": float(np.mean(scores)),
                    "accuracy_std": float(np.std(scores)),
                    "scores": scores.tolist(),
                }
            except Exception as exc:
                self.resultados[nombre] = {"error": str(exc)}

        validos = {nombre: res for nombre, res in self.resultados.items() if "accuracy_mean" in res}
        if validos:
            mejor_nombre = max(validos, key=lambda nombre: validos[nombre]["accuracy_mean"])
            mejor_modelo = self.modelos[mejor_nombre]
            mejor_modelo.fit(x_vectorizado, etiquetas)
            self.mejor_modelo = (mejor_nombre, mejor_modelo)

        return self.resultados

    def predecir(self, textos: list[str]) -> list[str]:
        """Predice usando el mejor modelo seleccionado."""
        if not self.mejor_modelo:
            raise ValueError("Primero ejecuta evaluar_todos()")

        x_vectorizado = self.vectorizer.transform(textos)
        return list(self.mejor_modelo[1].predict(x_vectorizado))

    def reporte(self) -> str:
        """Genera reporte comparativo de modelos."""
        lineas = ["Modelo                  | Accuracy   | Std Dev"]
        lineas.append("-" * 50)

        ordenados = sorted(
            self.resultados.items(),
            key=lambda item: item[1].get("accuracy_mean", -1),
            reverse=True,
        )
        for nombre, resultado in ordenados:
            if "accuracy_mean" in resultado:
                marca = " *" if self.mejor_modelo and nombre == self.mejor_modelo[0] else ""
                lineas.append(
                    f"{nombre:<23} | {resultado['accuracy_mean']:.4f}     | "
                    f"{resultado['accuracy_std']:.4f}{marca}"
                )
            else:
                lineas.append(f"{nombre:<23} | ERROR      | {resultado.get('error', '')[:20]}")

        return "\n".join(lineas)

    @staticmethod
    def _validar_datos(textos: list[str], etiquetas: list[str], cv_folds: int) -> None:
        if len(textos) != len(etiquetas):
            raise ValueError("textos y etiquetas deben tener la misma longitud")
        if not textos:
            raise ValueError("Se necesita al menos un texto para entrenar")
        if cv_folds < 2:
            raise ValueError("cv_folds debe ser al menos 2")

        conteo = Counter(etiquetas)
        min_clase = min(conteo.values())
        if min_clase < cv_folds:
            raise ValueError("Cada clase debe tener al menos cv_folds ejemplos")


TEXTOS_AC3 = [
    "inteligencia artificial deep learning redes neuronales transformers",
    "programacion software desarrollo aplicaciones web python javascript",
    "startup tecnologica innovacion digital plataforma cloud",
    "ciberseguridad hackers vulnerabilidad proteccion datos privacidad",
    "inflacion tasas interes banco central politica monetaria",
    "bolsa acciones mercado valores inversion rendimiento portafolio",
    "desempleo recesion economica crisis laboral empleo informal",
    "comercio exportaciones importaciones balanza aranceles tratado",
    "investigacion cientifica laboratorio experimento publicacion revista",
    "cambio climatico emisiones carbono calentamiento temperatura global",
    "vacuna medicamento ensayo clinico pacientes tratamiento hospital",
    "espacio cohete satelite mision astronauta exploracion lunar",
    "elecciones presidente candidato partido campana votacion democracia",
    "congreso legisladores reforma ley aprobacion dictamen senado",
    "seguridad policia crimen organizado justicia tribunal sentencia",
    "gobierno programa social presupuesto politica publica decreto",
]

ETIQUETAS_AC3 = [
    "tecnologia",
    "tecnologia",
    "tecnologia",
    "tecnologia",
    "economia",
    "economia",
    "economia",
    "economia",
    "ciencia",
    "ciencia",
    "ciencia",
    "ciencia",
    "politica",
    "politica",
    "politica",
    "politica",
]
