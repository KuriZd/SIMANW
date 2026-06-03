"""AC-6: Interfaz conversacional con memoria de contexto.

Uso:
    python main_ac6.py                        # corpus demo integrado
    python main_ac6.py data/noticias_ac1.json # corpus desde JSON de Fase 1 o AC-1
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.chatbot_contextual import (
    CONVERSACION_AC6,
    ChatbotContextual,
    cargar_noticias_desde_json,
)
from src.motor_busqueda import MotorBusqueda

SALIDA_JSON = Path("data") / "sesion_chatbot_ac6.json"

NOTICIAS_DEMO = [
    {
        "titulo": "Avances en inteligencia artificial generativa",
        "cuerpo": "La inteligencia artificial y el aprendizaje automatico impulsan nuevas aplicaciones de software y transforman la industria tecnologica.",
        "categoria_predicha": "tecnologia",
        "sentimiento": {"etiqueta": "positivo"},
        "url": "",
    },
    {
        "titulo": "Mercados financieros muestran volatilidad",
        "cuerpo": "La inflacion y las tasas de interes presionan al mercado de valores y a los inversionistas globales.",
        "categoria_predicha": "economia",
        "sentimiento": {"etiqueta": "negativo"},
        "url": "",
    },
    {
        "titulo": "Descubrimiento cientifico sobre cambio climatico",
        "cuerpo": "Investigadores publican nuevos datos sobre emisiones de carbono y calentamiento global en el Artico.",
        "categoria_predicha": "ciencia",
        "sentimiento": {"etiqueta": "negativo"},
        "url": "",
    },
    {
        "titulo": "Python mejora herramientas de programacion",
        "cuerpo": "La nueva version de Python ayuda al desarrollo de software e inteligencia artificial con mejor rendimiento.",
        "categoria_predicha": "tecnologia",
        "sentimiento": {"etiqueta": "positivo"},
        "url": "",
    },
    {
        "titulo": "Gobierno publica datos abiertos para transparencia",
        "cuerpo": "El gobierno federal libera datos abiertos para fortalecer la transparencia y las politicas publicas ciudadanas.",
        "categoria_predicha": "politica",
        "sentimiento": {"etiqueta": "positivo"},
        "url": "",
    },
    {
        "titulo": "Vacuna contra influenza alcanza alta efectividad",
        "cuerpo": "Ensayos clinicos confirman 92% de efectividad de la nueva vacuna en adultos mayores y pacientes de riesgo.",
        "categoria_predicha": "salud",
        "sentimiento": {"etiqueta": "positivo"},
        "url": "",
    },
    {
        "titulo": "Energias renovables reducen contaminacion ambiental",
        "cuerpo": "Paneles solares y turbinas eolicas disminuyen emisiones de carbono y mejoran la calidad del ambiente.",
        "categoria_predicha": "medio_ambiente",
        "sentimiento": {"etiqueta": "positivo"},
        "url": "",
    },
    {
        "titulo": "Reforma educativa aprobada en el Congreso",
        "cuerpo": "El Congreso aprobo una reforma al sistema educativo con nuevos programas para escuelas publicas.",
        "categoria_predicha": "politica",
        "sentimiento": {"etiqueta": "neutral"},
        "url": "",
    },
]

CONVERSACION_EXTENDIDA = [
    "Que noticias hay de tecnologia?",
    "Cuentame mas sobre eso",
    "Hay algo sobre inteligencia artificial?",
    "Y algo de economia?",
    "Dame otra noticia similar a la anterior",
]


def cargar_corpus(arg: str | None) -> tuple[list[dict], str]:
    if arg is None:
        return NOTICIAS_DEMO, "corpus demo integrado"
    ruta = Path(arg)
    if not ruta.exists():
        print(f"Archivo no encontrado: {ruta}. Usando corpus demo.")
        return NOTICIAS_DEMO, "corpus demo integrado"
    try:
        noticias = cargar_noticias_desde_json(ruta)
        return noticias, str(ruta)
    except Exception as exc:
        print(f"Error al cargar JSON: {exc}. Usando corpus demo.")
        return NOTICIAS_DEMO, "corpus demo integrado"


def imprimir_estadisticas(stats: dict) -> None:
    print("\n--- Estadisticas de sesion ---")
    print(f"  Interacciones          : {stats['interacciones']}")
    print(f"  Tiene contexto         : {stats['tiene_contexto']}")
    if stats["ultima_consulta_expandida"]:
        print(f"  Ultima consulta expand.: {stats['ultima_consulta_expandida'][:70]}")
    temas = stats.get("temas_interes", {})
    if temas:
        print(f"  Temas de interes       : {dict(list(temas.items())[:5])}")
    tipos = dict(stats.get("tipos_respuesta", {}))
    if tipos:
        print(f"  Tipos de respuesta     : {tipos}")


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    noticias, origen = cargar_corpus(arg)

    print("=== AC-6: Chatbot con Memoria de Contexto ===\n")
    print(f"Corpus   : {origen}")
    print(f"Noticias : {len(noticias)}\n")

    motor = MotorBusqueda()
    motor.indexar(noticias)

    chatbot = ChatbotContextual(noticias, motor)

    print("--- Conversacion de prueba ---\n")
    for pregunta in CONVERSACION_EXTENDIDA:
        respuesta, tipo, confianza = chatbot.responder(pregunta)
        print(f"Usuario : {pregunta}")
        print(f"Bot [{tipo}][{confianza:.2f}]: {respuesta[:120]}")
        print()

    imprimir_estadisticas(chatbot.estadisticas_sesion())

    print("\n--- Verificacion de metodos AC-6 ---")
    ref_test = "Dame mas detalles sobre eso"
    detecta = chatbot.detectar_referencia_contextual(ref_test)
    expandida = chatbot.expandir_consulta(ref_test)
    print(f"  detectar_referencia_contextual('{ref_test}'): {detecta}")
    print(f"  expandir_consulta:  {expandida[:80]}")

    chatbot.guardar_sesion(SALIDA_JSON)
    print(f"\nSesion guardada : {SALIDA_JSON}")
    print("Listo. El JSON es compatible con el pipeline SIMANW.")


if __name__ == "__main__":
    main()
