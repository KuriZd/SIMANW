"""AC-10: Sistema de alertas por consulta guardada.

Uso:
    python main_ac10.py
"""
from __future__ import annotations

from pathlib import Path

from src.alertas_consulta import SistemaAlertasConsulta, consultas_demo, noticias_nuevas_demo


def main() -> None:
    print("=== AC-10: Alertas por Consulta Guardada ===\n")

    sistema = SistemaAlertasConsulta(consultas_demo())
    ruta_consultas = sistema.guardar_consultas("data/ac10_consultas_guardadas.json")

    sin_nuevas = sistema.procesar_noticias_nuevas([])
    con_nuevas = sistema.procesar_noticias_nuevas(noticias_nuevas_demo(), "2026-05-25T12:00:00Z")
    repetidas = sistema.procesar_noticias_nuevas(noticias_nuevas_demo(), "2026-05-25T12:05:00Z")

    ruta_historial = sistema.guardar_historial("data/ac10_historial_alertas.json")

    print(f"Consultas persistidas          : {len(sistema.consultas)}")
    print(f"Ejecucion sin noticias nuevas  : {len(sin_nuevas)} alertas")
    print(f"Ejecucion con cinco noticias   : {len(con_nuevas)} alertas")
    print(f"Reprocesamiento (deduplicado)  : {len(repetidas)} alertas duplicadas")
    print()
    print("Mecanismo de deduplicacion:")
    print(sistema.documentar_deduplicacion())

    ruta_md = sistema.guardar_reporte_markdown("reports/alertas_ac10.md")

    print(f"\nArchivos generados:")
    print(f"  {ruta_consultas}")
    print(f"  {ruta_historial}")
    print(f"  {ruta_md}")


if __name__ == "__main__":
    main()
