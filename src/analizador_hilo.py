from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import nltk
import numpy as np
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


# ── Léxico heurístico para español ────────────────────────────────────────────

_POSITIVOS_ES: frozenset[str] = frozenset({
    "bueno", "buena", "excelente", "bien", "positivo", "positiva",
    "innovacion", "increible", "importante", "mejor", "avance", "logro",
    "beneficio", "favorable", "prometedor", "util", "eficiente", "valioso",
    "ganancia", "oportunidad", "progreso", "mejorar", "acuerdo", "apoyo",
    "transparencia", "esperanza", "optimista", "educacion", "calidad",
    "exitoso", "fuerte", "colaboracion", "propuesta", "valiosa", "progresista",
    "adecuada", "responsablemente", "capacitacion", "equidad", "solida",
    "adaptarse", "aprovechar", "integre", "marco", "pedagogico",
})

_NEGATIVOS_ES: frozenset[str] = frozenset({
    "malo", "mala", "terrible", "negativo", "negativa", "preocupa",
    "preocupaciones", "crisis", "desempleo", "problema", "riesgo", "dano",
    "perdida", "fracaso", "corrupcion", "desigualdad", "conflicto", "amenaza",
    "desastre", "recesion", "peligro", "injusticia", "violencia", "pobreza",
    "desacuerdo", "censura", "inflacion", "privacidad", "sesgo", "perjuicio",
    "error", "caida", "deterioro", "plagio", "deshonestidad", "restricciones",
    "perdemos",
})


def _score_heuristico_es(texto: str) -> float:
    """Puntua el sentimiento con léxico heurístico en español (-1.0 a 1.0)."""
    tokens = re.findall(r"\w+", texto.lower())
    pos = sum(1 for t in tokens if t in _POSITIVOS_ES)
    neg = sum(1 for t in tokens if t in _NEGATIVOS_ES)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / max(total, 1), 4)


# ── Clase principal ────────────────────────────────────────────────────────────

