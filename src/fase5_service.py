from __future__ import annotations

try:
    from src.chatbot_qa import SistemaQA
except ImportError:  # pragma: no cover
    SistemaQA = None  # type: ignore[assignment]

try:
    from src.chatbot_contextual import ChatbotContextual
except ImportError:  # pragma: no cover
    ChatbotContextual = None  # type: ignore[assignment]


class Fase5Service:
    """Capa conversacional y Q&A basada en el corpus cargado."""

    def __init__(self) -> None:
        self.corpus: list[dict] = []
        self.motor_busqueda = None
        self.qa = None
        self.contextual = None
        self.historial: list[dict] = []

    def preparar(self, corpus_procesado: list[dict], motor_busqueda=None) -> None:
        if not corpus_procesado:
            raise ValueError("No hay corpus para preparar Q&A.")
        self.corpus = [_normalizar_doc(doc) for doc in corpus_procesado]
        self.motor_busqueda = motor_busqueda
        self.historial = []
        if SistemaQA is not None and motor_busqueda is not None:
            self.qa = SistemaQA(self.corpus, motor_busqueda)
        if ChatbotContextual is not None and motor_busqueda is not None:
            try:
                self.contextual = ChatbotContextual(self.corpus, motor_busqueda)
            except Exception:
                self.contextual = None

    def responder(self, pregunta: str) -> str:
        pregunta = pregunta.strip()
        if not pregunta:
            return "Escribe una pregunta sobre el corpus cargado."
        if not self.corpus:
            return "No tengo informacion cargada para responder."

        respuesta = "No tengo informacion suficiente para responder con el corpus cargado."
        tipo = "sin_informacion"
        confianza = 0.0
        consulta_expandida = ""
        try:
            if self.contextual is not None and self.contextual.detectar_referencia_contextual(pregunta):
                respuesta, tipo, confianza = self.contextual.responder(pregunta)
                consulta_expandida = self.contextual.ultima_consulta_expandida
            elif self.qa is not None and self.qa.clasificar_intencion(pregunta) in {
                "conteo",
                "resumen",
                "sentimiento",
                "categoria",
            }:
                respuesta, tipo, confianza = self.qa.conversar(pregunta)
                if self.contextual is not None:
                    self.contextual.actualizar_contexto(pregunta, tipo)
            elif self.contextual is not None:
                respuesta, tipo, confianza = self.contextual.responder(pregunta)
                consulta_expandida = self.contextual.ultima_consulta_expandida
            elif self.motor_busqueda is not None:
                resultados = self.motor_busqueda.buscar_vectorial(pregunta, top_k=1)
                if resultados:
                    mejor = resultados[0]
                    respuesta = f"{mejor['titulo']}. {mejor.get('snippet', '')}"
                    tipo = "busqueda"
                    confianza = float(mejor.get("score", mejor.get("relevancia", 0.0)))
        except Exception as exc:
            respuesta = f"No pude responder con suficiente certeza: {exc}"
            tipo = "error"

        self.historial.append(
            {
                "pregunta": pregunta,
                "respuesta": respuesta,
                "tipo": tipo,
                "confianza": confianza,
                "consulta_expandida": consulta_expandida,
                "usa_contexto": tipo in {"contextual", "personalizada"} or bool(consulta_expandida),
            }
        )
        return respuesta

    def obtener_historial(self) -> list[dict]:
        return list(self.historial)

    def estadisticas_contexto(self) -> dict:
        if self.contextual is None:
            return {
                "interacciones": len(self.historial),
                "temas_interes": {},
                "tipos_respuesta": {},
                "ultima_consulta_expandida": "",
                "tiene_contexto": False,
            }
        stats = self.contextual.estadisticas_sesion()
        return {
            "interacciones": stats["interacciones"],
            "temas_interes": stats["temas_interes"],
            "tipos_respuesta": dict(stats["tipos_respuesta"]),
            "ultima_consulta_expandida": stats["ultima_consulta_expandida"],
            "tiene_contexto": stats["tiene_contexto"],
        }


def _normalizar_doc(doc: dict) -> dict:
    normalizado = dict(doc)
    normalizado["cuerpo"] = doc.get("cuerpo") or doc.get("texto_original") or doc.get("texto_limpio") or ""
    normalizado["categoria_original"] = doc.get("categoria_original") or doc.get("categoria") or "sin_categoria"
    return normalizado
