"""AC-8: Control de calidad del corpus rastreado.

Uso:
    python main_ac8.py
    python main_ac8.py data/noticias_extraidas.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.control_calidad import ControlCalidadCorpus


NOTICIAS_DEMO = [
    {
        "titulo": "Avances en inteligencia artificial generativa",
        "cuerpo": "La inteligencia artificial generativa transforma procesos de software, educacion y analisis de datos a gran escala.",
        "fecha": "2026-05-10",
        "autor": "Maria Garcia",
        "categoria_original": "tecnologia",
        "url": "https://demo.test/noticias/ia",
        "fuente": "https://demo.test",
    },
    {
        "titulo": "Mercados reaccionan a nuevas tasas",
        "cuerpo": "La Reserva Federal ajusta tasas de interes ante presiones inflacionarias y expectativas del mercado de valores.",
        "fecha": "2026-05-11",
        "autor": "Juan Lopez",
        "categoria_original": "economia",
        "url": "https://demo.test/noticias/economia",
        "fuente": "https://demo.test",
    },
    {
        "titulo": "",
        "cuerpo": "Noticia sin titulo, debe ser rechazada.",
        "fecha": "2026-05-12",
        "autor": "Autor",
        "categoria_original": "general",
        "url": "https://demo.test/noticias/sin-titulo",
        "fuente": "https://demo.test",
    },
    {
        "titulo": "Cuerpo muy corto",
        "cuerpo": "corto",
        "fecha": "2026-05-12",
        "autor": "Autor",
        "categoria_original": "general",
        "url": "https://demo.test/noticias/corto",
        "fuente": "https://demo.test",
    },
    {
        "titulo": "Fecha con formato incorrecto",
        "cuerpo": "Esta noticia tiene una fecha en formato incorrecto que no sigue el estandar ISO YYYY-MM-DD.",
        "fecha": "25/05/2026",
        "autor": "Autor",
        "categoria_original": "general",
        "url": "https://demo.test/noticias/fecha",
        "fuente": "https://demo.test",
    },
    {
        "titulo": "Duplicado exacto por URL",
        "cuerpo": "Esta noticia comparte la misma URL que la primera, por lo que sera detectada como duplicado exacto.",
        "fecha": "2026-05-13",
        "autor": "Autor Copia",
        "categoria_original": "tecnologia",
        "url": "https://demo.test/noticias/ia",
        "fuente": "https://demo.test",
    },
    {
        "titulo": "Avances en inteligencia artificial generativa",
        "cuerpo": "Cuerpo distinto pero titulo identico al primer registro, detectado como duplicado casi identico.",
        "fecha": "2026-05-14",
        "autor": "Otro Autor",
        "categoria_original": "tecnologia",
        "url": "https://demo.test/noticias/ia-copia",
        "fuente": "https://demo.test",
    },
]


def cargar_noticias(arg: str | None) -> list[dict]:
    if arg is None:
        return NOTICIAS_DEMO
    ruta = Path(arg)
    if not ruta.exists():
        print(f"Archivo no encontrado: {ruta}. Usando corpus demo.")
        return NOTICIAS_DEMO
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return datos if isinstance(datos, list) else NOTICIAS_DEMO


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    noticias = cargar_noticias(arg)

    print("=== AC-8: Control de Calidad del Corpus ===\n")

    control = ControlCalidadCorpus()
    depurado = control.validar(noticias)

    informe = control.generar_informe()
    print(f"Total registros    : {informe['total_registros']}")
    print(f"Validos            : {informe['registros_validos']}")
    print(f"Rechazados         : {informe['registros_rechazados']}")
    print(f"Invalidos/incompl. : {informe['invalidos_o_incompletos']}")
    print(f"Duplicados URL     : {informe['duplicados_exactos_url']}")
    print(f"Duplicados titulo  : {informe['duplicados_casi_identicos_titulo']}")
    print(f"Corpus depurado    : {len(depurado)} noticias")

    print("\nResumen:\n")
    print(control.parrafo_resumen())

    ruta_informe = control.guardar_informe("data/ac8_informe_calidad.json")
    ruta_depurado = control.guardar_corpus_depurado("data/corpus_depurado_ac8.json")
    ruta_rechazados = control.guardar_rechazados("data/registros_rechazados_ac8.json")
    ruta_md = control.guardar_resumen_markdown("reports/resumen_calidad_ac8.md")

    print(f"\nArchivos generados:")
    print(f"  {ruta_informe}")
    print(f"  {ruta_depurado}")
    print(f"  {ruta_rechazados}")
    print(f"  {ruta_md}")


if __name__ == "__main__":
    main()
