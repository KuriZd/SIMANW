from __future__ import annotations

import re
import unicodedata
from collections import Counter


class ChatbotContextual:
    """
    AC-6: Chatbot con memoria de contexto.
    """

    def __init__(self, noticias: list[dict], motor_busqueda) -> None:
        self.noticias = noticias
        self.motor = motor_busqueda
        self.historial: list[dict] = []
        self.contexto_temas: Counter = Counter()
        self.usuario_preferencias: dict = {}

    def actualizar_contexto(self, pregunta: str, respuesta_tipo: str) -> None:
        """Actualiza el contexto basandose en la interaccion."""
        self.historial.append({"pregunta": pregunta, "tipo": respuesta_tipo})
        for tema in self._temas_en_pregunta(pregunta):
            self.contexto_temas[tema] += 1

    def _temas_en_pregunta(self, pregunta: str) -> list[str]:
        pregunta_normalizada = self._normalizar(pregunta)

        temas = {
            "tecnologia": ["tecnologia", "ia", "python", "programacion", "software", "machine", "learning"],
            "economia": ["economia", "mercado", "mercados", "finanzas", "dinero", "inflacion"],
            "ciencia": ["ciencia", "clima", "investigacion", "cientifico", "calentamiento"],
            "politica": ["gobierno", "politica", "datos", "publica", "reforma"],
        }

        palabras = re.findall(r"\b\w+\b", pregunta_normalizada)
        return [tema for tema, claves in temas.items() if any(clave in palabras for clave in claves)]

    def responder(self, pregunta: str) -> tuple[str, str, float]:
        """Genera respuesta considerando el contexto previo."""
        pregunta_normalizada = self._normalizar(pregunta)

        if self._es_referencia_contextual(pregunta_normalizada) and self.historial:
            ultimo = self.historial[-1]
            pregunta_expandida = f"{ultimo['pregunta']} {pregunta}"
            resultados = self.motor.buscar_vectorial(pregunta_expandida, top_k=2)
            if resultados:
                tipo = "contextual"
                respuesta = f"Basandome en nuestra conversacion anterior, encontre: {resultados[0]['titulo']}"
                self.actualizar_contexto(pregunta, tipo)
                return respuesta, tipo, float(resultados[0]["relevancia"])

        resultados = self.motor.buscar_vectorial(pregunta, top_k=5)
        if resultados:
            temas_pregunta = self._temas_en_pregunta(pregunta)
            tema_prioritario = temas_pregunta[0] if temas_pregunta else None
            if tema_prioritario is None and self.contexto_temas:
                tema_prioritario = self.contexto_temas.most_common(1)[0][0]

            if tema_prioritario:
                for resultado in resultados:
                    if resultado["categoria"] == tema_prioritario:
                        tipo = "personalizada"
                        respuesta = f"Como te interesa {tema_prioritario}, mira esto: {resultado['titulo']}"
                        self.actualizar_contexto(pregunta, tipo)
                        return respuesta, tipo, float(resultado["relevancia"])

            tipo = "directa"
            respuesta = f"{resultados[0]['titulo']}. {resultados[0]['snippet']}"
            self.actualizar_contexto(pregunta, tipo)
            return respuesta, tipo, float(resultados[0]["relevancia"])

        tipo = "fallback"
        respuesta = "No encontre algo especifico. Puedes darme mas detalles?"
        self.actualizar_contexto(pregunta, tipo)
        return respuesta, tipo, 0.0

    def estadisticas_sesion(self) -> dict:
        return {
            "interacciones": len(self.historial),
            "temas_interes": dict(self.contexto_temas.most_common()),
            "tipos_respuesta": Counter(item["tipo"] for item in self.historial),
        }

    @staticmethod
    def _es_referencia_contextual(pregunta_normalizada: str) -> bool:
        referencias = ["eso", "esa", "anterior", "mas sobre", "otra", "similar"]
        return any(referencia in pregunta_normalizada for referencia in referencias)

    @staticmethod
    def _normalizar(texto: str) -> str:
        texto = texto.lower()
        texto = unicodedata.normalize("NFKD", texto)
        return "".join(caracter for caracter in texto if not unicodedata.combining(caracter))


CONVERSACION_AC6 = [
    "Que noticias hay de tecnologia?",
    "Cuentame mas sobre eso",
    "Hay algo sobre inteligencia artificial?",
    "Y algo de economia?",
    "Dame otra noticia similar a la anterior",
]