class AnalizadorHiloDiscusion:
    """
    AC-4: Analiza un hilo completo de red social o foro de discusion.

    idioma="english" usa VADER; idioma="spanish" usa léxico heurístico.
    """

    def __init__(self, idioma: str = "english") -> None:
        self.idioma = idioma
        self._asegurar_recurso_vader()
        self.sia = SentimentIntensityAnalyzer() if idioma == "english" else None
        self.mensajes: list[dict] = []

    # ── Carga ─────────────────────────────────────────────────────────────────

    def cargar_hilo(self, mensajes: list[dict]) -> None:
        """Carga un hilo y calcula sentimiento + tono por mensaje."""
        if not mensajes:
            raise ValueError("El hilo no puede estar vacio")
        for i, msg in enumerate(mensajes):
            for campo in ("usuario", "texto", "timestamp"):
                if campo not in msg:
                    raise ValueError(f"Mensaje {i} no tiene el campo requerido '{campo}'")

        self.mensajes = [msg.copy() for msg in mensajes]
        for msg in self.mensajes:
            score = self._score(msg["texto"])
            msg["sentimiento"] = score
            msg["tono"] = "positivo" if score > 0.05 else "negativo" if score < -0.05 else "neutral"

    # ── Análisis ──────────────────────────────────────────────────────────────

    def evolucion_sentimiento(self, ventana: int = 3) -> list[dict]:
        """Evolucion del sentimiento con promedio movil."""
        if ventana < 1:
            raise ValueError("ventana debe ser al menos 1")

        sentimientos = [msg["sentimiento"] for msg in self.mensajes]
        evolucion = []
        for i, score in enumerate(sentimientos):
            inicio = max(0, i - ventana + 1)
            segmento = sentimientos[inicio : i + 1]
            evolucion.append({
                "posicion": i + 1,
                "usuario": self.mensajes[i]["usuario"],
                "timestamp": self.mensajes[i]["timestamp"],
                "sentimiento_puntual": score,
                "tendencia": round(sum(segmento) / len(segmento), 4),
            })
        return evolucion

    def detectar_subtemas(self, n_clusters: int = 3) -> dict[int, dict]:
        """Detecta subtemas usando TF-IDF + KMeans."""
        if not self.mensajes:
            return {}

        textos = [msg["texto"] for msg in self.mensajes]
        n_clusters = max(1, min(n_clusters, len(textos)))
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            token_pattern=r"(?u)\b\w\w+\b",
        )
        matriz = vectorizer.fit_transform(textos)

        if matriz.shape[1] == 0:
            return {
                0: {
                    "keywords": [],
                    "n_mensajes": len(textos),
                    "mensajes_idx": list(range(len(textos))),
                    "usuarios": list({msg["usuario"] for msg in self.mensajes}),
                    "sentimiento_promedio": float(np.mean([msg["sentimiento"] for msg in self.mensajes])),
                }
            }

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(matriz)

        agrupados: dict[int, list[int]] = defaultdict(list)
        for idx, cluster_id in enumerate(clusters):
            agrupados[int(cluster_id)].append(idx)

        terminos = vectorizer.get_feature_names_out()
        subtemas_info: dict[int, dict] = {}
        for cluster_id, indices in agrupados.items():
            centroide = kmeans.cluster_centers_[cluster_id]
            top_idx = centroide.argsort()[-5:][::-1]
            keywords = [terminos[i] for i in top_idx if centroide[i] > 0]
            sentimientos_cluster = [self.mensajes[i]["sentimiento"] for i in indices]
            subtemas_info[cluster_id] = {
                "keywords": keywords,
                "n_mensajes": len(indices),
                "mensajes_idx": indices,
                "usuarios": sorted({self.mensajes[i]["usuario"] for i in indices}),
                "sentimiento_promedio": round(float(np.mean(sentimientos_cluster)), 4),
            }

        return subtemas_info

    def usuarios_mas_activos(self, top_n: int = 5) -> list[tuple[str, int]]:
        """Identifica usuarios mas participativos."""
        return Counter(msg["usuario"] for msg in self.mensajes).most_common(top_n)

    def extraer_hashtags(self) -> list[tuple[str, int]]:
        """Extrae y cuenta hashtags del hilo."""
        conteo: Counter = Counter()
        for msg in self.mensajes:
            conteo.update(re.findall(r"#(\w+)", msg["texto"]))
        return conteo.most_common()

    def resumen_hilo(self) -> dict:
        """Resumen estadístico automático del hilo."""
        total = len(self.mensajes)
        if total == 0:
            return {
                "total_mensajes": 0,
                "participantes": 0,
                "sentimiento_promedio": 0.0,
                "tono": "mixto",
                "positivos_pct": 0.0,
                "negativos_pct": 0.0,
                "neutrales_pct": 0.0,
                "hashtags_top": [],
                "usuarios_activos": [],
            }

        scores = [msg["sentimiento"] for msg in self.mensajes]
        promedio = sum(scores) / total
        positivos = sum(1 for s in scores if s > 0.05)
        negativos = sum(1 for s in scores if s < -0.05)
        neutrales = total - positivos - negativos

        tono = "positivo" if promedio > 0.05 else "negativo" if promedio < -0.05 else "mixto"

        return {
            "total_mensajes": total,
            "participantes": len({msg["usuario"] for msg in self.mensajes}),
            "sentimiento_promedio": round(float(promedio), 4),
            "tono": tono,
            "positivos_pct": round(100 * positivos / total, 1),
            "negativos_pct": round(100 * negativos / total, 1),
            "neutrales_pct": round(100 * neutrales / total, 1),
            "hashtags_top": self.extraer_hashtags()[:5],
            "usuarios_activos": self.usuarios_mas_activos(3),
        }

    def generar_resumen_textual(self) -> str:
        """Produce un resumen legible del hilo."""
        resumen = self.resumen_hilo()
        subtemas = self.detectar_subtemas()

        keywords: list[str] = []
        for info in subtemas.values():
            keywords.extend(info["keywords"][:2])
        temas_str = ", ".join(dict.fromkeys(keywords[:6])) or "varios temas"

        usuarios = [u for u, _ in resumen["usuarios_activos"][:3]]
        usuarios_str = ", ".join(usuarios) or "desconocidos"

        hashtags = [f"#{h}" for h, _ in resumen["hashtags_top"][:4]]
        hashtags_str = " ".join(hashtags) if hashtags else "sin hashtags"

        return (
            f"El hilo contiene {resumen['total_mensajes']} mensajes de "
            f"{resumen['participantes']} participantes. "
            f"El tono general fue {resumen['tono']} "
            f"(sentimiento promedio: {resumen['sentimiento_promedio']:+.3f}). "
            f"Se detectaron {resumen['positivos_pct']:.0f}% mensajes positivos "
            f"y {resumen['negativos_pct']:.0f}% negativos. "
            f"Los temas principales fueron: {temas_str}. "
            f"Hashtags destacados: {hashtags_str}. "
            f"Los usuarios mas activos fueron: {usuarios_str}."
        )

    def guardar_json(self, ruta: str | Path) -> None:
        """Exporta el análisis completo a JSON."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        resumen = self.resumen_hilo()
        resumen_serializable = {
            **resumen,
            "hashtags_top": [list(h) for h in resumen["hashtags_top"]],
            "usuarios_activos": [list(u) for u in resumen["usuarios_activos"]],
        }

        payload = {
            "actividad": "AC-4",
            "descripcion": "Analisis de hilos de discusion de red social",
            "idioma": self.idioma,
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "resumen": resumen_serializable,
            "evolucion_sentimiento": self.evolucion_sentimiento(),
            "subtemas": {str(k): v for k, v in self.detectar_subtemas().items()},
            "usuarios_activos": [list(u) for u in self.usuarios_mas_activos()],
            "hashtags": [list(h) for h in self.extraer_hashtags()],
            "resumen_textual": self.generar_resumen_textual(),
            "mensajes_analizados": self.mensajes,
        }

        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(payload, archivo, ensure_ascii=False, indent=2)

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _score(self, texto: str) -> float:
        if self.sia is not None:
            return float(self.sia.polarity_scores(texto)["compound"])
        return _score_heuristico_es(texto)

    @staticmethod
    def _asegurar_recurso_vader() -> None:
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)


# ── Función de carga desde JSON ───────────────────────────────────────────────

def cargar_hilo_desde_json(ruta: str | Path) -> list[dict]:
    """
    Carga un hilo desde un archivo JSON.
    Normaliza campos alternativos (author/text/date → usuario/texto/timestamp).
    """
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    if not isinstance(datos, list):
        raise ValueError("El JSON debe contener una lista de mensajes")

    mensajes: list[dict] = []
    for item in datos:
        texto = item.get("texto") or item.get("text") or item.get("contenido") or ""
        if not texto:
            continue
        mensajes.append({
            "usuario": item.get("usuario") or item.get("author") or item.get("user") or "@desconocido",
            "texto": str(texto),
            "timestamp": str(item.get("timestamp") or item.get("fecha") or item.get("date") or ""),
        })
    return mensajes


# ── Demo en inglés (retrocompatibilidad) ──────────────────────────────────────

HILO_IA_DEMO = [
    {"usuario": "@dev_laura",   "texto": "Just tried the new AI coding assistant and it's amazing! #AI #coding", "timestamp": "10:00"},
    {"usuario": "@tech_mike",   "texto": "I agree, the code suggestions are incredibly accurate #AI",             "timestamp": "10:05"},
    {"usuario": "@skeptic_joe", "texto": "But what about job displacement? This AI thing worries me a lot",       "timestamp": "10:08"},
    {"usuario": "@dev_laura",   "texto": "Good point Joe, but I think it's a tool not a replacement #AItools",    "timestamp": "10:12"},
    {"usuario": "@data_sara",   "texto": "The real concern is bias in training data, we need better datasets",    "timestamp": "10:15"},
    {"usuario": "@tech_mike",   "texto": "True, but the progress is undeniable. Exciting times! #innovation",     "timestamp": "10:20"},
    {"usuario": "@skeptic_joe", "texto": "I lost my freelance gig because of AI. This is terrible for workers",   "timestamp": "10:25"},
    {"usuario": "@prof_chen",   "texto": "Research shows AI creates more jobs than it destroys historically",     "timestamp": "10:30"},
    {"usuario": "@data_sara",   "texto": "We need regulation and ethical guidelines urgently #AIethics",          "timestamp": "10:35"},
    {"usuario": "@dev_laura",   "texto": "Totally agree with Sara. Responsible AI development is key #responsible","timestamp": "10:40"},
    {"usuario": "@tech_mike",   "texto": "Companies investing in AI training for employees is the best approach", "timestamp": "10:45"},
    {"usuario": "@prof_chen",   "texto": "Great discussion everyone! The future needs both innovation and responsibility", "timestamp": "10:50"},
]

# ── Demo en español ───────────────────────────────────────────────────────────

HILO_IA_ES = [
    {"usuario": "@prof_morales",     "texto": "La inteligencia artificial en educacion es una oportunidad increible para los estudiantes #IA #educacion", "timestamp": "09:00"},
    {"usuario": "@estudiante_ana",   "texto": "Totalmente de acuerdo! Las herramientas de IA me ayudan a aprender mejor #innovacion",                     "timestamp": "09:05"},
    {"usuario": "@maestro_garcia",   "texto": "Tengo preocupaciones sobre el plagio y la deshonestidad academica con estas herramientas",                  "timestamp": "09:08"},
    {"usuario": "@investigador_reyes","texto": "El riesgo de sesgo en los algoritmos es un problema grave que debemos atender #sesgo",                      "timestamp": "09:12"},
    {"usuario": "@prof_morales",     "texto": "Con regulacion adecuada podemos aprovechar los beneficios sin perder calidad educativa #regulacion",        "timestamp": "09:15"},
    {"usuario": "@estudiante_ana",   "texto": "La IA me ahorra tiempo en tareas repetitivas y me permite enfocarme en pensar de forma critica",            "timestamp": "09:18"},
    {"usuario": "@maestro_garcia",   "texto": "Perdemos la evaluacion real del conocimiento si los alumnos usan IA sin restricciones claras",              "timestamp": "09:22"},
    {"usuario": "@empresario_vega",  "texto": "Las empresas necesitan profesionales que sepan usar IA, la educacion debe adaptarse al futuro #futuro",     "timestamp": "09:25"},
    {"usuario": "@investigador_reyes","texto": "La desigualdad de acceso a tecnologia es una amenaza real para la equidad educativa #equidad",              "timestamp": "09:30"},
    {"usuario": "@prof_morales",     "texto": "Propongo un marco etico y pedagogico que integre IA responsablemente en el aula #etica",                    "timestamp": "09:35"},
    {"usuario": "@estudiante_ana",   "texto": "Me parece una propuesta muy valiosa y progresista para el futuro de la educacion",                          "timestamp": "09:40"},
    {"usuario": "@maestro_garcia",   "texto": "Si hay capacitacion docente adecuada la propuesta podria funcionar bien #capacitacion",                     "timestamp": "09:45"},
    {"usuario": "@empresario_vega",  "texto": "El sector privado puede apoyar con recursos y plataformas de calidad #colaboracion",                        "timestamp": "09:48"},
    {"usuario": "@investigador_reyes","texto": "Necesitamos investigacion solida sobre el impacto real en el aprendizaje de los alumnos #investigacion",    "timestamp": "09:52"},
]
