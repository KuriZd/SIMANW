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
        "tecnologia": [
            "tecnologia", "ia", "inteligencia", "artificial", "python", "programacion",
            "software", "algoritmo", "machine", "learning", "datos", "digital",
            "computacion", "red", "internet", "app", "sistema", "automatico",
        ],
        "economia": [
            "economia", "mercado", "mercados", "finanzas", "dinero", "inflacion",
            "inversion", "bolsa", "precio", "banco", "credito", "deuda",
        ],
        "ciencia": [
            "ciencia", "investigacion", "cientifico", "experimento", "laboratorio",
            "calentamiento", "estudio", "descubrimiento", "fisico", "quimico",
        ],
        "politica": [
            "gobierno", "politica", "presidente", "congreso", "reforma", "ley",
            "ministro", "eleccion", "voto", "partido", "diputado", "senado",
        ],
        "salud": [
            "salud", "hospital", "vacuna", "medicina", "tratamiento", "paciente",
            "enfermedad", "medico", "virus", "pandemia", "clinica",
        ],
        "medio_ambiente": [
            "clima", "carbono", "contaminacion", "ambiente", "emisiones", "ambiental",
            "naturaleza", "ecosistema", "biodiversidad", "reciclaje",
        ],
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

    # ------------------------------------------------------------------
    # Deteccion de intencion
    # ------------------------------------------------------------------

    _INTENCIONES: dict[str, list[str]] = {
        "conteo": ["cuantas", "cuantos", "total", "numero", "cantidad", "cuantos hay"],
        "sentimiento": ["sentimiento", "tono", "opinion", "positiv", "negativ", "emocion"],
        "categoria": ["categoria", "tema", "tipo", "clasifica", "categorias", "temas"],
        "resumen": ["resumen", "resume", "sintetiza", "sintesis", "panorama"],
    }

    def _clasificar_intencion(self, pregunta: str) -> str:
        normalizada = normalizar_texto(pregunta)
        for intencion, claves in self._INTENCIONES.items():
            if any(clave in normalizada for clave in claves):
                return intencion
        return "busqueda"

    def _respuesta_conteo(self) -> tuple[str, str, float]:
        from collections import Counter as _Counter
        categorias = _Counter(
            n.get("categoria_predicha", n.get("categoria_original", "sin categoria"))
            for n in self.noticias
        )
        distribucion = ", ".join(f"{cat}: {tot}" for cat, tot in categorias.most_common())
        return (
            f"Tengo {len(self.noticias)} noticias indexadas. Distribucion: {distribucion}",
            "conteo",
            1.0,
        )

    def _respuesta_sentimiento(self) -> tuple[str, str, float]:
        from collections import Counter as _Counter
        con_sentimiento = [n for n in self.noticias if "sentimiento" in n and "compound" in n["sentimiento"]]
        if not con_sentimiento:
            return "Las noticias aun no tienen analisis de sentimiento.", "sentimiento", 0.0
        promedio = sum(n["sentimiento"]["compound"] for n in con_sentimiento) / len(con_sentimiento)
        etiquetas = _Counter(n["sentimiento"].get("etiqueta", "?") for n in con_sentimiento)
        tono = "positivo" if promedio > 0.05 else ("negativo" if promedio < -0.05 else "neutral")
        return (
            f"Analisis de sentimiento: {dict(etiquetas)}. Tono general: {tono} (promedio: {promedio:+.3f}).",
            "sentimiento",
            0.9,
        )

    def _respuesta_categoria(self) -> tuple[str, str, float]:
        from collections import Counter as _Counter
        categorias = _Counter(
            n.get("categoria_predicha", n.get("categoria_original", "sin categoria"))
            for n in self.noticias
        )
        lineas = ["Categorias en el corpus:"]
        for cat, total in categorias.most_common():
            ejemplo = next(
                n["titulo"] for n in self.noticias
                if n.get("categoria_predicha", n.get("categoria_original")) == cat
            )
            lineas.append(f"  - {cat} ({total}): {ejemplo}")
        return "\n".join(lineas), "categoria", 0.9

    def _respuesta_resumen(self) -> tuple[str, str, float]:
        lineas = [f"Resumen del corpus ({len(self.noticias)} noticias):"]
        for n in self.noticias:
            sentimiento = n.get("sentimiento", {}).get("etiqueta", "?")
            categoria = n.get("categoria_predicha", n.get("categoria_original", "?"))
            lineas.append(f"  - [{categoria}][{sentimiento}] {n['titulo']}")
        return "\n".join(lineas), "resumen", 1.0

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def responder(self, pregunta: str) -> tuple[str, str, float]:
        """
        Genera una respuesta considerando el contexto acumulado.

        Devuelve (respuesta, tipo, confianza).
        Tipos posibles: conteo, sentimiento, categoria, resumen,
                        directa, contextual, personalizada, fallback.
        """
        if not pregunta or not pregunta.strip():
            return "No entendi la pregunta. Por favor escribe algo.", "fallback", 0.0

        # Intenciones estructuradas tienen prioridad sobre busqueda contextual
        intencion = self._clasificar_intencion(pregunta)
        if intencion == "conteo":
            respuesta, tipo, confianza = self._respuesta_conteo()
            self.actualizar_contexto(pregunta, tipo)
            return respuesta, tipo, confianza
        if intencion == "sentimiento":
            respuesta, tipo, confianza = self._respuesta_sentimiento()
            self.actualizar_contexto(pregunta, tipo)
            return respuesta, tipo, confianza
        if intencion == "categoria":
            respuesta, tipo, confianza = self._respuesta_categoria()
            self.actualizar_contexto(pregunta, tipo)
            return respuesta, tipo, confianza
        if intencion == "resumen":
            respuesta, tipo, confianza = self._respuesta_resumen()
            self.actualizar_contexto(pregunta, tipo)
            return respuesta, tipo, confianza

        pregunta_normalizada = normalizar_texto(pregunta)

        if self._es_referencia_contextual(pregunta_normalizada) and self.historial:
            consulta_expandida = self.expandir_consulta(pregunta)
            self.ultima_consulta_expandida = consulta_expandida
            resultados = self._buscar(consulta_expandida)
            if resultados:
                tipo = "contextual"
                lineas = ["Basandome en nuestra conversacion anterior, encontre:"]
                for r in resultados:
                    lineas.append(f"\n**{r['titulo']}**\n{r.get('snippet', '')}")
                self.actualizar_contexto(pregunta, tipo, resultados)
                return "\n".join(lineas), tipo, float(resultados[0]["relevancia"])

        resultados = self._buscar(pregunta)
        if resultados:
            temas_pregunta = self._temas_en_pregunta(pregunta)
            tema_prioritario = temas_pregunta[0] if temas_pregunta else None
            if tema_prioritario is None and self.contexto_temas:
                tema_prioritario = self.contexto_temas.most_common(1)[0][0]

            if tema_prioritario:
                filtrados = [r for r in resultados if r.get("categoria") == tema_prioritario]
                if filtrados:
                    tipo = "personalizada"
                    lineas = [f"Como te interesa {tema_prioritario}, aqui las noticias relevantes:"]
                    for r in filtrados:
                        lineas.append(f"\n**{r['titulo']}**\n{r.get('snippet', '')}")
                    self.actualizar_contexto(pregunta, tipo, filtrados)
                    return "\n".join(lineas), tipo, float(filtrados[0]["relevancia"])

            tipo = "directa"
            lineas = [f"Encontre {len(resultados)} noticias relevantes:"]
            for r in resultados:
                lineas.append(f"\n**{r['titulo']}**\n{r.get('snippet', '')}")
            self.actualizar_contexto(pregunta, tipo, resultados)
            return "\n".join(lineas), tipo, float(resultados[0]["relevancia"])

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
            return self.motor.buscar_vectorial(consulta, top_k=20)
        if hasattr(self.motor, "buscar"):
            return self.motor.buscar(consulta, top_k=20)
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
        palabras = set(re.findall(r"\b\w+\b", pregunta_normalizada))
        for ref in cls._REFERENCIAS:
            if " " in ref:  # frase multi-palabra: busqueda de subcadena
                if ref in pregunta_normalizada:
                    return True
            elif ref in palabras:  # palabra sola: coincidencia exacta
                return True
        return False

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
