from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path

import nltk
from nltk import bigrams, trigrams
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize


_CONTEXTO_PERSONA = {
    "presidente", "director", "secretario", "doctor", "dr", "ing", "lic", "señor",
    "señora", "ministro", "gobernador", "senador", "diputado", "general", "fiscal",
}
_CONTEXTO_LUGAR = {
    "ciudad", "estado", "municipio", "país", "región", "colonia", "calle", "avenida",
    "pueblo", "localidad", "delegación", "capital", "territorio",
}
_CONTEXTO_ORG = {
    "empresa", "instituto", "universidad", "secretaría", "ministerio", "partido",
    "organización", "asociación", "corporación", "fundación", "comisión", "consejo",
}

STOPWORDS_ES_FALLBACK = {
    "a",
    "al",
    "como",
    "con",
    "de",
    "del",
    "el",
    "en",
    "es",
    "la",
    "las",
    "lo",
    "los",
    "para",
    "por",
    "que",
    "se",
    "son",
    "su",
    "sus",
    "un",
    "una",
    "y",
}


class AnalisisDiscurso:
    """
    AC-2: Analisis estadistico profundo de textos.

    Calcula n-gramas, riqueza lexica por secciones, entidades nombradas
    heuristicas y comparativas entre multiples documentos.
    """

    def __init__(self, idioma: str = "spanish") -> None:
        self.idioma = idioma
        self.stop_words = self._cargar_stopwords(idioma)

    def analizar(self, texto: str, titulo: str = "Documento") -> dict:
        """Analisis completo de un texto."""
        if not texto or not texto.strip():
            return {"titulo": titulo, "estado": "insuficiente", "motivo": "texto vacío"}

        oraciones = self._sent_tokenize(texto)
        tokens_original = self._word_tokenize(texto)
        tokens_lower = [token.lower() for token in tokens_original]
        tokens_alfa = [token for token in tokens_lower if self._es_palabra(token) and len(token) > 2]
        tokens_filtrados = [token for token in tokens_alfa if token not in self.stop_words]

        if len(tokens_filtrados) < 5:
            return {
                "titulo": titulo,
                "estado": "insuficiente",
                "motivo": f"solo {len(tokens_filtrados)} tokens tras limpieza (mínimo 5)",
            }

        bigramas_lista = list(bigrams(tokens_filtrados))
        trigramas_lista = list(trigrams(tokens_filtrados))

        riqueza_secciones = self._riqueza_por_seccion(tokens_filtrados, secciones=4)
        entidades_tipadas = self._extraer_entidades(tokens_original)
        conteo_ent = Counter(token for token, _ in entidades_tipadas)
        tipos_map = {token: tipo for token, tipo in entidades_tipadas}
        posibles_entidades = [
            (token, tipos_map.get(token, "DESCONOCIDO"), count)
            for token, count in conteo_ent.most_common(8)
        ]

        return {
            "titulo": titulo,
            "estado": "ok",
            "oraciones": len(oraciones),
            "palabras_totales": len(tokens_alfa),
            "vocabulario_unico": len(set(tokens_filtrados)),
            "riqueza_lexica_global": len(set(tokens_filtrados)) / max(len(tokens_filtrados), 1),
            "riqueza_por_seccion": riqueza_secciones,
            "promedio_palabras_oracion": len(tokens_alfa) / max(len(oraciones), 1),
            "top_unigramas": Counter(tokens_filtrados).most_common(10),
            "top_bigramas": Counter(bigramas_lista).most_common(7),
            "top_trigramas": Counter(trigramas_lista).most_common(5),
            "posibles_entidades": posibles_entidades,
            "_tokens_filtrados": tokens_filtrados,
        }

    def comparar_textos(self, analisis_lista: list[dict]) -> list[dict]:
        """Compara estadisticas entre multiples textos. Omite análisis insuficientes."""
        filas = []
        for a in analisis_lista:
            if a.get("estado") == "insuficiente":
                continue
            top_b = a["top_bigramas"][0][0] if a.get("top_bigramas") else ()
            top_t = a["top_trigramas"][0][0] if a.get("top_trigramas") else ()
            filas.append(
                {
                    "titulo": a["titulo"],
                    "palabras": a.get("palabras_totales", 0),
                    "vocabulario": a.get("vocabulario_unico", 0),
                    "riqueza": round(a.get("riqueza_lexica_global", 0.0), 4),
                    "promedio_oracion": round(a.get("promedio_palabras_oracion", 0.0), 1),
                    "top_bigrama": " ".join(top_b) if top_b else "",
                    "top_trigrama": " ".join(top_t) if top_t else "",
                }
            )
        return filas

    @staticmethod
    def guardar_json(
        ruta: str | Path,
        textos_analizados: list[dict],
        comparativa: list[dict],
    ) -> None:
        """Serializa los resultados de AC-2 en un archivo JSON."""
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "actividad": "AC-2",
            "descripcion": "Analisis estadistico profundo de discursos y textos largos",
            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
            "textos_analizados": [_serializar_analisis(a) for a in textos_analizados],
            "comparativa": comparativa,
        }

        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(payload, archivo, ensure_ascii=False, indent=2)

    def _sent_tokenize(self, texto: str) -> list[str]:
        try:
            return sent_tokenize(texto, language=self.idioma)
        except LookupError:
            return [parte.strip() for parte in re.split(r"[.!?]+", texto) if parte.strip()]

    def _word_tokenize(self, texto: str) -> list[str]:
        try:
            return word_tokenize(texto, language=self.idioma)
        except LookupError:
            return re.findall(r"\b[\wáéíóúÁÉÍÓÚñÑüÜ]+\b", texto)

    def _extraer_entidades(self, tokens_original: list[str]) -> list[tuple[str, str]]:
        """Retorna lista de (token, tipo) con tipo: PERSONA | LUGAR | ORG | DESCONOCIDO."""
        tokens_lower = [t.lower() for t in tokens_original]
        entidades: list[tuple[str, str]] = []
        for idx, token in enumerate(tokens_original):
            if not token or not token[0].isupper():
                continue
            if not self._es_palabra(token) or len(token) <= 2:
                continue
            if token.lower() in self.stop_words:
                continue
            contexto = set(tokens_lower[max(0, idx - 3):idx])
            if contexto & _CONTEXTO_PERSONA:
                tipo = "PERSONA"
            elif contexto & _CONTEXTO_LUGAR:
                tipo = "LUGAR"
            elif contexto & _CONTEXTO_ORG:
                tipo = "ORG"
            else:
                tipo = "DESCONOCIDO"
            entidades.append((token, tipo))
        return entidades

    @staticmethod
    def _riqueza_por_seccion(tokens: list[str], secciones: int) -> list[float]:
        if not tokens:
            return []

        tamano = max(len(tokens) // secciones, 1)
        riqueza = []
        for indice in range(secciones):
            inicio = indice * tamano
            fin = len(tokens) if indice == secciones - 1 else (indice + 1) * tamano
            seccion = list(islice(tokens, inicio, fin))
            if seccion:
                riqueza.append(len(set(seccion)) / len(seccion))
        return riqueza

    @staticmethod
    def _es_palabra(token: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-záéíóúÁÉÍÓÚñÑüÜ]+", token))

    @staticmethod
    def _cargar_stopwords(idioma: str) -> set[str]:
        try:
            return set(stopwords.words(idioma))
        except LookupError:
            try:
                nltk.download("stopwords", quiet=True)
                return set(stopwords.words(idioma))
            except LookupError:
                return STOPWORDS_ES_FALLBACK


def generar_nube_palabras(tokens: list[str], ruta: str | Path) -> bool:
    """
    Genera nube de palabras a partir de tokens filtrados.
    Retorna True si se genero, False si wordcloud no esta instalado.
    """
    try:
        from wordcloud import WordCloud  # type: ignore[import]
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    nube = WordCloud(
        width=800,
        height=400,
        background_color="white",
        collocations=False,
    ).generate(" ".join(tokens))

    plt.figure(figsize=(10, 5))
    plt.imshow(nube, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close()
    return True


def _serializar_analisis(analisis: dict) -> dict:
    """Convierte tuplas de n-gramas a listas para que sean serializables en JSON."""
    resultado = {k: v for k, v in analisis.items() if not k.startswith("_")}
    resultado["top_unigramas"] = [[w, c] for w, c in analisis.get("top_unigramas", [])]
    resultado["top_bigramas"] = [[list(b), c] for b, c in analisis.get("top_bigramas", [])]
    resultado["top_trigramas"] = [[list(t), c] for t, c in analisis.get("top_trigramas", [])]
    # Entidades: (token, tipo, count) → [token, tipo, count]
    ents = analisis.get("posibles_entidades", [])
    resultado["posibles_entidades"] = [
        [e[0], e[1], e[2]] if len(e) == 3 else [e[0], "DESCONOCIDO", e[1]]
        for e in ents
    ]
    return resultado
