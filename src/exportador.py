from __future__ import annotations

import csv
import json
from pathlib import Path


class ExportadorNoticias:
    """Guarda las noticias extraídas en formatos reutilizables."""

    def __init__(self, carpeta_salida: str = "data") -> None:
        self.carpeta_salida = Path(carpeta_salida)
        self.carpeta_salida.mkdir(parents=True, exist_ok=True)

    def guardar_json(self, noticias: list[dict], nombre_archivo: str = "noticias_extraidas.json") -> Path:
        ruta = self.carpeta_salida / nombre_archivo
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(noticias, archivo, ensure_ascii=False, indent=2)
        return ruta

    def guardar_csv(self, noticias: list[dict], nombre_archivo: str = "noticias_extraidas.csv") -> Path:
        ruta = self.carpeta_salida / nombre_archivo

        if not noticias:
            ruta.write_text("", encoding="utf-8")
            return ruta

        with ruta.open("w", encoding="utf-8", newline="") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=noticias[0].keys())
            writer.writeheader()
            writer.writerows(noticias)

        return ruta
