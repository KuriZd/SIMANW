from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def normalizar_texto(texto: str) -> str:
    """Elimina acentos y convierte a minusculas para comparacion robusta."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def cargar_noticias_desde_json(ruta: str | Path) -> list[dict]:
    """Carga noticias desde JSON SIMANW. Acepta formatos de AC-1, AC-3 y Fase 1."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if not isinstance(datos, list):
        raise ValueError("El JSON debe contener una lista de noticias")
    noticias: list[dict] = []
    for item in datos:
        titulo = item.get("titulo", "")
        cuerpo = item.get("cuerpo") or item.get("resumen") or ""
        if titulo or cuerpo:
            noticias.append({
                "titulo": titulo,
                "cuerpo": cuerpo,
                "categoria_predicha": item.get("categoria_predicha") or item.get("categoria") or "?",
                "sentimiento": item.get("sentimiento", {}),
                "url": item.get("url", ""),
                "fuente": item.get("fuente", ""),
                "fecha": item.get("fecha", ""),
            })
    if not noticias:
        raise ValueError("No se encontraron noticias validas en el JSON")
    return noticias


class ChatbotContextual:
    """
    AC-6: Chatbot con memoria de contexto.

    Recuerda temas previos de la sesion, detecta referencias contextuales
    y adapta sus respuestas al historial acumulado.
    """

    _TEMAS_PALABRAS: dict[str, list[str]] = {
        "tecnologia": ["tecnologia", "ia", "python", "programacion", "software", "algoritmo", "machine", "learning"],
        "economia": ["economia", "mercado", "mercados", "finanzas", "dinero", "inflacion", "inversion"],
        "ciencia": ["ciencia", "investigacion", "cientifico", "experimento", "laboratorio", "calentamiento"],
        "politica": ["gobierno", "politica", "presidente", "congreso", "reforma"],
        "salud": ["salud", "hospital", "vacuna", "medicina", "tratamiento", "paciente"],
        "medio_ambiente": ["clima", "carbono", "contaminacion", "ambiente", "emisiones", "ambiental"],
    }
    _REFERENCIAS: list[str] = [
        "eso", "esa", "ese", "anterior", "mas sobre", "otra", "similar",
        "continua", "explicame", "dame mas", "lo mismo",
    ]

    def __init__(self, noticias: list[dict], motor_busqueda) -> None:
        self.noticias = noticias
        self.motor = motor_busqueda
        self.historial: list[dict] = []
        self.contexto_temas: Counter = Counter()
        self.usuario_preferencias: dict = {}
        self.ultimo_resultado: dict | None = None
        self.ultima_consulta_expandida: str = ""

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def actualizar_contexto(
        self, pregunta: str, respuesta_tipo: str, resultados: list[dict] | None = None
    ) -> None:
        """Guarda la interaccion en el historial y actualiza temas detectados."""
        self.historial.append({
            "pregunta": pregunta,
            "tipo": respuesta_tipo,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        for tema in self._temas_en_pregunta(pregunta):
            self.contexto_temas[tema] += 1
        if resultados:
            self.ultimo_resultado = resultados[0]

    def detectar_referencia_contextual(self, pregunta: str) -> bool:
        """Devuelve True si la pregunta depende del contexto anterior."""
        return self._es_referencia_contextual(normalizar_texto(pregunta))

    def expandir_consulta(self, pregunta: str) -> str:
        """Construye una consulta enriquecida combinando historial y ultimo resultado."""
        if not self.historial:
            return pregunta
        partes = [self.historial[-1]["pregunta"]]
        if self.ultimo_resultado:
            titulo_prev = self.ultimo_resultado.get("titulo", "")
            if titulo_prev:
                partes.append(titulo_prev)
        partes.append(pregunta)
        return " ".join(p for p in partes if p)

    def responder(self, pregunta: str) -> tuple[str, str, float]:
        """
        Genera una respuesta considerando el contexto acumulado.

        Devuelve (respuesta, tipo, confianza).
        Tipos posibles: directa, contextual, personalizada, fallback.
        """
        if not pregunta or not pregunta.strip():
            return "No entendi la pregunta. Por favor escribe algo.", "fallback", 0.0

        pregunta_normalizada = normalizar_texto(pregunta)

        if self._es_referencia_contextual(pregunta_normalizada) and self.historial:
            consulta_expandida = self.expandir_consulta(pregunta)
            self.ultima_consulta_expandida = consulta_expandida
            resultados = self._buscar(consulta_expandida)
            if resultados:
                tipo = "contextual"
                respuesta = (
                    f"Basandome en nuestra conversacion anterior, encontre: "
                    f"{resultados[0]['titulo']}. {resultados[0].get('snippet', '')}"
                )
                self.actualizar_contexto(pregunta, tipo, resultados)
                return respuesta, tipo, float(resultados[0]["relevancia"])

        resultados = self._buscar(pregunta)
        if resultados:
            temas_pregunta = self._temas_en_pregunta(pregunta)
            tema_prioritario = temas_pregunta[0] if temas_pregunta else None
            if tema_prioritario is None and self.contexto_temas:
                tema_prioritario = self.contexto_temas.most_common(1)[0][0]

            if tema_prioritario:
                for resultado in resultados:
                    if resultado.get("categoria") == tema_prioritario:
                        tipo = "personalizada"
                        respuesta = (
                            f"Como te interesa {tema_prioritario}, mira esto: "
                            f"{resultado['titulo']}. {resultado.get('snippet', '')}"
                        )
                        self.actualizar_contexto(pregunta, tipo, [resultado])
                        return respuesta, tipo, float(resultado["relevancia"])

            tipo = "directa"
            respuesta = f"{resultados[0]['titulo']}. {resultados[0].get('snippet', '')}"
            self.actualizar_contexto(pregunta, tipo, resultados)
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
            "ultima_consulta_expandida": self.ultima_consulta_expandida,
            "tiene_contexto": len(self.historial) > 0,
        }

    def guardar_sesion(self, ruta: str | Path) -> None:
        """Exporta historial y estadisticas a JSON compatible con pipeline SIMANW."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        stats = self.estadisticas_sesion()
        payload = {
            "actividad": "AC-6",
            "descripcion": "Chatbot con memoria de contexto",
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "historial": self.historial,
            "estadisticas": {
                "interacciones": stats["interacciones"],
                "ultima_consulta_expandida": stats["ultima_consulta_expandida"],
                "tiene_contexto": stats["tiene_contexto"],
            },
            "temas_interes": stats["temas_interes"],
            "tipos_respuesta": dict(stats["tipos_respuesta"]),
            "preferencias_usuario": self.usuario_preferencias,
        }
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(payload, archivo, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Metodos internos
    # ------------------------------------------------------------------

    def _buscar(self, consulta: str) -> list[dict]:
        """Adaptador para motores con buscar_vectorial o buscar."""
        if not consulta or not consulta.strip():
            return []
        if hasattr(self.motor, "buscar_vectorial"):
            return self.motor.buscar_vectorial(consulta, top_k=5)
        if hasattr(self.motor, "buscar"):
            return self.motor.buscar(consulta, top_k=5)
        return []

    def _temas_en_pregunta(self, pregunta: str) -> list[str]:
        normalizada = normalizar_texto(pregunta)
        palabras = set(re.findall(r"\b\w+\b", normalizada))
        temas_detectados: list[str] = []
        for tema, claves in self._TEMAS_PALABRAS.items():
            for clave in claves:
                if " " in clave:
                    if clave in normalizada:
                        temas_detectados.append(tema)
                        break
                elif clave in palabras:
                    temas_detectados.append(tema)
                    break
        return temas_detectados

    @classmethod
    def _es_referencia_contextual(cls, pregunta_normalizada: str) -> bool:
        return any(ref in pregunta_normalizada for ref in cls._REFERENCIAS)

    @staticmethod
    def _normalizar(texto: str) -> str:
        return normalizar_texto(texto)


CONVERSACION_AC6 = [
    "Que noticias hay de tecnologia?",
    "Cuentame mas sobre eso",
    "Hay algo sobre inteligencia artificial?",
    "Y algo de economia?",
    "Dame otra noticia similar a la anterior",
]
