from __future__ import annotations

from collections import Counter
from datetime import datetime


class GeneradorReportes:
    """Genera reportes automaticos del SIMANW."""

    def __init__(self, noticias: list[dict], knowledge_graph) -> None:
        self.noticias = noticias
        self.kg = knowledge_graph

    def reporte_completo(self, generado_en: datetime | None = None) -> str:
        """Genera el reporte integrador completo."""
        fecha = generado_en or datetime.now()
        lineas = []
        lineas.append("=" * 70)
        lineas.append("  REPORTE AUTOMATICO - SISTEMA SIMANW")
        lineas.append(f"  Generado: {fecha.strftime('%Y-%m-%d %H:%M:%S')}")
        lineas.append("=" * 70)

        categorias = Counter(self._categoria(noticia) for noticia in self.noticias)
        sentimientos = [noticia["sentimiento"]["compound"] for noticia in self.noticias if "sentimiento" in noticia]
        promedio_sentimiento = sum(sentimientos) / len(sentimientos) if sentimientos else 0.0

        lineas.append("\n1. RESUMEN EJECUTIVO")
        lineas.append("-" * 40)
        lineas.append(f"   Noticias procesadas: {len(self.noticias)}")
        lineas.append(f"   Triples en Knowledge Graph: {self.kg.total_triples()}")
        lineas.append(f"   Categorias detectadas: {len(categorias)}")
        lineas.append(f"   Sentimiento promedio: {promedio_sentimiento:+.3f}")
        lineas.append(f"   Tono general: {self._tono_general(promedio_sentimiento)}")

        lineas.append("\n2. DISTRIBUCION POR CATEGORIA")
        lineas.append("-" * 40)
        for categoria, total in categorias.most_common():
            barra = "#" * (total * 8)
            porcentaje = 100 * total / max(len(self.noticias), 1)
            lineas.append(f"   {categoria:<12} {barra} {total} ({porcentaje:.0f}%)")

        lineas.append("\n3. ANALISIS DE SENTIMIENTO")
        lineas.append("-" * 40)
        distribucion_sentimiento = Counter(
            noticia["sentimiento"]["etiqueta"] for noticia in self.noticias if "sentimiento" in noticia
        )
        for etiqueta, total in distribucion_sentimiento.most_common():
            marcador = "+" if etiqueta == "positivo" else "-" if etiqueta == "negativo" else "~"
            lineas.append(f"   [{marcador}] {etiqueta}: {total} noticia(s)")

        lineas.append("\n   Detalle por noticia:")
        noticias_ordenadas = sorted(
            self.noticias,
            key=lambda noticia: noticia.get("sentimiento", {}).get("compound", 0.0),
        )
        for noticia in noticias_ordenadas:
            sentimiento = noticia.get("sentimiento")
            if sentimiento:
                lineas.append(f"   [{sentimiento['compound']:+.3f}] {noticia['titulo'][:50]}")

        lineas.append("\n4. CATALOGO DE NOTICIAS")
        lineas.append("-" * 40)
        for indice, noticia in enumerate(self.noticias, start=1):
            categoria = self._categoria(noticia)
            sentimiento = noticia.get("sentimiento", {}).get("etiqueta", "?")
            lineas.append(f"   {indice}. [{noticia['fecha']}] [{categoria}] [{sentimiento}]")
            lineas.append(f"      {noticia['titulo']}")
            lineas.append(f"      Autor: {noticia.get('autor', '?')} | Fuente: {noticia.get('fuente', '?')}")
            lineas.append("")

        lineas.append("\n5. CAPACIDADES DEMOSTRADAS")
        lineas.append("-" * 40)
        for nombre, descripcion in capacidades_simanw():
            lineas.append(f"   [OK] {nombre:<16}  {descripcion}")

        lineas.append("\n" + "=" * 70)
        lineas.append("  FIN DEL REPORTE")
        lineas.append("=" * 70)

        return "\n".join(lineas)

    @staticmethod
    def _categoria(noticia: dict) -> str:
        return noticia.get("categoria_predicha", noticia.get("categoria_original", "general"))

    @staticmethod
    def _tono_general(promedio: float) -> str:
        if promedio > 0.05:
            return "POSITIVO"
        if promedio < -0.05:
            return "NEGATIVO"
        return "NEUTRAL"


def capacidades_simanw() -> list[tuple[str, str]]:
    return [
        ("Rastreo Web", "Extraccion automatica con BeautifulSoup/Scrapy"),
        ("NLP", "Tokenizacion, stemming, stopwords, representacion TF-IDF"),
        ("Clasificacion", "Categorizacion automatica con SVM/NB"),
        ("Sentimientos", "Analisis de polaridad con VADER"),
        ("Recomendacion", "Sugerencias basadas en similitud coseno"),
        ("Publicidad", "Deteccion de temas en conversacion"),
        ("Busqueda", "Motor con indice invertido y ranking vectorial"),
        ("Evaluacion IRS", "Precision, Recall, F1, MAP, P@K"),
        ("Chatbot", "Respuestas por similitud semantica"),
        ("Q&A", "Pregunta-respuesta con comprension de intencion"),
        ("Knowledge Graph", "Ontologia OWL + triples RDF"),
        ("SPARQL", "Consultas semanticas sobre el grafo"),
        ("Datos Abiertos", "Integracion con datasets gubernamentales"),
        ("Reportes", "Generacion automatica de resumenes"),
    ]


def resumen_pipeline_completo() -> str:
    return """

           SISTEMA SIMANW - PIPELINE COMPLETO

  Fase 1: RASTREO WEB
     HTML parsing (BeautifulSoup)
     Control de alcance (dominio/directorio)
     Spider (Scrapy en produccion)
     Almacenamiento (JSON/CSV)

  Fase 2: PROCESAMIENTO NLP
     Tokenizacion + Limpieza
     Stopwords + Stemming
     Vectorizacion TF-IDF
     Calculo de similitudes (coseno)

  Fase 3: ANALISIS AUTOMATICO
     Clasificacion (SVM/NB)
     Sentimiento (VADER)
     Recomendacion (similitud contenido)
     Deteccion temas + publicidad

  Fase 4: MOTOR DE BUSQUEDA
     Indice invertido
     Busqueda booleana y vectorial
     Evaluacion (P, R, F1, MAP)
     Busqueda en lenguaje natural

  Fase 5: CHATBOT + Q&A
     Chatbot por similitud
     Sistema pregunta-respuesta
     Comprension de intencion

  Fase 6: WEB SEMANTICA
     Ontologia OWL del dominio
     Knowledge Graph (RDF triples)
     Consultas SPARQL
     Datos abiertos + Linked Data

  Fase 7: REPORTES + ENTREGA
     Generacion automatica de reportes
     Estadisticas y visualizacion

"""
