from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC


class SelectorModelo:
    """
    AC-3: Entrena multiples modelos y selecciona automaticamente el mejor
    usando validacion cruzada estratificada.
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
        self._clases: list[str] = []

    def evaluar_todos(self, textos: list[str], etiquetas: list[str], cv_folds: int = 3) -> dict[str, dict]:
        """Evalua todos los modelos con validacion cruzada estratificada."""
        self._validar_datos(textos, etiquetas, cv_folds)

        conteo = Counter(etiquetas)
        self._clases = sorted(conteo)
        min_clase = min(conteo.values())

        if len(self._clases) < 2:
            raise ValueError("Se necesitan al menos dos clases para clasificar")

        cv_efectivos = min(cv_folds, min_clase)
        if cv_efectivos < 2:
            raise ValueError(
                f"La clase con menos muestras tiene {min_clase} ejemplo(s); "
                "se necesitan al menos 2 por clase para validacion cruzada"
            )

        if cv_efectivos < cv_folds:
            print(
                f"[AC-3] cv_folds ajustado de {cv_folds} a {cv_efectivos} "
                f"(clase mas pequena: {min_clase} muestra(s))"
            )

        x_vec = self.vectorizer.fit_transform(textos)
        cv = StratifiedKFold(n_splits=cv_efectivos, shuffle=True, random_state=42)
        self.resultados = {}
        self.mejor_modelo = None

        for nombre, modelo in self.modelos.items():
            try:
                scores = cross_val_score(modelo, x_vec, etiquetas, cv=cv, scoring="accuracy")
                self.resultados[nombre] = {
                    "accuracy_mean": float(np.mean(scores)),
                    "accuracy_std": float(np.std(scores)),
                    "scores": scores.tolist(),
                }
            except Exception as exc:
                self.resultados[nombre] = {"error": str(exc)}

        validos = {n: r for n, r in self.resultados.items() if "accuracy_mean" in r}
        if validos:
            mejor_nombre = max(
                validos,
                key=lambda n: (validos[n]["accuracy_mean"], -validos[n]["accuracy_std"]),
            )
            self.modelos[mejor_nombre].fit(x_vec, etiquetas)
            self.mejor_modelo = (mejor_nombre, self.modelos[mejor_nombre])

        return self.resultados

    def predecir(self, textos: list[str]) -> list[str]:
        """Predice usando el mejor modelo seleccionado."""
        if not self.mejor_modelo:
            raise ValueError("Primero ejecuta evaluar_todos()")
        x_vec = self.vectorizer.transform(textos)
        return list(self.mejor_modelo[1].predict(x_vec))

    def reporte(self) -> str:
        """Genera reporte comparativo de modelos en texto."""
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
                lineas.append(
                    f"{nombre:<23} | ERROR      | {resultado.get('error', '')[:20]}"
                )
        return "\n".join(lineas)

    def guardar_resultados(
        self,
        ruta: str | Path,
        textos: list[str] | None = None,
        predicciones_prueba: list[dict] | None = None,
    ) -> None:
        """Exporta los resultados de evaluacion a JSON."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "actividad": "AC-3",
            "descripcion": "Clasificador multimodelo con seleccion automatica",
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "total_textos": len(textos) if textos is not None else 0,
            "total_clases": len(self._clases),
            "clases": self._clases,
            "mejor_modelo": self.mejor_modelo[0] if self.mejor_modelo else "",
            "resultados": self.resultados,
            "predicciones_prueba": predicciones_prueba or [],
        }

        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(payload, archivo, ensure_ascii=False, indent=2)

    def guardar_modelo(self, ruta_modelo: str | Path, ruta_vectorizer: str | Path) -> None:
        """Guarda el mejor modelo y el vectorizador con joblib."""
        import joblib

        if not self.mejor_modelo:
            raise ValueError("No hay modelo entrenado. Ejecuta evaluar_todos() primero.")

        ruta_modelo = Path(ruta_modelo)
        ruta_vectorizer = Path(ruta_vectorizer)
        ruta_modelo.parent.mkdir(parents=True, exist_ok=True)
        ruta_vectorizer.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.mejor_modelo[1], ruta_modelo)
        joblib.dump(self.vectorizer, ruta_vectorizer)

    def cargar_modelo(self, ruta_modelo: str | Path, ruta_vectorizer: str | Path) -> None:
        """Carga un modelo y vectorizador previamente guardados."""
        import joblib

        modelo = joblib.load(Path(ruta_modelo))
        self.vectorizer = joblib.load(Path(ruta_vectorizer))
        nombre = Path(ruta_modelo).stem
        self.mejor_modelo = (nombre, modelo)
        if nombre not in self.resultados:
            self.resultados[nombre] = {"cargado_desde_disco": True}

    @staticmethod
    def _validar_datos(textos: list[str], etiquetas: list[str], cv_folds: int) -> None:
        if not textos:
            raise ValueError("Se necesita al menos un texto para entrenar")
        if len(textos) != len(etiquetas):
            raise ValueError("textos y etiquetas deben tener la misma longitud")
        if cv_folds < 2:
            raise ValueError("cv_folds debe ser al menos 2")


def cargar_dataset_desde_json(ruta: str | Path) -> tuple[list[str], list[str]]:
    """
    Carga textos y etiquetas desde un archivo JSON de noticias SIMANW.
    Combina titulo + resumen + cuerpo como texto y usa categoria como etiqueta.
    """
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if not isinstance(datos, list):
        raise ValueError("El archivo JSON debe contener una lista de noticias")

    textos: list[str] = []
    etiquetas: list[str] = []

    for noticia in datos:
        partes = [
            noticia.get("titulo", ""),
            noticia.get("resumen", ""),
            noticia.get("cuerpo", ""),
        ]
        texto = " ".join(p for p in partes if p).strip()
        etiqueta = (
            noticia.get("categoria_predicha")
            or noticia.get("categoria_original")
            or noticia.get("categoria")
            or noticia.get("fuente", "")
        )
        if texto and etiqueta:
            textos.append(texto)
            etiquetas.append(str(etiqueta))

    return textos, etiquetas


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
