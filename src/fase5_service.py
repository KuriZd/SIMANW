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
        if SistemaQA is not None and motor_busqueda is not None:
            self.qa = SistemaQA(self.corpus, motor_busqueda)
        if ChatbotContextual is not None:
            try:
                self.contextual = ChatbotContextual(self.corpus)
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
        try:
            if self.qa is not None:
                respuesta, tipo, confianza = self.qa.conversar(pregunta)
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
            }
        )
        return respuesta

    def obtener_historial(self) -> list[dict]:
        return list(self.historial)


def _normalizar_doc(doc: dict) -> dict:
    normalizado = dict(doc)
    normalizado["cuerpo"] = doc.get("cuerpo") or doc.get("texto_original") or doc.get("texto_limpio") or ""
    normalizado["categoria_original"] = doc.get("categoria_original") or doc.get("categoria") or "sin_categoria"
    return normalizado
