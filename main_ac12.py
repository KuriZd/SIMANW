"""AC-12: Trazabilidad y reproducibilidad del pipeline.

Uso:
    python main_ac12.py
"""
from __future__ import annotations

from pathlib import Path

from src.trazabilidad import trazabilidad_demo


ARCHIVOS_SALIDA = {
    "rastreo_paginado": "data/ac1_noticias_paginadas.json",
    "calidad": "data/ac8_informe_calidad.json",
    "tendencias": "data/ac9_tendencias.csv",
    "consultas_guardadas": "data/ac10_consultas_guardadas.json",
    "historial_alertas": "data/ac10_historial_alertas.json",
    "usabilidad": "data/ac11_resultados_usabilidad.csv",
}

ALUMNO = "Alumno SIMANW"


def main() -> None:
    print("=== AC-12: Trazabilidad y Reproducibilidad del Pipeline ===\n")

    traza = trazabilidad_demo()

    ruta_manifiesto = traza.guardar_manifiesto("data/ac12_manifiesto.json", ARCHIVOS_SALIDA)
    ruta_log = traza.guardar_log_jsonl("logs/ac12_log.jsonl")
    ruta_checklist = traza.guardar_checklist("reports/checklist_ac12.md", ALUMNO)
    ruta_limitaciones = traza.guardar_limitaciones("reports/limitaciones_ac12.md")

    print("Procedimiento reproducible:")
    print(traza.procedimiento_reproducible())

    print("\nChecklist firmado:")
    print(traza.checklist_firmado(ALUMNO))

    print("\nAnexo de limitaciones:")
    print(traza.anexo_limitaciones())

    print(f"\nArchivos generados:")
    print(f"  {ruta_manifiesto}")
    print(f"  {ruta_log}")
    print(f"  {ruta_checklist}")
    print(f"  {ruta_limitaciones}")


if __name__ == "__main__":
    main()
