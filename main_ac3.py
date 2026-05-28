"""AC-3: Clasificador multimodelo con seleccion automatica.

Uso:
    python main_ac3.py                       # datos de ejemplo integrados
    python main_ac3.py data/noticias_ac1.json  # dataset desde JSON de Fase 1
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.selector_modelo import (
    ETIQUETAS_AC3,
    TEXTOS_AC3,
    SelectorModelo,
    cargar_dataset_desde_json,
)

SALIDA_JSON = Path("data") / "resultados_ac3.json"
SALIDA_MODELO = Path("models") / "mejor_modelo_ac3.joblib"
SALIDA_VECTORIZER = Path("models") / "vectorizer_ac3.joblib"

TEXTOS_PRUEBA = [
    "nueva aplicacion de machine learning para detectar fraudes bancarios",
    "el presidente anuncio reformas al sistema de justicia y seguridad",
    "inflacion y tasas de interes presionan al mercado de valores",
    "descubrimiento de nueva especie en la selva amazonica",
]


def cargar_datos() -> tuple[list[str], list[str], str]:
    """Devuelve (textos, etiquetas, origen)."""
    if len(sys.argv) > 1:
        ruta = Path(sys.argv[1])
        if not ruta.exists():
            print(f"Archivo no encontrado: {ruta}. Usando datos de ejemplo.")
            return TEXTOS_AC3, ETIQUETAS_AC3, "datos de ejemplo integrados"
        try:
            textos, etiquetas = cargar_dataset_desde_json(ruta)
            if len(set(etiquetas)) < 2:
                print("El JSON no tiene suficientes clases. Usando datos de ejemplo.")
                return TEXTOS_AC3, ETIQUETAS_AC3, "datos de ejemplo integrados"
            return textos, etiquetas, str(ruta)
        except Exception as exc:
            print(f"Error al cargar JSON: {exc}. Usando datos de ejemplo.")

    return TEXTOS_AC3, ETIQUETAS_AC3, "datos de ejemplo integrados"


def main() -> None:
    print("=== AC-3: Clasificador Multimodelo con Seleccion Automatica ===\n")

    textos, etiquetas, origen = cargar_datos()
    from collections import Counter
    dist = Counter(etiquetas)
    print(f"Origen       : {origen}")
    print(f"Total textos : {len(textos)}")
    print(f"Clases       : {dict(dist)}\n")

    selector = SelectorModelo()

    print("Evaluando modelos con validacion cruzada...\n")
    try:
        selector.evaluar_todos(textos, etiquetas, cv_folds=3)
    except ValueError as exc:
        print(f"Error de validacion: {exc}")
        sys.exit(1)

    print(selector.reporte())

    mejor = selector.mejor_modelo[0] if selector.mejor_modelo else "N/A"
    mejor_res = selector.resultados.get(mejor, {})
    print(f"\nModelo seleccionado : {mejor}")
    if "accuracy_mean" in mejor_res:
        print(f"Accuracy CV         : {mejor_res['accuracy_mean']:.4f} ± {mejor_res['accuracy_std']:.4f}")

    print("\nPredicciones sobre textos nuevos:")
    predicciones = selector.predecir(TEXTOS_PRUEBA)
    predicciones_log: list[dict] = []
    for texto, pred in zip(TEXTOS_PRUEBA, predicciones):
        print(f"  [{pred:<12}] {texto[:65]}")
        predicciones_log.append({"texto": texto, "categoria_predicha": pred})
    print()

    selector.guardar_resultados(SALIDA_JSON, textos, predicciones_log)
    print(f"Resultados guardados : {SALIDA_JSON}")

    try:
        selector.guardar_modelo(SALIDA_MODELO, SALIDA_VECTORIZER)
        print(f"Modelo guardado      : {SALIDA_MODELO}")
        print(f"Vectorizador guardado: {SALIDA_VECTORIZER}")
    except ImportError:
        print("joblib no disponible. Instala con: pip install joblib")

    print("\nListo. Los archivos son compatibles con el pipeline SIMANW.")


if __name__ == "__main__":
    main()
