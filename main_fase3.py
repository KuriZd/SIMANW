from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.clasificador_noticias import (
    ETIQUETAS_ENTRENAMIENTO,
    TEXTOS_ENTRENAMIENTO,
    ClasificadorNoticias,
)
from src.detector_publicidad import DetectorTemasPublicidad, NOTA_ETICA_PUBLICIDAD
from src.exportador import guardar_json, guardar_markdown
from src.html_demo import html_portal_noticias
from src.extractor import ExtractorNoticias
from src.recomendacion import SistemaRecomendacion
from src.sentimientos import AnalizadorSentimientos


RUTAS_DATOS = [
    Path("data/noticias_extraidas.json"),
    Path("data/noticias_ac1.json"),
    Path("data/corpus_depurado_ac8.json"),
]


def cargar_noticias_fase3() -> tuple[list[dict], str]:
    for ruta in RUTAS_DATOS:
        if ruta.exists():
            with ruta.open(encoding="utf-8") as archivo:
                datos = json.load(archivo)
            if isinstance(datos, list) and datos:
                return [_normalizar_noticia(n) for n in datos if isinstance(n, dict)], str(ruta)

    extractor = ExtractorNoticias()
    noticias = extractor.extraer_de_html(html_portal_noticias, url_base="https://portal-noticias.com")
    return [_normalizar_noticia(n) for n in noticias], "demo local"


def ejecutar_clasificacion(noticias: list[dict]) -> tuple[ClasificadorNoticias, dict]:
    print("Entrenamiento del clasificador")
    clasificador = ClasificadorNoticias()
    resultado_entrenamiento = clasificador.entrenar(TEXTOS_ENTRENAMIENTO, ETIQUETAS_ENTRENAMIENTO)
    clasificador.clasificar_noticias(noticias)
    print(f"Categorias detectadas: {resultado_entrenamiento['categorias']}")
    print(f"Noticias clasificadas: {len(noticias)}")
    return clasificador, resultado_entrenamiento


def ejecutar_sentimientos(noticias: list[dict]) -> dict:
    analizador = AnalizadorSentimientos()
    resultados, resumen = analizador.analizar_noticias(noticias)
    print(f"Resumen de sentimiento: {resumen['distribucion']} | promedio={resumen['sentimiento_promedio']:+.3f}")
    return {"resultados": resultados, "resumen": resumen}


def ejecutar_recomendaciones(noticias: list[dict]) -> dict:
    recomendador = SistemaRecomendacion(noticias)
    por_noticia = {
        str(indice): recomendador.recomendar_detallado(indice, top_n=2)
        for indice in range(len(noticias))
    }
    perfil = recomendador.recomendar_por_perfil_detallado(list(range(min(2, len(noticias)))), top_n=3)
    print("Recomendaciones por contenido generadas")
    return {"por_noticia": por_noticia, "perfil_usuario": perfil}


def ejecutar_conversacion() -> dict:
    detector = DetectorTemasPublicidad()
    conversacion = [
        ("Laura", "La inteligencia artificial esta cambiando el desarrollo de software"),
        ("Miguel", "Tambien me interesan las inversiones y las tasas de interes"),
        ("Ana", "Los laboratorios publicaron un estudio cientifico sobre clima"),
        ("Roberto", "Prefiero revisar informacion general antes de decidir"),
    ]
    resultados = detector.simular_chat(conversacion)
    resumen = detector.resumen_temas()
    print(f"Temas detectados en conversacion: {resumen['temas']}")
    return {"resultados": resultados, "resumen": resumen}


def exportar_resultados(resultados: dict) -> tuple[Path, Path]:
    ruta_json = guardar_json(resultados, "data/resultados_fase3.json")
    ruta_md = guardar_markdown(_reporte_markdown(resultados), "reports/reporte_fase3.md")
    return ruta_json, ruta_md


