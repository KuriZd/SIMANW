"""AC-5: Evaluacion comparativa de modelos de busqueda booleano vs vectorial.

Uso:
    python main_ac5.py                        # corpus demo integrado
    python main_ac5.py data/noticias_ac1.json # corpus desde JSON de AC-1
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.comparador_busqueda import (
    CONSULTAS_EVAL_AC5,
    ComparadorModelos,
    cargar_documentos_desde_json,
)

SALIDA_JSON = Path("data") / "resultados_ac5.json"

DOCUMENTOS_DEMO = [
    {
        "titulo": "Inteligencia artificial generativa",
        "cuerpo": "La inteligencia artificial transforma software y programacion con modelos de lenguaje.",
    },
    {
        "titulo": "Mercados financieros y volatilidad",
        "cuerpo": "La economia enfrenta volatilidad en mercados de valores ante alzas de tasas.",
    },
    {
        "titulo": "Cambio climatico y ciencia",
        "cuerpo": "Investigadores cientificos estudian calentamiento global, carbono y emisiones.",
    },
    {
        "titulo": "Python para inteligencia artificial",
        "cuerpo": "Python ayuda a crear aplicaciones de machine learning e inteligencia artificial.",
    },
    {
        "titulo": "Datos abiertos gobierno transparencia",
        "cuerpo": "El gobierno publica datos abiertos para promover transparencia y rendicion de cuentas.",
    },
    {
        "titulo": "Redes neuronales profundas",
        "cuerpo": "Deep learning y redes neuronales convolucionales mejoran reconocimiento de imagenes.",
    },
    {
        "titulo": "Criptomonedas y blockchain economia",
        "cuerpo": "Bitcoin y ethereum representan activos digitales en economia descentralizada.",
    },
    {
        "titulo": "Vacunas investigacion cientifica",
        "cuerpo": "Ensayos clinicos y vacunas de ARN mensajero revolucionan medicina moderna.",
    },
    {
        "titulo": "Seguridad cibernetica y privacidad",
        "cuerpo": "Ataques de ransomware amenazan infraestructura critica y datos personales.",
    },
    {
        "titulo": "Energia renovable solar eolica",
        "cuerpo": "Paneles solares y turbinas eolicas reducen dependencia de combustibles fosiles.",
    },
]

CONSULTAS_DEMO = [
    {"consulta": "inteligencia artificial", "relevantes": [0, 3, 5]},
    {"consulta": "mercados volatilidad economia", "relevantes": [1, 6]},
    {"consulta": "datos abiertos gobierno", "relevantes": [4]},
    {"consulta": "cambio climatico cientifico", "relevantes": [2, 7]},
    {"consulta": "redes neuronales deep learning", "relevantes": [0, 3, 5]},
    {"consulta": "seguridad privacidad cibernetica", "relevantes": [8]},
]


def cargar_corpus(arg: str | None) -> tuple[list[dict], str]:
    if arg is None:
        return DOCUMENTOS_DEMO, "corpus demo integrado"
    ruta = Path(arg)
    if not ruta.exists():
        print(f"Archivo no encontrado: {ruta}. Usando corpus demo.")
        return DOCUMENTOS_DEMO, "corpus demo integrado"
    try:
        docs = cargar_documentos_desde_json(ruta)
        return docs, str(ruta)
    except Exception as exc:
        print(f"Error al cargar JSON: {exc}. Usando corpus demo.")
        return DOCUMENTOS_DEMO, "corpus demo integrado"


def imprimir_detalle(resultados: list[dict]) -> None:
    print("\n--- Detalle por consulta ---")
    for resultado in resultados:
        bool_m = resultado["booleano"]
        vec_m = resultado["vectorial"]
        print(f"  Consulta: {resultado['consulta']}")
        print(
            f"    Booleano  -> recuperados: {bool_m['recuperados']:>2}  "
            f"P={bool_m['precision']:.3f}  R={bool_m['recall']:.3f}  F1={bool_m['f1']:.3f}"
        )
        print(
            f"    Vectorial -> recuperados: {vec_m['recuperados']:>2}  "
            f"P={vec_m['precision']:.3f}  R={vec_m['recall']:.3f}  F1={vec_m['f1']:.3f}"
        )


def imprimir_promedios(evaluacion: dict) -> None:
    pb = evaluacion["promedio_booleano"]
    pv = evaluacion["promedio_vectorial"]
    print("\n--- Promedios globales ---")
    print(f"  {'Modelo':<12} | {'Precisión':>9} | {'Recall':>6} | {'F1':>6}")
    print(f"  {'-'*40}")
    print(f"  {'Booleano':<12} | {pb['precision']:>9.4f} | {pb['recall']:>6.4f} | {pb['f1']:>6.4f}")
    print(f"  {'Vectorial':<12} | {pv['precision']:>9.4f} | {pv['recall']:>6.4f} | {pv['f1']:>6.4f}")
    print(f"\n  Ganador por precisión : {evaluacion['ganador_precision']}")
    print(f"  Ganador por F1        : {evaluacion['ganador_f1']}")


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    documentos, origen = cargar_corpus(arg)

    consultas = CONSULTAS_DEMO if arg is None else CONSULTAS_EVAL_AC5

    print("=== AC-5: Evaluación Comparativa de Modelos de Búsqueda ===\n")
    print(f"Corpus   : {origen}")
    print(f"Docs     : {len(documentos)}")
    print(f"Consultas: {len(consultas)}\n")

    comparador = ComparadorModelos(documentos)

    print("--- Búsqueda booleana (ejemplo: 'inteligencia artificial') ---")
    bool_res = comparador.busqueda_booleana("inteligencia artificial")
    print(f"  Documentos recuperados (IDs): {bool_res}")
    for idx in bool_res:
        print(f"    [{idx}] {documentos[idx]['titulo']}")

    print("\n--- Búsqueda vectorial top-5 (ejemplo: 'inteligencia artificial') ---")
    vec_res = comparador.busqueda_vectorial("inteligencia artificial", top_k=5)
    for idx, score in vec_res:
        print(f"  [{idx}] score={score:.4f}  {documentos[idx]['titulo']}")

    evaluacion = comparador.evaluar_consultas(consultas)
    imprimir_detalle(evaluacion["resultados"])
    imprimir_promedios(evaluacion)

    print("\n--- Reporte comparativo ---")
    print(comparador.reporte(consultas))

    comparador.guardar_json(SALIDA_JSON, consultas)
    print(f"\nResultados guardados : {SALIDA_JSON}")
    print("Listo. El JSON es compatible con el pipeline SIMANW.")


if __name__ == "__main__":
    main()
