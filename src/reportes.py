from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

from src.exportador import guardar_markdown


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

    def reporte_markdown(
        self,
        tendencias: dict | None = None,
        consultas_busqueda: list[dict] | None = None,
        respuestas_chatbot: list[dict] | None = None,
        generado_en: datetime | None = None,
    ) -> str:
        """Genera el reporte final en Markdown para entrega reproducible."""
        fecha = generado_en or datetime.now()
        categorias = Counter(self._categoria(noticia) for noticia in self.noticias)
        sentimientos = Counter(
            noticia["sentimiento"]["etiqueta"] for noticia in self.noticias if "sentimiento" in noticia
        )
        scores = [noticia["sentimiento"]["compound"] for noticia in self.noticias if "sentimiento" in noticia]
        promedio = sum(scores) / len(scores) if scores else 0.0

        lineas = [
            "# Reporte final SIMANW",
            "",
            f"Generado: {fecha.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Resumen del corpus",
            "",
            f"- Noticias procesadas: {len(self.noticias)}",
            f"- Categorias detectadas: {len(categorias)}",
            f"- Sentimiento promedio: {promedio:+.3f}",
            f"- Tono general: {self._tono_general(promedio)}",
            f"- Triples RDF: {self.kg.total_triples()}",
            "",
            "## Noticias por categoria",
            "",
            "| Categoria | Noticias |",
            "|---|---:|",
        ]
        for categoria, total in categorias.most_common():
            lineas.append(f"| {categoria} | {total} |")

        lineas.extend(["", "## Analisis de sentimiento", "", "| Sentimiento | Noticias |", "|---|---:|"])
        for etiqueta, total in sentimientos.most_common():
            lineas.append(f"| {etiqueta} | {total} |")

        lineas.extend(["", "## Tendencias", ""])
        if tendencias:
            lineas.append(f"Granularidad: {tendencias.get('granularidad', 'N/D')}")
            lineas.append("")
            lineas.append("| Categoria | Periodo | Noticias |")
            lineas.append("|---|---|---:|")
            for fila in tendencias.get("tabla", []):
                lineas.append(f"| {fila['categoria']} | {fila['periodo']} | {fila['noticias']} |")
            conclusion = tendencias.get("conclusion")
            if conclusion:
                lineas.extend(["", conclusion])
        else:
            lineas.append("No se generaron tendencias para este corpus.")

        lineas.extend(["", "## Consultas de busqueda", ""])
        if consultas_busqueda:
            for item in consultas_busqueda:
                lineas.append(f"### {item['consulta']}")
                resultados = item.get("resultados", [])
                if not resultados:
                    lineas.append("Sin resultados.")
                for resultado in resultados:
                    lineas.append(
                        f"- [{resultado.get('score', resultado.get('relevancia', 0.0)):.3f}] "
                        f"{resultado.get('titulo', '')} "
                        f"({resultado.get('categoria', '?')}, {resultado.get('fecha', '')})"
                    )
        else:
            lineas.append("No se registraron consultas de busqueda.")

        lineas.extend(["", "## Resultados del chatbot", ""])
        if respuestas_chatbot:
            for item in respuestas_chatbot:
                lineas.append(f"- Pregunta: {item['pregunta']}")
                lineas.append(f"  Respuesta: {item['respuesta']}")
        else:
            lineas.append("No se registraron respuestas del chatbot.")

        lineas.extend(
            [
                "",
                "## Resumen del grafo RDF",
                "",
                f"- Total de triples: {self.kg.total_triples()}",
                "- Serializaciones generadas: Turtle y JSON-LD.",
                "- Consultable mediante SPARQL con prefijos SIMANW, Dublin Core, FOAF y Schema.org.",
                "",
                "## Conclusiones",
                "",
                "El pipeline integra rastreo o carga de corpus, depuracion, procesamiento NLP, "
                "clasificacion, sentimiento, busqueda, Q&A, grafo RDF y reportes. Los artefactos "
                "generados permiten reproducir la ejecucion y auditar cada etapa sin depender "
                "unicamente de salidas por consola.",
                "",
            ]
        )

        return "\n".join(lineas)

    def guardar_reporte_markdown(
        self,
        ruta: str | Path = "outputs/reportes/reporte_final.md",
        tendencias: dict | None = None,
        consultas_busqueda: list[dict] | None = None,
        respuestas_chatbot: list[dict] | None = None,
        generado_en: datetime | None = None,
    ) -> Path:
        contenido = self.reporte_markdown(
            tendencias=tendencias,
            consultas_busqueda=consultas_busqueda,
            respuestas_chatbot=respuestas_chatbot,
            generado_en=generado_en,
        )
        return guardar_markdown(contenido, ruta)

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
