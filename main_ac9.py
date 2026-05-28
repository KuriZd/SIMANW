"""AC-9: Linea de tiempo y tendencias por tema.

Uso:
    python main_ac9.py
    python main_ac9.py data/noticias_extraidas.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.tendencias_temporales import NOTICIAS_AC9_DEMO, TendenciasTemporales


def cargar_noticias(arg: str | None) -> list[dict]:
    if arg is None:
        return NOTICIAS_AC9_DEMO
    ruta = Path(arg)
    if not ruta.exists():
        print(f"Archivo no encontrado: {ruta}. Usando corpus demo.")
        return NOTICIAS_AC9_DEMO
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return datos if isinstance(datos, list) else NOTICIAS_AC9_DEMO


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    noticias = cargar_noticias(arg)

    print("=== AC-9: Linea de Tiempo y Tendencias por Tema ===\n")
    print("Granularidad: mensual")
    print("Justificacion: el corpus abarca varios meses; el mes ofrece periodos")
    print("suficientes sin fragmentar un corpus de tamano medio.\n")

    analizador = TendenciasTemporales(granularidad="mes")
    analizador.cargar_noticias(noticias)

    print("--- Visualizacion ASCII (noticias por categoria y mes) ---")
    print(analizador.visualizacion_texto())
    print()

    print("--- Tabla Resumen ---")
    print(f"{'Categoria':<15} {'Periodo':<12} {'Noticias':>8}")
    print("-" * 38)
    for fila in analizador.tabla_resumen():
        print(f"  {fila['categoria']:<13} {fila['periodo']:<12} {fila['noticias']:>8}")

    ruta_csv = analizador.exportar_csv("data/ac9_tendencias.csv")
    print(f"\n  Tabla exportada: {ruta_csv}")

    pico = analizador.pico_notable()
    print(f"\n--- Pico Notable ---")
    print(f"  Categoria: {pico['categoria']} | Periodo: {pico['periodo']} | Noticias: {pico['count']}")
    for titulo in pico["titulos"][:3]:
        print(f"  - {titulo[:65]}")

    conteos = analizador.conteo_por_periodo()
    categorias_top = sorted(conteos, key=lambda c: sum(conteos[c].values()), reverse=True)[:3]
    print("\n--- Tendencias de Terminos (primer vs. ultimo periodo) ---")
    for cat in categorias_top:
        tend = analizador.tendencia_terminos(cat)
        if tend["aumentan"] or tend["disminuyen"]:
            print(f"\n  [{cat}]  {tend['primer_periodo']} -> {tend['ultimo_periodo']}")
            print(f"  Aumentan  : {tend['aumentan'][:4]}")
            print(f"  Disminuyen: {tend['disminuyen'][:4]}")

    print()
    print(analizador.conclusion())

    ruta_json = analizador.guardar_reporte_json("reports/tendencias_ac9.json")
    ruta_md = analizador.guardar_conclusion_markdown("reports/conclusion_tendencias_ac9.md")

    try:
        ruta_png = analizador.exportar_png("reports/tendencias_ac9.png")
        print(f"\nGrafico PNG generado: {ruta_png}")
    except Exception as exc:
        print(f"\n  (PNG omitido: {exc})")

    print(f"\nArchivos generados:")
    print(f"  {ruta_csv}")
    print(f"  {ruta_json}")
    print(f"  {ruta_md}")


if __name__ == "__main__":
    main()
