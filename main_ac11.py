"""AC-11: Estudio de usabilidad del buscador y chatbot.

Uso:
    python main_ac11.py
"""
from __future__ import annotations

from pathlib import Path

from src.usabilidad import estudio_demo


def main() -> None:
    print("=== AC-11: Estudio de Usabilidad del Buscador y Chatbot ===\n")

    estudio = estudio_demo()

    print("Guion de tareas:")
    for idx, tarea in enumerate(estudio.tareas, start=1):
        print(f"  {idx}. {tarea}")

    print("\nPromedios del cuestionario (escala 1-5):")
    for item, promedio in estudio.promedios().items():
        print(f"  {item}: {promedio}")

    print("\nProblemas identificados y mejoras propuestas:")
    for item in estudio.problemas_y_mejoras():
        print(f"  - Problema : {item['problema']}")
        print(f"    Mejora   : {item['mejora']}")
        print()

    print("Reflexion sobre consentimiento informado:")
    print(estudio.reflexion_consentimiento())

    ruta_csv = estudio.exportar_csv("data/ac11_resultados_usabilidad.csv")
    ruta_reporte = estudio.guardar_reporte_markdown("reports/usabilidad_ac11.md")
    ruta_etica = estudio.guardar_reflexion_etica("reports/reflexion_etica_ac11.md")

    print(f"\nArchivos generados:")
    print(f"  {ruta_csv}")
    print(f"  {ruta_reporte}")
    print(f"  {ruta_etica}")


if __name__ == "__main__":
    main()
