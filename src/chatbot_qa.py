from __future__ import annotations

import unicodedata
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


STOPWORDS_PREGUNTAS_ES = {
    "a",
    "al",
    "algo",
    "cual",
    "cuando",
    "cuanto",
    "cuantos",
    "de",
    "del",
    "dice",
    "el",
    "en",
    "es",
    "esa",
    "ese",
    "hay",
    "la",
    "las",
    "lo",
    "los",
    "me",
    "noticia",
    "noticias",
    "que",
    "sobre",
    "un",
    "una",
}


class ChatbotSIMANW:
    """
    Chatbot del SIMANW que responde preguntas sobre noticias procesadas
    usando similitud TF-IDF.
    """

    def __init__(self, noticias: list[dict]) -> None:
        if not noticias:
            raise ValueError("Se necesita al menos una noticia para construir el chatbot")

        self.noticias = noticias
        self.historial: list[dict] = []
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=2000,
            strip_accents="unicode",
            lowercase=True,
            stop_words=list(STOPWORDS_PREGUNTAS_ES),
        )
        self._construir_base()

    def _construir_base(self) -> None:
        """Construye la base de conocimiento a partir de las noticias."""
        self.pares_qa: list[dict] = []

        for noticia in self.noticias:
            titulo = noticia["titulo"]
            cuerpo = noticia["cuerpo"]
            categoria = noticia.get("categoria_predicha", noticia.get("categoria_original", "sin categoria"))
            sentimiento = noticia.get("sentimiento", {}).get("etiqueta", "sin sentimiento")

            self.pares_qa.append(
                {
                    "contexto": f"{titulo} {cuerpo}",
                    "respuesta": f"{titulo}. {cuerpo}",
                    "tipo": "contenido",
                }
            )
            self.pares_qa.append(
                {
                    "contexto": f"categoria tema tipo {categoria} {titulo}",
                    "respuesta": f"Esa noticia pertenece a la categoria '{categoria}': {titulo}",
                    "tipo": "categoria",
                }
            )
            self.pares_qa.append(
                {
                    "contexto": f"sentimiento opinion tono {sentimiento} {titulo}",
                    "respuesta": f"El tono de esa noticia es {sentimiento}: {titulo}",
                    "tipo": "sentimiento",
                }
            )

        contextos = [par["contexto"] for par in self.pares_qa]
        self.matriz_qa = self.vectorizer.fit_transform(contextos)

    def responder(self, pregunta: str, umbral: float = 0.05) -> tuple[str, float]:
        """Genera respuesta a una pregunta del usuario."""
        pregunta_vec = self.vectorizer.transform([pregunta])
        similitudes = cosine_similarity(pregunta_vec, self.matriz_qa)[0]
        mejor_idx = int(similitudes.argmax())
        confianza = float(similitudes[mejor_idx])

        self.historial.append({"pregunta": pregunta, "confianza": confianza})

        if confianza < umbral:
            return "No tengo informacion suficiente para responder eso. Puedes reformular tu pregunta?", 0.0

        return self.pares_qa[mejor_idx]["respuesta"], confianza

    def resumen_interaccion(self) -> str:
        total = len(self.historial)
        if total == 0:
            return "Sin interacciones"

        promedio = sum(item["confianza"] for item in self.historial) / total
        return f"{total} preguntas, confianza promedio: {promedio:.3f}"


