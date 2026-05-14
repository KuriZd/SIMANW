from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class DetectorTemasPublicidad:
    """Detecta temas en conversaciones y selecciona publicidad relacionada."""

    def __init__(self) -> None:
        self.mensajes: list[dict] = []
        self.catalogo_publicidad = {
            "tecnologia": [
                "Curso de IA y Machine Learning - 50% descuento",
                "Laptop para programadores - i9 + 32GB RAM",
                "Conferencia Tech 2026 - Boletos disponibles",
            ],
            "economia": [
                "App de inversiones - Comienza con $100",
                "Curso de finanzas personales gratuito",
                "Tarjeta de credito sin anualidad",
            ],
            "ciencia": [
                "Suscripcion a revista cientifica digital",
                "Telescopio astronomico - envio gratis",
                "Curso de ciencia de datos online",
            ],
            "politica": [
                "Portal de transparencia gubernamental",
                "Notificaciones de cambios legislativos",
                "Foro de participacion ciudadana",
            ],
        }
        self._construir_perfiles()

    def _construir_perfiles(self) -> None:
        temas_texto = {
            "tecnologia": "inteligencia artificial programacion software apps tecnologia computadora robot digital innovacion machine learning desarrolladores",
            "economia": "dinero inversion mercado bolsa finanzas banco economia empleo trabajo tasas interes fondos",
            "ciencia": "investigacion cientifico descubrimiento estudio laboratorio clima universo datos",
            "politica": "gobierno elecciones presidente ley congreso partido democracia legislativo transparencia",
        }
        self.temas = list(temas_texto.keys())
        self.vec_temas = TfidfVectorizer()
        self.matriz_temas = self.vec_temas.fit_transform(temas_texto.values())

    def agregar_mensaje(self, usuario: str, texto: str) -> None:
        self.mensajes.append({"usuario": usuario, "texto": texto})

    def detectar_tema(self, ventana: int = 5) -> tuple[str, float]:
        if not self.mensajes:
            return "general", 0.0

        ultimos = self.mensajes[-ventana:]
        texto_ventana = " ".join(mensaje["texto"] for mensaje in ultimos)
        vec_conversacion = self.vec_temas.transform([texto_ventana])
        similitudes = cosine_similarity(vec_conversacion, self.matriz_temas)[0]

        mejor_idx = int(similitudes.argmax())
        confianza = float(similitudes[mejor_idx])
        if confianza <= 0:
            return "general", 0.0

        return self.temas[mejor_idx], confianza

    def obtener_publicidad(self, tema: str) -> str:
        if tema in self.catalogo_publicidad:
            return self.catalogo_publicidad[tema][0]
        return "Descubre las mejores ofertas del dia"

    def simular_chat(self, conversacion: list[tuple[str, str]]) -> list[dict]:
        resultados = []

        for usuario, mensaje in conversacion:
            self.agregar_mensaje(usuario, mensaje)
            tema, confianza = self.detectar_tema()
            publicidad = self.obtener_publicidad(tema)
            resultados.append(
                {
                    "usuario": usuario,
                    "mensaje": mensaje,
                    "tema": tema,
                    "confianza": confianza,
                    "publicidad": publicidad,
                }
            )

        return resultados
