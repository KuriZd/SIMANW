"""AC-13: Publicacion semantica y validacion RDF del Knowledge Graph.

Uso:
    python main_ac13.py
    python main_ac13.py data/noticias_extraidas.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.knowledge_graph import (
    QUERY_AC13_AUTORES_PRODUCTIVOS,
    QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
    QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
    KnowledgeGraphSIMANW,
)
from src.tendencias_temporales import NOTICIAS_AC9_DEMO


def cargar_noticias(arg: str | None) -> list[dict]:
    if arg is None:
        return NOTICIAS_AC9_DEMO[:6]
    ruta = Path(arg)
    if not ruta.exists():
        print(f"Archivo no encontrado: {ruta}. Usando corpus demo.")
        return NOTICIAS_AC9_DEMO[:6]
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return (datos if isinstance(datos, list) else NOTICIAS_AC9_DEMO)[:6]


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    noticias_base = cargar_noticias(arg)

    print("=== AC-13: Publicacion Semantica y Validacion RDF ===\n")

    noticias_kg = []
    for indice, noticia in enumerate(noticias_base, start=1):
        noticias_kg.append(
            {
                **noticia,
                "autor": f"Autor {indice % 3}",
                "fuente": "https://demo.test",
                "url": f"https://demo.test/kg/{indice}",
                "sentimiento": {
                    "etiqueta": "positivo" if indice % 2 else "negativo",
                    "compound": 0.4 if indice % 2 else -0.3,
                },
            }
        )

    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(noticias_kg)

    enlaces = kg.agregar_enlaces_externos_basicos()
    rutas = kg.exportar_rdf("data/ac13_simanw")
    validacion = kg.validar_formas()

    print(f"Triples RDF              : {kg.total_triples()}")
    print(f"Turtle                   : {rutas['turtle']}")
    print(f"JSON-LD                  : {rutas['json-ld']}")
    print(f"Enlaces externos         : {len(enlaces)}")
    print(f"Validacion conforme      : {validacion['conforme']}")
    print(f"Violaciones SHACL        : {len(validacion['violaciones'])}")

    print("\nConsultas SPARQL propias del KG:")
    for nombre, query in [
        ("Autores productivos", QUERY_AC13_AUTORES_PRODUCTIVOS),
        ("Sentimiento por categoria", QUERY_AC13_SENTIMIENTO_POR_CATEGORIA),
        ("Noticias negativas recientes", QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS),
    ]:
        filas = kg.consultar(query)
        print(f"  {nombre}: {len(filas)} fila(s)")

    print("\nFragmento JSON-LD de ejemplo (noticia 1):")
    print(kg.fragmento_jsonld_noticia(1))

    print("\nNota de reutilizacion de datos:")
    print(kg.nota_reutilizacion_datos())

    print(f"\nArchivos generados:")
    print(f"  {rutas['turtle']}")
    print(f"  {rutas['json-ld']}")


if __name__ == "__main__":
    main()
