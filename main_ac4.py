"""AC-4: Análisis de hilos de discusión de red social.

Uso:
    python main_ac4.py                        # hilo en español (predeterminado)
    python main_ac4.py en                     # hilo demo en inglés con VADER
    python main_ac4.py data/mi_hilo.json      # hilo desde archivo JSON
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.analizador_hilo import (
    HILO_IA_DEMO,
    HILO_IA_ES,
    AnalizadorHiloDiscusion,
    cargar_hilo_desde_json,
)

SALIDA_JSON = Path("data") / "analisis_hilo_ac4.json"


def cargar_hilo(arg: str | None) -> tuple[list[dict], str]:
    """Devuelve (mensajes, idioma) según el argumento recibido."""
    if arg is None or arg == "es":
        return HILO_IA_ES, "spanish"
    if arg == "en":
        return HILO_IA_DEMO, "english"
    ruta = Path(arg)
    if ruta.exists():
        try:
            return cargar_hilo_desde_json(ruta), "spanish"
        except Exception as exc:
            print(f"Error al cargar JSON: {exc}. Usando hilo en español.")
    return HILO_IA_ES, "spanish"


def imprimir_resumen(resumen: dict) -> None:
    print("--- Resumen general ---")
    print(f"  Mensajes      : {resumen['total_mensajes']}")
    print(f"  Participantes : {resumen['participantes']}")
    print(f"  Tono general  : {resumen['tono']}  (promedio: {resumen['sentimiento_promedio']:+.3f})")
    print(f"  Positivos     : {resumen['positivos_pct']:.0f}%")
    print(f"  Negativos     : {resumen['negativos_pct']:.0f}%")
    print(f"  Neutrales     : {resumen['neutrales_pct']:.0f}%")
    print(f"  Hashtags top  : {[h for h, _ in resumen['hashtags_top']]}")
    print(f"  Mas activos   : {[u for u, _ in resumen['usuarios_activos']]}")


def imprimir_evolucion(evolucion: list[dict]) -> None:
    print("\n--- Evolución del sentimiento ---")
    for item in evolucion:
        tendencia = item["tendencia"]
        barra = "+" * int(max(0, tendencia * 10)) + "-" * int(max(0, -tendencia * 10))
        print(
            f"  Msg {item['posicion']:>2} {item['timestamp']}  "
            f"{item['usuario']:<22}  "
            f"[{item['sentimiento_puntual']:+.2f}]  "
            f"tendencia: {tendencia:+.3f}  |{barra}"
        )


def imprimir_subtemas(subtemas: dict) -> None:
    print("\n--- Subtemas detectados ---")
    for cluster_id, info in subtemas.items():
        kw = ", ".join(info["keywords"]) or "—"
        print(f"  Subtema {int(cluster_id) + 1}  ({info['n_mensajes']} msgs)  [{info['sentimiento_promedio']:+.3f}]")
        print(f"    Palabras clave : {kw}")
        print(f"    Usuarios       : {', '.join(info['usuarios'])}")


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    mensajes, idioma = cargar_hilo(arg)

    print(f"=== AC-4: Análisis de Hilo de Discusión ===\n")
    print(f"Hilo     : {len(mensajes)} mensajes")
    print(f"Idioma   : {idioma}\n")

    analizador = AnalizadorHiloDiscusion(idioma=idioma)
    analizador.cargar_hilo(mensajes)

    imprimir_resumen(analizador.resumen_hilo())
    imprimir_evolucion(analizador.evolucion_sentimiento(ventana=3))
    imprimir_subtemas(analizador.detectar_subtemas(n_clusters=3))

    print("\n--- Usuarios más activos ---")
    for usuario, cantidad in analizador.usuarios_mas_activos(top_n=5):
        print(f"  {usuario:<25} {cantidad} mensaje(s)")

    print("\n--- Hashtags frecuentes ---")
    hashtags = analizador.extraer_hashtags()
    if hashtags:
        for tag, cnt in hashtags:
            print(f"  #{tag:<20} {cnt}")
    else:
        print("  (sin hashtags en este hilo)")

    print("\n--- Resumen textual automático ---")
    print(" ", analizador.generar_resumen_textual())

    analizador.guardar_json(SALIDA_JSON)
    print(f"\nResultados guardados : {SALIDA_JSON}")
    print("Listo. El JSON es compatible con el pipeline SIMANW.")


if __name__ == "__main__":
    main()