class SistemaQA:
    """
    Sistema de pregunta-respuesta que comprende la intencion del usuario
    y genera respuestas a partir de la informacion indexada.
    """

    def __init__(self, noticias: list[dict], motor_busqueda) -> None:
        if not noticias:
            raise ValueError("Se necesita al menos una noticia para construir el sistema Q&A")

        self.noticias = noticias
        self.motor = motor_busqueda
        self.historial_conversacion: list[dict] = []

    def clasificar_intencion(self, pregunta: str) -> str:
        """Determina que tipo de informacion busca el usuario."""
        pregunta_lower = self._normalizar(pregunta)

        if any(palabra in pregunta_lower for palabra in ["cuantas", "cuantos", "total", "numero"]):
            return "conteo"
        if any(palabra in pregunta_lower for palabra in ["resumen", "resume", "sintetiza"]):
            return "resumen"
        if any(palabra in pregunta_lower for palabra in ["sentimiento", "tono", "opinion", "positiv", "negativ"]):
            return "sentimiento"
        if any(palabra in pregunta_lower for palabra in ["categoria", "tema", "tipo", "clasifica"]):
            return "categoria"
        if any(palabra in pregunta_lower for palabra in ["compara", "diferencia", "relacion"]):
            return "comparacion"
        if any(palabra in pregunta_lower for palabra in ["recomienda", "sugiere", "similar"]):
            return "recomendacion"

        return "busqueda"

    def generar_respuesta(self, pregunta: str) -> tuple[str, str, float]:
        """Genera una respuesta segun la intencion detectada."""
        intencion = self.clasificar_intencion(pregunta)

        if intencion == "conteo":
            return self._respuesta_conteo()
        if intencion == "sentimiento":
            return self._respuesta_sentimiento()
        if intencion == "categoria":
            return self._respuesta_categoria()
        if intencion == "resumen":
            return self._respuesta_resumen()
        if intencion == "recomendacion":
            return self._respuesta_recomendacion(pregunta)
        if intencion == "comparacion":
            return self._respuesta_comparacion(pregunta)

        return self._respuesta_busqueda(pregunta)

    def _respuesta_conteo(self) -> tuple[str, str, float]:
        categorias = Counter(self._categoria(noticia) for noticia in self.noticias)
        distribucion = ", ".join(f"{categoria}: {total}" for categoria, total in categorias.most_common())
        respuesta = f"Tengo {len(self.noticias)} noticias indexadas. Distribucion: {distribucion}"
        return respuesta, "conteo", 1.0

    def _respuesta_sentimiento(self) -> tuple[str, str, float]:
        noticias_con_sentimiento = [noticia for noticia in self.noticias if "sentimiento" in noticia]
        if not noticias_con_sentimiento:
            return "Las noticias todavia no tienen analisis de sentimiento.", "sentimiento", 0.0

        sentimientos = Counter(noticia["sentimiento"]["etiqueta"] for noticia in noticias_con_sentimiento)
        promedio = sum(noticia["sentimiento"]["compound"] for noticia in noticias_con_sentimiento) / len(
            noticias_con_sentimiento
        )

        if promedio > 0.05:
            tono = "positivo"
        elif promedio < -0.05:
            tono = "negativo"
        else:
            tono = "neutral"

        respuesta = f"Analisis de sentimiento: {dict(sentimientos)}. El tono general es {tono} (promedio: {promedio:+.3f})."
        return respuesta, "sentimiento", 0.9

    def _respuesta_categoria(self) -> tuple[str, str, float]:
        categorias = Counter(self._categoria(noticia) for noticia in self.noticias)
        lineas = ["Categorias detectadas en las noticias:"]

        for categoria, total in categorias.most_common():
            ejemplo = next(noticia["titulo"] for noticia in self.noticias if self._categoria(noticia) == categoria)
            lineas.append(f"  - {categoria} ({total}): {ejemplo[:40]}...")

        return "\n".join(lineas), "categoria", 0.9

    def _respuesta_resumen(self) -> tuple[str, str, float]:
        lineas = [f"Resumen del corpus ({len(self.noticias)} noticias):"]

        for noticia in self.noticias:
            sentimiento = noticia.get("sentimiento", {}).get("etiqueta", "?")
            categoria = self._categoria(noticia)
            lineas.append(f"  - [{categoria}][{sentimiento}] {noticia['titulo'][:50]}")

        return "\n".join(lineas), "resumen", 1.0

    def _respuesta_recomendacion(self, pregunta: str) -> tuple[str, str, float]:
        resultados = self.motor.buscar_vectorial(pregunta, top_k=3)
        if not resultados:
            return "No encontre noticias para recomendar sobre ese tema.", "recomendacion", 0.0

        lineas = ["Te recomiendo estas noticias relacionadas:"]
        for resultado in resultados:
            lineas.append(f"  - [{resultado['relevancia']:.2f}] {resultado['titulo'][:50]}...")

        return "\n".join(lineas), "recomendacion", float(resultados[0]["relevancia"])

    def _respuesta_comparacion(self, pregunta: str) -> tuple[str, str, float]:
        resultados = self.motor.buscar_vectorial(pregunta, top_k=2)
        if len(resultados) < 2:
            return "Necesito al menos dos noticias relacionadas para comparar.", "comparacion", 0.0

        respuesta = (
            "Las noticias mas relacionadas para comparar son: "
            f"'{resultados[0]['titulo']}' y '{resultados[1]['titulo']}'."
        )
        return respuesta, "comparacion", float(resultados[0]["relevancia"])

    def _respuesta_busqueda(self, pregunta: str) -> tuple[str, str, float]:
        resultados = self.motor.buscar_vectorial(pregunta, top_k=2)
        if not resultados:
            return "No encontre informacion relevante para tu pregunta.", "busqueda", 0.0

        mejor = resultados[0]
        respuesta = f"{mejor['titulo']}.\n{mejor['snippet']}"
        return respuesta, "busqueda", float(mejor["relevancia"])

    def conversar(self, pregunta: str) -> tuple[str, str, float]:
        """Interfaz conversacional con historial."""
        respuesta, tipo, confianza = self.generar_respuesta(pregunta)
        self.historial_conversacion.append(
            {
                "pregunta": pregunta,
                "tipo": tipo,
                "confianza": confianza,
            }
        )
        return respuesta, tipo, confianza

    @staticmethod
    def _categoria(noticia: dict) -> str:
        return noticia.get("categoria_predicha", noticia.get("categoria_original", "sin categoria"))

    @staticmethod
    def _normalizar(texto: str) -> str:
        texto = texto.lower()
        texto = unicodedata.normalize("NFKD", texto)
        return "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
