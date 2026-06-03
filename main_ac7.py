"""AC-7: Enriquecimiento del Knowledge Graph con Wikidata.

Uso:
    python main_ac7.py                         # grafo demo integrado
    python main_ac7.py data/kg_simanw.ttl      # grafo Turtle existente
    python main_ac7.py data/noticias_ac1.json  # construir KG desde noticias JSON
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.enriquecedor_kg import (
    EnriquecedorKG,
    cargar_grafo_desde_turtle,
    crear_grafo_demo,
    crear_uri_entidad,
)

SALIDA_TTL = Path("data") / "kg_enriquecido_ac7.ttl"
SALIDA_JSON = Path("data") / "enlaces_wikidata_ac7.json"

DATOS = Namespace = None  # se define tras importar rdflib

from rdflib import Namespace as _NS

DATA = _NS("http://simanw.org/data/")

ENTIDADES_WIKIDATA = [
    (DATA["categoria_tecnologia"], "Q11016",  "Tecnologia de la informacion"),
    (DATA["categoria_economia"],   "Q159810", "Economia"),
    (DATA["categoria_ciencia"],    "Q336",    "Ciencia"),
    (DATA["categoria_gobierno"],   "Q7188",   "Gobierno"),
    (DATA["categoria_salud"],      "Q12136",  "Salud"),
]

PROPIEDADES_EXTERNAS = {
    DATA["categoria_tecnologia"]: {
        "P279": "Sector economico terciario",
        "P910": "Categoria: Tecnologia de la informacion",
    },
    DATA["categoria_economia"]: {
        "P279": "Ciencias sociales",
    },
}


def cargar_grafo(arg: str | None):
    """Devuelve (grafo, descripcion) segun el argumento."""
    if arg is None:
        return crear_grafo_demo(), "grafo demo integrado"

    ruta = Path(arg)
    if not ruta.exists():
        print(f"Archivo no encontrado: {ruta}. Usando grafo demo.")
        return crear_grafo_demo(), "grafo demo integrado"

    ext = ruta.suffix.lower()
    if ext in (".ttl", ".rdf", ".n3"):
        try:
            return cargar_grafo_desde_turtle(ruta), str(ruta)
        except Exception as exc:
            print(f"Error al cargar Turtle: {exc}. Usando grafo demo.")
            return crear_grafo_demo(), "grafo demo integrado"

    if ext == ".json":
        try:
            return _grafo_desde_json(ruta), str(ruta)
        except Exception as exc:
            print(f"Error al cargar JSON: {exc}. Usando grafo demo.")
            return crear_grafo_demo(), "grafo demo integrado"

    print(f"Formato no reconocido: {ext}. Usando grafo demo.")
    return crear_grafo_demo(), "grafo demo integrado"


def _grafo_desde_json(ruta: Path):
    """Construye un KG completo desde noticias JSON y retorna el grafo rdflib."""
    import json
    from src.knowledge_graph import KnowledgeGraphSIMANW

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    noticias = datos if isinstance(datos, list) else []
    kg = KnowledgeGraphSIMANW()
    kg.construir_desde_noticias(noticias)
    return kg.graph


def imprimir_enlaces(enriquecedor: EnriquecedorKG) -> None:
    print("\nEnlaces locales -> Wikidata:")
    for enlace in enriquecedor.enlaces_externos:
        local_id = enlace["local"].rsplit("/", 1)[-1]
        print(f"  {local_id:<30} -> {enlace['wikidata_id']}  ({enlace['etiqueta']})")


def imprimir_consulta_sparql(enriquecedor: EnriquecedorKG, tema: str) -> None:
    print(f"\nQuery SPARQL sugerida para Wikidata [{tema}]:")
    print(enriquecedor.generar_query_wikidata(tema))


def verificar_consulta_local(enriquecedor: EnriquecedorKG) -> None:
    print("\n--- Verificacion SPARQL local (owl:sameAs) ---")
    resultados = enriquecedor.consulta_enriquecimiento()
    if not resultados:
        print("  (sin resultados)")
        return
    for fila in resultados:
        local_id = str(fila.local).rsplit("/", 1)[-1]
        externo_id = str(fila.externo).rsplit("/", 1)[-1]
        etiqueta = str(fila.etiqueta)
        print(f"  {local_id:<30} owl:sameAs  wd:{externo_id}  \"{etiqueta}\"")


def demo_buscar_entidad(enriquecedor: EnriquecedorKG) -> None:
    print("\n--- Query generada para buscar entidad por nombre ---")
    query_busqueda = enriquecedor.buscar_entidad_wikidata("Mexico")
    print(query_busqueda)


def demo_consulta_wikidata(enriquecedor: EnriquecedorKG) -> None:
    print("\n--- Consulta opcional al endpoint real de Wikidata ---")
    query = enriquecedor.generar_query_wikidata("gobierno")
    resultados = enriquecedor.consultar_wikidata(query)
    if resultados:
        print(f"  Resultados obtenidos: {len(resultados)}")
        for r in resultados[:3]:
            print(f"  {r}")
    else:
        print("  (sin conexion o SPARQLWrapper no disponible — enriquecimiento local completado igualmente)")


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    grafo, origen = cargar_grafo(arg)

    print("=== AC-7: Enriquecimiento con Wikidata ===\n")
    print(f"Origen     : {origen}")
    print(f"Triples KG : {len(grafo)}")

    enriquecedor = EnriquecedorKG(grafo)

    print("\n--- Enlazando entidades locales con Wikidata ---")
    for entidad, wid, etiqueta in ENTIDADES_WIKIDATA:
        enriquecedor.enlazar_entidad(entidad, wid, etiqueta)

    print("--- Agregando propiedades externas ---")
    for entidad, props in PROPIEDADES_EXTERNAS.items():
        enriquecedor.agregar_datos_externos(entidad, props)

    print(f"\nTriples totales tras enriquecimiento: {len(grafo)}")
    print(f"Enlaces externos creados: {len(enriquecedor.enlaces_externos)}")

    imprimir_enlaces(enriquecedor)
    verificar_consulta_local(enriquecedor)
    imprimir_consulta_sparql(enriquecedor, "tecnologia")

    print("\n--- Crear URI desde nombre libre ---")
    uri = crear_uri_entidad("Inteligencia Artificial")
    print(f"  'Inteligencia Artificial'  ->  {uri}")

    demo_buscar_entidad(enriquecedor)
    demo_consulta_wikidata(enriquecedor)

    enriquecedor.guardar_grafo(SALIDA_TTL)
    print(f"\nGrafo Turtle guardado : {SALIDA_TTL}")

    enriquecedor.guardar_reporte_json(SALIDA_JSON)
    print(f"Reporte JSON guardado : {SALIDA_JSON}")
    print("\nListo. Archivos compatibles con el pipeline SIMANW.")


if __name__ == "__main__":
    main()