def main() -> None:
    noticias, fuente = cargar_noticias_fase3()
    print("=== Fase 3: Clasificacion y Analisis Automatico ===")
    print(f"Fuente de datos: {fuente}")
    print(f"Noticias cargadas: {len(noticias)}\n")

    _, entrenamiento = ejecutar_clasificacion(noticias)
    sentimientos = ejecutar_sentimientos(noticias)
    recomendaciones = ejecutar_recomendaciones(noticias)
    conversacion = ejecutar_conversacion()

    resultados = {
        "fase": "Fase 3",
        "fuente_datos": fuente,
        "clasificacion": {
            "entrenamiento": {
                "accuracy_cv": entrenamiento["accuracy_cv"],
                "categorias": entrenamiento["categorias"],
                "n_muestras": entrenamiento["n_muestras"],
            },
            "noticias": [
                {
                    "indice": indice,
                    "titulo": noticia.get("titulo", ""),
                    "categoria_original": noticia.get("categoria_original", ""),
                    "categoria_predicha": noticia.get("categoria_predicha", ""),
                    "scores_categoria": noticia.get("scores_categoria", {}),
                }
                for indice, noticia in enumerate(noticias)
            ],
        },
        "sentimientos": sentimientos,
        "recomendaciones": recomendaciones,
        "conversacion": conversacion,
        "notas": {
            "vader": "VADER funciona mejor en ingles; para textos en espanol se usa como aproximacion inicial con un ajuste lexico local.",
            "etica": NOTA_ETICA_PUBLICIDAD,
        },
    }

    ruta_json, ruta_md = exportar_resultados(resultados)
    print(f"\nExportacion JSON: {ruta_json}")
    print(f"Reporte Markdown: {ruta_md}")


def _normalizar_noticia(noticia: dict) -> dict:
    titulo = str(noticia.get("titulo") or noticia.get("title") or "Sin titulo")
    cuerpo = str(noticia.get("cuerpo") or noticia.get("resumen") or noticia.get("texto_original") or titulo)
    categoria = (
        noticia.get("categoria_original")
        or noticia.get("categoria")
        or noticia.get("categoria_predicha")
        or "sin_categoria"
    )
    normalizada = dict(noticia)
    normalizada.update(
        {
            "titulo": titulo,
            "cuerpo": cuerpo,
            "resumen": str(noticia.get("resumen") or cuerpo[:180]),
            "categoria_original": str(categoria),
            "categoria": str(noticia.get("categoria") or categoria),
            "url": str(noticia.get("url") or ""),
            "fuente": str(noticia.get("fuente") or noticia.get("fuente_nombre") or ""),
        }
    )
    return normalizada


def _reporte_markdown(resultados: dict) -> str:
    clasificacion = resultados["clasificacion"]["entrenamiento"]
    sentimientos = resultados["sentimientos"]["resumen"]
    temas = Counter(
        item["tema"]
        for item in resultados["conversacion"]["resultados"]
    )
    return "\n".join(
        [
            "# Reporte Fase 3",
            "",
            "## Clasificacion",
            f"- Noticias clasificadas: {len(resultados['clasificacion']['noticias'])}",
            f"- Categorias de entrenamiento: {', '.join(clasificacion['categorias'])}",
            f"- Accuracy CV: {clasificacion['accuracy_cv']:.3f}",
            "",
            "## Sentimientos",
            f"- Distribucion: {sentimientos['distribucion']}",
            f"- Sentimiento promedio: {sentimientos['sentimiento_promedio']:+.3f}",
            f"- Tono general: {sentimientos['tono_general']}",
            "",
            "Nota: VADER funciona mejor en ingles; para textos en espanol se usa como aproximacion inicial con un ajuste lexico local.",
            "",
            "## Recomendaciones",
            f"- Perfiles generados: {len(resultados['recomendaciones']['perfil_usuario'])}",
            f"- Noticias con recomendaciones: {len(resultados['recomendaciones']['por_noticia'])}",
            "",
            "## Conversacion y publicidad simulada",
            f"- Temas detectados: {dict(temas)}",
            "",
            f"Nota etica: {NOTA_ETICA_PUBLICIDAD}",
            "",
        ]
    )


if __name__ == "__main__":
    main()
