"""AC-1: Rastreo con paginacion en un sitio real.

Uso:
    python main_ac1.py                  # Hacker News (predeterminado)
    python main_ac1.py hacker_news      # Hacker News
    python main_ac1.py unam_noticias    # UNAM Noticias (verificar robots.txt)
    python main_ac1.py simulado         # Demo local sin peticiones reales
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.rastreador_paginado import RastreadorPaginado, crear_fetcher_simulado

SALIDA_JSON = Path("data") / "noticias_ac1.json"

# ---------------------------------------------------------------------------
# Configuraciones de portales
# Agrega aqui nuevos sitios respetando robots.txt y terminos de uso.
# ---------------------------------------------------------------------------
CONFIGS: dict[str, dict] = {
    # Hacker News: robots.txt no bloquea bots genericos; estructura HTML simple.
    "hacker_news": {
        "url_base": "https://news.ycombinator.com/",
        "fuente": "Hacker News",
        "selector_articulos": ".athing",
        "selector_siguiente": ".morelink",
        "selector_titulo": ".titleline > a",
        "selector_resumen": None,
        "selector_url": ".titleline > a",
        "delay": 3.0,
        "max_paginas": 4,
        "max_noticias": 20,
        "user_agent": "SIMANWBot/1.0 (proyecto-academico ITM)",
        "respetar_robots": True,
    },
    # UNAM Noticias: portal en espanol. Verifica robots.txt antes de ejecutar.
    # Los selectores CSS pueden variar si el sitio actualiza su plantilla.
    "unam_noticias": {
        "url_base": "https://www.noticias.unam.mx/",
        "fuente": "UNAM Noticias",
        "selector_articulos": "article",
        "selector_siguiente": "a[rel='next'], .pagination .next a",
        "selector_titulo": "h2 a, h3 a, .entry-title a",
        "selector_resumen": ".entry-summary, .excerpt, p",
        "selector_url": "h2 a, h3 a, .entry-title a",
        "delay": 3.0,
        "max_paginas": 3,
        "max_noticias": 20,
        "user_agent": "SIMANWBot/1.0 (proyecto-academico ITM)",
        "respetar_robots": True,
    },
    # Demo local: sin peticiones HTTP, util para clase o pruebas rapidas.
    "simulado": {
        "url_base": "https://ejemplo-noticias.test/noticias?page=1",
        "fuente": "Demo SIMANW",
        "selector_articulos": "article",
        "selector_siguiente": "a.next-page",
        "selector_titulo": None,
        "selector_resumen": None,
        "selector_url": None,
        "delay": 0.0,
        "max_paginas": 4,
        "max_noticias": 20,
        "user_agent": "SIMANWBot/1.0",
        "respetar_robots": False,
    },
}


def main() -> None:
    nombre = sys.argv[1] if len(sys.argv) > 1 else "hacker_news"

    if nombre not in CONFIGS:
        print(f"Portal desconocido: '{nombre}'")
        print(f"Opciones disponibles: {', '.join(CONFIGS)}")
        sys.exit(1)

    config = CONFIGS[nombre]
    es_simulado = nombre == "simulado"

    print(f"=== AC-1: Rastreo Paginado — {config['fuente']} ===\n")
    print(f"URL base      : {config['url_base']}")
    print(f"Delay         : {config['delay']}s entre paginas")
    print(f"Max noticias  : {config['max_noticias']}")
    print(f"Max paginas   : {config['max_paginas']}")
    print(f"robots.txt    : {'activo' if config['respetar_robots'] else 'desactivado'}")
    print()

    fetcher = crear_fetcher_simulado(noticias_por_pagina=5, total_paginas=4) if es_simulado else None

    rastreador = RastreadorPaginado(
        url_base=config["url_base"],
        fuente=config["fuente"],
        selector_articulos=config["selector_articulos"],
        selector_siguiente=config["selector_siguiente"],
        selector_titulo=config.get("selector_titulo"),
        selector_resumen=config.get("selector_resumen"),
        selector_url=config.get("selector_url"),
        delay=config["delay"],
        max_paginas=config["max_paginas"],
        max_noticias=config["max_noticias"],
        user_agent=config["user_agent"],
        fetcher=fetcher,
        respetar_robots=config["respetar_robots"],
    )

    print("Verificando robots.txt...")
    if not rastreador.puede_rastrear(config["url_base"]):
        print("robots.txt bloquea el rastreo en esta URL.")
        print("Ajusta la configuracion o elige otro portal en CONFIGS dentro de main_ac1.py.")
        sys.exit(0)

    print("Rastreo permitido. Iniciando...\n")

    resultados = rastreador.rastrear()

    print(f"Paginas visitadas : {len(rastreador.paginas_visitadas)}")
    print(f"Noticias extraidas: {len(resultados)}")

    if not resultados:
        print("\nNo se extrajeron noticias.")
        print("Verifica los selectores CSS del sitio con las herramientas de desarrollador del navegador.")
        sys.exit(0)

    print("\nPrimeras 5 noticias:")
    for i, noticia in enumerate(resultados[:5], 1):
        titulo = noticia["titulo"][:75] + "..." if len(noticia["titulo"]) > 75 else noticia["titulo"]
        url = noticia["url"][:75] + "..." if len(noticia["url"]) > 75 else noticia["url"]
        print(f"  {i}. {titulo}")
        print(f"     {url}")

    total = rastreador.guardar_json(SALIDA_JSON)
    print(f"\nGuardado: {SALIDA_JSON} ({total} noticias)")
    print("Listo. El archivo puede usarse como entrada para el pipeline SIMANW.")


if __name__ == "__main__":
    main()
