"""AC-11: Estudio de usabilidad del buscador y chatbot."""
from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean
from typing import Any


TAREAS_USABILIDAD = [
    "Buscar noticias sobre inteligencia artificial con busqueda directa.",
    "Usar lenguaje natural para encontrar noticias economicas recientes.",
    "Preguntar cuantas noticias hay sobre ciencia.",
    "Pedir una recomendacion de lectura sobre tecnologia.",
    "Hacer una pregunta de seguimiento usando el contexto de la respuesta anterior.",
]

CUESTIONARIO_USABILIDAD = [
    "Facilidad para completar las tareas",
    "Relevancia de los resultados",
    "Confianza en las respuestas",
    "Claridad del lenguaje del chatbot",
    "Rapidez percibida",
    "Facilidad para reformular consultas",
    "Utilidad de las recomendaciones",
    "Satisfaccion general",
]


class EstudioUsabilidad:
    """Agrega resultados anonimizados de una prueba con usuarios."""

    def __init__(self, tareas: list[str] | None = None, items: list[str] | None = None) -> None:
        self.tareas = tareas or TAREAS_USABILIDAD
        self.items = items or CUESTIONARIO_USABILIDAD
        self.participantes: list[dict[str, Any]] = []

    def registrar_participante(
        self,
        codigo: str,
        respuestas: dict[str, int],
        problemas: list[str],
    ) -> None:
        if len(respuestas) < len(self.items):
            raise ValueError("El cuestionario debe incluir todos los items definidos.")
        self.participantes.append(
            {"participante": codigo, "respuestas": respuestas, "problemas": problemas}
        )

    def promedios(self) -> dict[str, float]:
        return {
            item: round(mean(p["respuestas"][item] for p in self.participantes), 2)
            for item in self.items
        }

    def tabla_anonimizada(self) -> list[dict[str, Any]]:
        filas: list[dict[str, Any]] = []
        for participante in self.participantes:
            fila = {"participante": participante["participante"]}
            fila.update(participante["respuestas"])
            filas.append(fila)
        return filas

    def exportar_csv(self, ruta: str | Path) -> Path:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        campos = ["participante", *self.items]
        with ruta.open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=campos)
            writer.writeheader()
            writer.writerows(self.tabla_anonimizada())
        return ruta

    def problemas_y_mejoras(self) -> list[dict[str, str]]:
        problemas = [
            "Los usuarios no distinguen claramente busqueda directa y busqueda natural.",
            "Algunos resultados relevantes aparecen debajo de documentos menos utiles.",
            "El chatbot no siempre explica la fuente de una respuesta de conteo.",
            "Las recomendaciones no muestran por que una noticia fue sugerida.",
            "Las preguntas de seguimiento pierden contexto cuando cambia el tema.",
        ]
        mejoras = [
            "Etiquetar visualmente el modo activo y conservar ejemplos breves por modo.",
            "Reordenar resultados combinando similitud vectorial, fecha y coincidencia exacta.",
            "Mostrar el conteo, el filtro aplicado y enlaces a las noticias consideradas.",
            "Agregar una justificacion basada en categoria, terminos coincidentes y sentimiento.",
            "Guardar un resumen de contexto por sesion y pedir confirmacion ante cambios ambiguos.",
        ]
        return [{"problema": p, "mejora": m} for p, m in zip(problemas, mejoras)]

    def reflexion_consentimiento(self) -> str:
        return (
            "La prueba debe iniciar con consentimiento informado: se explica el objetivo academico, "
            "las tareas, el tiempo estimado y que la participacion es voluntaria. No se registran "
            "nombres reales; cada persona se identifica con un codigo anonimo. Las respuestas se "
            "usan solo para evaluar el SIMANW y se reportan de forma agregada, evitando publicar "
            "consultas personales o datos que permitan identificar a participantes."
        )


def estudio_demo() -> EstudioUsabilidad:
    estudio = EstudioUsabilidad()
    base = [
        ("P1", [4, 4, 3, 4, 5, 3, 4, 4], ["No encontro filtros visibles."]),
        ("P2", [3, 4, 4, 3, 4, 3, 3, 4], ["Dudo de la fuente del conteo."]),
        ("P3", [4, 3, 3, 4, 4, 4, 3, 3], ["La recomendacion parecia poco explicada."]),
    ]
    for codigo, valores, problemas in base:
        estudio.registrar_participante(codigo, dict(zip(estudio.items, valores)), problemas)
    return estudio
