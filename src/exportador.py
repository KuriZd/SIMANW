from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class ExportadorNoticias:
    """Guarda las noticias extraídas en formatos reutilizables."""

    def __init__(self, carpeta_salida: str = "data") -> None:
        self.carpeta_salida = Path(carpeta_salida)
        self.carpeta_salida.mkdir(parents=True, exist_ok=True)

    def guardar_json(self, noticias: list[dict], nombre_archivo: str = "noticias_extraidas.json") -> Path:
        ruta = self.carpeta_salida / nombre_archivo
        guardar_json(noticias, ruta)
        return ruta

    def guardar_csv(self, noticias: list[dict], nombre_archivo: str = "noticias_extraidas.csv") -> Path:
        ruta = self.carpeta_salida / nombre_archivo
        guardar_csv(noticias, ruta)
        return ruta


def guardar_json(datos: Any, ruta: str | Path) -> Path:
    """Guarda datos serializables en JSON creando directorios intermedios."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    return ruta


def guardar_csv(filas: list[dict], ruta: str | Path) -> Path:
    """Guarda una lista de diccionarios como CSV con columnas estables."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    if not filas:
        ruta.write_text("", encoding="utf-8")
        return ruta

    campos: list[str] = []
    for fila in filas:
        for campo in fila.keys():
            if campo not in campos:
                campos.append(campo)

    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        for fila in filas:
            writer.writerow({campo: _valor_csv(fila.get(campo, "")) for campo in campos})

    return ruta


def guardar_markdown(contenido: str, ruta: str | Path) -> Path:
    """Guarda contenido Markdown creando directorios intermedios."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def _valor_csv(valor: Any) -> Any:
    if isinstance(valor, (dict, list, tuple)):
        return json.dumps(valor, ensure_ascii=False)
    return valor
