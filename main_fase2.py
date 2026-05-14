from __future__ import annotations

from main import (
    ejecutar_control_rastreo,
    ejecutar_extraccion,
    ejecutar_exportacion,
    ejecutar_parser_dom,
    ejecutar_pipeline_nlp,
    ejecutar_representacion_vectorial,
    ejecutar_similitud,
)


def main() -> None:
    ejecutar_parser_dom()
    noticias = ejecutar_extraccion()
    ejecutar_control_rastreo()
    ejecutar_pipeline_nlp(noticias)
    representacion = ejecutar_representacion_vectorial(noticias)
    ejecutar_similitud(noticias, representacion)
    ejecutar_exportacion(noticias)


if __name__ == "__main__":
    main()
