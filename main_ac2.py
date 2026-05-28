"""AC-2: Analisis estadistico profundo de discursos y textos largos.

Uso:
    python main_ac2.py
"""
from __future__ import annotations

from pathlib import Path

from src.analisis_discurso import AnalisisDiscurso, generar_nube_palabras
from src.nltk_setup import descargar_recursos

SALIDA_JSON = Path("data") / "analisis_ac2.json"
SALIDA_NUBE = Path("data") / "nube_palabras_ac2.png"

TEXTO_DISCURSO = """La educacion es la herramienta mas poderosa para transformar una sociedad.
En Mexico, la inversion en educacion debe ser prioritaria para garantizar el desarrollo
economico y social. Los jovenes mexicanos merecen oportunidades de calidad en todos los
niveles educativos. Las universidades tecnologicas y los institutos de investigacion son
pilares fundamentales para la innovacion. La ciencia y la tecnologia son motores del
progreso nacional. El Instituto Tecnologico de Morelia ha formado generaciones de
ingenieros que contribuyen al desarrollo del pais. La inteligencia artificial y la
programacion son competencias esenciales para el futuro laboral. Mexico necesita mas
profesionales en ciencias computacionales y recuperacion de informacion. La educacion
superior debe adaptarse a los retos del siglo veintiuno. La innovacion tecnologica
requiere inversion publica y privada sostenida. Los estudiantes de hoy son los lideres
tecnologicos de manana."""

TEXTO_CIENTIFICO = """El procesamiento de lenguaje natural permite a las computadoras
comprender y generar texto humano. Los modelos de aprendizaje profundo como BERT y GPT
han revolucionado este campo. La representacion vectorial de documentos mediante TF-IDF
sigue siendo fundamental para sistemas de recuperacion de informacion. Los algoritmos de
clasificacion como Naive Bayes y SVM logran alta precision en categorizacion de texto.
El analisis de sentimientos combina tecnicas lexicas con aprendizaje automatico para
determinar la polaridad emocional de un texto. Las redes neuronales recurrentes procesan
secuencias de palabras capturando dependencias temporales. Los transformadores han
demostrado superioridad en tareas de traduccion automatica y resumen de texto. La
tokenizacion y la normalizacion son pasos previos esenciales en cualquier pipeline NLP.
El corpus de entrenamiento determina la calidad del modelo resultante. La evaluacion
mediante metricas como precision, recall y F1 permite comparar sistemas de forma objetiva."""


def imprimir_analisis(analisis: dict) -> None:
    print(f"--- {analisis['titulo']} ---")
    print(f"  Oraciones              : {analisis['oraciones']}")
    print(f"  Palabras totales       : {analisis['palabras_totales']}")
    print(f"  Vocabulario unico      : {analisis['vocabulario_unico']}")
    print(f"  Riqueza lexica global  : {analisis['riqueza_lexica_global']:.3f}")
    print(f"  Prom. palabras/oracion : {analisis['promedio_palabras_oracion']:.1f}")

    riqueza_sec = [f"{v:.3f}" for v in analisis["riqueza_por_seccion"]]
    print(f"  Riqueza por seccion    : {riqueza_sec}")

    top_b = [(f"{b[0]} {b[1]}", c) for b, c in analisis["top_bigramas"][:4]]
    print(f"  Top bigramas           : {top_b}")

    top_t = [(f"{t[0]} {t[1]} {t[2]}", c) for t, c in analisis["top_trigramas"][:3]]
    print(f"  Top trigramas          : {top_t}")

    entidades = [e for e, _ in analisis["posibles_entidades"][:6]]
    print(f"  Entidades detectadas   : {entidades}")
    print()


def imprimir_comparativa(comparativa: list[dict]) -> None:
    print("--- Comparativa entre textos ---")
    cabecera = f"{'Texto':<22} {'Palabras':>9} {'Vocab':>7} {'Riqueza':>8} {'P/Oracion':>10} {'Top bigrama':<22} {'Top trigrama'}"
    print(cabecera)
    print("-" * len(cabecera))
    for fila in comparativa:
        print(
            f"{fila['titulo']:<22} {fila['palabras']:>9} {fila['vocabulario']:>7} "
            f"{fila['riqueza']:>8.3f} {fila['promedio_oracion']:>10.1f} "
            f"{fila['top_bigrama']:<22} {fila['top_trigrama']}"
        )
    print()


def main() -> None:
    print("=== AC-2: Analisis Estadistico de Discursos ===\n")

    print("Verificando recursos NLTK...")
    descargar_recursos()
    print("Recursos listos.\n")

    analizador = AnalisisDiscurso()

    analisis_disc = analizador.analizar(TEXTO_DISCURSO, "Discurso Educativo")
    analisis_cient = analizador.analizar(TEXTO_CIENTIFICO, "Texto Cientifico NLP")

    for analisis in [analisis_disc, analisis_cient]:
        imprimir_analisis(analisis)

    comparativa = analizador.comparar_textos([analisis_disc, analisis_cient])
    imprimir_comparativa(comparativa)

    AnalisisDiscurso.guardar_json(SALIDA_JSON, [analisis_disc, analisis_cient], comparativa)
    print(f"Resultados guardados en: {SALIDA_JSON}")

    tokens_disc = analisis_disc.get("_tokens_filtrados", [])
    generada = generar_nube_palabras(tokens_disc, SALIDA_NUBE)
    if generada:
        print(f"Nube de palabras guardada en: {SALIDA_NUBE}")
    else:
        print("Nube de palabras no generada (instala 'wordcloud' con: pip install wordcloud)")

    print("\nListo. Archivo JSON compatible con el pipeline SIMANW.")


if __name__ == "__main__":
    main()
