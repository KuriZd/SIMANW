from __future__ import annotations

import re
from collections import Counter, defaultdict

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


class AnalizadorHiloDiscusion:
    """
    AC-4: Analiza un hilo completo de red social.
    """

    def __init__(self) -> None:
        self._asegurar_recurso_vader()
        self.sia = SentimentIntensityAnalyzer()
        self.mensajes: list[dict] = []

    def cargar_hilo(self, mensajes: list[dict]) -> None:
        """Carga un hilo de discusion y calcula sentimiento por mensaje."""
        self.mensajes = [mensaje.copy() for mensaje in mensajes]
        for mensaje in self.mensajes:
            mensaje["sentimiento"] = float(self.sia.polarity_scores(mensaje["texto"])["compound"])

    def evolucion_sentimiento(self, ventana: int = 3) -> list[dict]:
        """Analiza como evoluciona el sentimiento a lo largo del hilo."""
        if ventana < 1:
            raise ValueError("ventana debe ser al menos 1")

        sentimientos = [mensaje["sentimiento"] for mensaje in self.mensajes]
        evolucion = []
        for indice, sentimiento in enumerate(sentimientos):
            inicio = max(0, indice - ventana + 1)
            segmento = sentimientos[inicio : indice + 1]
            promedio_ventana = sum(segmento) / len(segmento)
            evolucion.append(
                {
                    "posicion": indice + 1,
                    "sentimiento_puntual": sentimiento,
                    "tendencia": promedio_ventana,
                }
            )
        return evolucion

    def detectar_subtemas(self, n_clusters: int = 3) -> dict[int, dict]:
        """Detecta subtemas en el hilo usando clustering TF-IDF + KMeans."""
        if not self.mensajes:
            return {}

        textos = [mensaje["texto"] for mensaje in self.mensajes]
        n_clusters = max(1, min(n_clusters, len(textos)))
        vectorizer = TfidfVectorizer(max_features=500, stop_words="english", token_pattern=r"(?u)\b\w\w+\b")
        matriz = vectorizer.fit_transform(textos)

        if matriz.shape[1] == 0:
            return {0: {"keywords": [], "n_mensajes": len(textos), "mensajes_idx": list(range(len(textos)))}}

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(matriz)

        subtemas = defaultdict(list)
        for indice, cluster_id in enumerate(clusters):
            subtemas[int(cluster_id)].append(indice)

        terminos = vectorizer.get_feature_names_out()
        subtemas_info = {}
        for cluster_id, indices in subtemas.items():
            centroide = kmeans.cluster_centers_[cluster_id]
            top_idx = centroide.argsort()[-5:][::-1]
            keywords = [terminos[indice] for indice in top_idx if centroide[indice] > 0]
            subtemas_info[cluster_id] = {
                "keywords": keywords,
                "n_mensajes": len(indices),
                "mensajes_idx": indices,
            }

        return subtemas_info

    def usuarios_mas_activos(self, top_n: int = 5) -> list[tuple[str, int]]:
        """Identifica usuarios mas participativos."""
        participacion = Counter(mensaje["usuario"] for mensaje in self.mensajes)
        return participacion.most_common(top_n)

    def resumen_hilo(self) -> dict:
        """Genera resumen automatico del hilo."""
        total = len(self.mensajes)
        if total == 0:
            return {
                "total_mensajes": 0,
                "participantes": 0,
                "sentimiento_promedio": 0.0,
                "tono": "mixto",
                "positivos_pct": 0.0,
                "negativos_pct": 0.0,
                "hashtags_top": [],
                "usuarios_activos": [],
            }

        sentimiento_promedio = sum(mensaje["sentimiento"] for mensaje in self.mensajes) / total
        positivos = sum(1 for mensaje in self.mensajes if mensaje["sentimiento"] > 0.05)
        negativos = sum(1 for mensaje in self.mensajes if mensaje["sentimiento"] < -0.05)

        hashtags = Counter()
        for mensaje in self.mensajes:
            hashtags.update(re.findall(r"#(\w+)", mensaje["texto"]))

        if sentimiento_promedio > 0.05:
            tono = "positivo"
        elif sentimiento_promedio < -0.05:
            tono = "negativo"
        else:
            tono = "mixto"

        return {
            "total_mensajes": total,
            "participantes": len(set(mensaje["usuario"] for mensaje in self.mensajes)),
            "sentimiento_promedio": float(sentimiento_promedio),
            "tono": tono,
            "positivos_pct": 100 * positivos / total,
            "negativos_pct": 100 * negativos / total,
            "hashtags_top": hashtags.most_common(5),
            "usuarios_activos": self.usuarios_mas_activos(3),
        }

    @staticmethod
    def _asegurar_recurso_vader() -> None:
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)


HILO_IA_DEMO = [
    {
        "usuario": "@dev_laura",
        "texto": "Just tried the new AI coding assistant and it's amazing! #AI #coding",
        "timestamp": "10:00",
    },
    {
        "usuario": "@tech_mike",
        "texto": "I agree, the code suggestions are incredibly accurate #AI",
        "timestamp": "10:05",
    },
    {
        "usuario": "@skeptic_joe",
        "texto": "But what about job displacement? This AI thing worries me a lot",
        "timestamp": "10:08",
    },
    {
        "usuario": "@dev_laura",
        "texto": "Good point Joe, but I think it's a tool not a replacement #AItools",
        "timestamp": "10:12",
    },
    {
        "usuario": "@data_sara",
        "texto": "The real concern is bias in training data, we need better datasets",
        "timestamp": "10:15",
    },
    {
        "usuario": "@tech_mike",
        "texto": "True, but the progress is undeniable. Exciting times! #innovation",
        "timestamp": "10:20",
    },
    {
        "usuario": "@skeptic_joe",
        "texto": "I lost my freelance gig because of AI. This is terrible for workers",
        "timestamp": "10:25",
    },
    {
        "usuario": "@prof_chen",
        "texto": "Research shows AI creates more jobs than it destroys historically",
        "timestamp": "10:30",
    },
    {
        "usuario": "@data_sara",
        "texto": "We need regulation and ethical guidelines urgently #AIethics",
        "timestamp": "10:35",
    },
    {
        "usuario": "@dev_laura",
        "texto": "Totally agree with Sara. Responsible AI development is key #responsible",
        "timestamp": "10:40",
    },
    {
        "usuario": "@tech_mike",
        "texto": "Companies investing in AI training for employees is the best approach",
        "timestamp": "10:45",
    },
    {
        "usuario": "@prof_chen",
        "texto": "Great discussion everyone! The future needs both innovation and responsibility",
        "timestamp": "10:50",
    },
]
