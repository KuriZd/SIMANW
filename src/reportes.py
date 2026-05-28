from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.exportador import guardar_json, guardar_markdown


class GeneradorReportes:
    """Genera reportes automaticos del SIMANW."""

    def __init__(self, noticias: list[dict], knowledge_graph) -> None:
        self.noticias = noticias
        self.kg = knowledge_graph

    def reporte_completo(self, generado_en: datetime | None = None) -> str:
        """Genera el reporte integrador completo en texto plano."""
        fecha = generado_en or datetime.now()
        categorias = Counter(self._categoria(noticia) for noticia in self.noticias)
        sentimientos = [self._compound(noticia) for noticia in self.noticias if self._compound(noticia) is not None]
        promedio_sentimiento = sum(sentimientos) / len(sentimientos) if sentimientos else 0.0

        lineas = [
            "=" * 70,
            "  REPORTE AUTOMATICO - SISTEMA SIMANW",
            f"  Generado: {fecha.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
            "",
            "1. RESUMEN EJECUTIVO",
            "-" * 40,
            f"   Noticias procesadas: {len(self.noticias)}",
            f"   Triples en Knowledge Graph: {self._total_triples()}",
            f"   Categorias detectadas: {len(categorias)}",
            f"   Sentimiento promedio: {promedio_sentimiento:+.3f}",
            f"   Tono general: {self._tono_general(promedio_sentimiento)}",
            "",
            "2. DISTRIBUCION POR CATEGORIA",
            "-" * 40,
        ]

        for categoria, total in categorias.most_common():
            barra = "#" * (total * 8)
            porcentaje = 100 * total / max(len(self.noticias), 1)
            lineas.append(f"   {categoria:<12} {barra} {total} ({porcentaje:.0f}%)")

        lineas.extend(["", "3. ANALISIS DE SENTIMIENTO", "-" * 40])
        distribucion_sentimiento = Counter(
            self._etiqueta_sentimiento(noticia) for noticia in self.noticias if self._etiqueta_sentimiento(noticia)
        )
        for etiqueta, total in distribucion_sentimiento.most_common():
            marcador = "+" if etiqueta == "positivo" else "-" if etiqueta == "negativo" else "~"
            lineas.append(f"   [{marcador}] {etiqueta}: {total} noticia(s)")

        lineas.append("\n   Detalle por noticia:")
        noticias_ordenadas = sorted(self.noticias, key=lambda noticia: self._compound(noticia) or 0.0)
        for noticia in noticias_ordenadas:
            compound = self._compound(noticia)
            if compound is not None:
                lineas.append(f"   [{compound:+.3f}] {self._titulo(noticia)[:50]}")

        lineas.extend(["", "4. CATALOGO DE NOTICIAS", "-" * 40])
        for indice, noticia in enumerate(self.noticias, start=1):
            categoria = self._categoria(noticia)
            sentimiento = self._etiqueta_sentimiento(noticia) or "?"
            lineas.append(f"   {indice}. [{self._fecha(noticia)}] [{categoria}] [{sentimiento}]")
            lineas.append(f"      {self._titulo(noticia)}")
            lineas.append(f"      Autor: {self._valor(noticia, 'autor')} | Fuente: {self._valor(noticia, 'fuente')}")
            lineas.append("")

        lineas.extend(["", "5. CAPACIDADES DEMOSTRADAS", "-" * 40])
        for nombre, descripcion in capacidades_simanw():
            lineas.append(f"   [OK] {nombre:<16}  {descripcion}")

        lineas.extend(["", "=" * 70, "  FIN DEL REPORTE", "=" * 70])
        return "\n".join(lineas)

    def reporte_markdown(
        self,
        tendencias: dict | None = None,
        consultas_busqueda: list[dict] | None = None,
        respuestas_chatbot: list[dict] | None = None,
        analisis: dict | None = None,
        grafo_info: dict | None = None,
        evidencias_ac: dict[str, dict] | None = None,
        estado_pipeline: dict[str, str] | None = None,
        archivos_generados: list[str] | None = None,
        generado_en: datetime | None = None,
    ) -> str:
        """Genera el reporte final en Markdown para entrega reproducible."""
        fecha = generado_en or datetime.now()
        analisis = analisis or {}
        grafo_info = grafo_info or {}
        evidencias_ac = evidencias_ac or {}
        estado_pipeline = estado_pipeline or {}
        archivos_generados = archivos_generados or []

        categorias = Counter(self._categoria(noticia) for noticia in self.noticias)
        sentimientos = Counter(
            self._etiqueta_sentimiento(noticia) for noticia in self.noticias if self._etiqueta_sentimiento(noticia)
        )
        scores = [self._compound(noticia) for noticia in self.noticias if self._compound(noticia) is not None]
        promedio = sum(scores) / len(scores) if scores else 0.0
        triples = int(grafo_info.get("total_triples", self._total_triples()) or 0)

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
            f"- Triples RDF: {triples}",
            f"- Artefactos generados: {len(archivos_generados)}",
            "",
        ]

        self._agregar_estado_pipeline(lineas, estado_pipeline)
        self._agregar_evidencia_academica(lineas, evidencias_ac)
        self._agregar_ac3(lineas, analisis)
        self._agregar_ac5(lineas, analisis)
        self._agregar_ac7(lineas, grafo_info)

        lineas.extend(["## Noticias por categoria", "", "| Categoria | Noticias |", "|---|---:|"])
        for categoria, total in categorias.most_common():
            lineas.append(f"| {categoria} | {total} |")

        lineas.extend(["", "## Analisis de sentimiento", "", "| Sentimiento | Noticias |", "|---|---:|"])
        for etiqueta, total in sentimientos.most_common():
            lineas.append(f"| {etiqueta} | {total} |")

        lineas.extend(["", "## Tendencias", ""])
        self._agregar_tendencias(lineas, tendencias)

        lineas.extend(["", "## Consultas de busqueda", ""])
        self._agregar_consultas(lineas, consultas_busqueda)

        lineas.extend(["", "## Resultados del chatbot", ""])
        self._agregar_chatbot(lineas, respuestas_chatbot)

        lineas.extend(
            [
                "",
                "## Resumen del grafo RDF",
                "",
                f"- Total de triples: {triples}",
                "- Serializaciones generadas: Turtle y JSON-LD.",
                "- Consultable mediante SPARQL con prefijos SIMANW, Dublin Core, FOAF y Schema.org.",
                "",
                "## Catalogo de noticias procesadas",
                "",
                "| # | Fecha | Titulo | Categoria | Sentimiento | Autor | Fuente |",
                "|---:|---|---|---|---|---|---|",
            ]
        )
        for indice, noticia in enumerate(self.noticias, start=1):
            lineas.append(
                f"| {indice} | {self._fecha(noticia)} | {self._escape(self._titulo(noticia))} | "
                f"{self._escape(self._categoria(noticia))} | {self._etiqueta_sentimiento(noticia) or 'N/D'} | "
                f"{self._escape(self._valor(noticia, 'autor'))} | {self._escape(self._valor(noticia, 'fuente'))} |"
            )

        lineas.extend(["", "## Artefactos generados", ""])
        if archivos_generados:
            for ruta in archivos_generados:
                lineas.append(f"- `{ruta}`")
        else:
            lineas.append("No se registraron artefactos adicionales.")

        lineas.extend(
            [
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
        analisis: dict | None = None,
        grafo_info: dict | None = None,
        evidencias_ac: dict[str, dict] | None = None,
        estado_pipeline: dict[str, str] | None = None,
        archivos_generados: list[str] | None = None,
        generado_en: datetime | None = None,
    ) -> Path:
        contenido = self.reporte_markdown(
            tendencias=tendencias,
            consultas_busqueda=consultas_busqueda,
            respuestas_chatbot=respuestas_chatbot,
            analisis=analisis,
            grafo_info=grafo_info,
            evidencias_ac=evidencias_ac,
            estado_pipeline=estado_pipeline,
            archivos_generados=archivos_generados,
            generado_en=generado_en,
        )
        return guardar_markdown(contenido, ruta)

    def guardar_reporte_json(
        self,
        ruta: str | Path = "outputs/reportes/reporte_final.json",
        analisis: dict | None = None,
        grafo_info: dict | None = None,
        evidencias_ac: dict[str, dict] | None = None,
        estado_pipeline: dict[str, str] | None = None,
        archivos_generados: list[str] | None = None,
        generado_en: datetime | None = None,
    ) -> Path:
        fecha = generado_en or datetime.now()
        scores = [self._compound(noticia) for noticia in self.noticias if self._compound(noticia) is not None]
        promedio = sum(scores) / len(scores) if scores else 0.0
        data: dict[str, Any] = {
            "fase": "Fase 7",
            "generado": fecha.isoformat(),
            "resumen": {
                "noticias_procesadas": len(self.noticias),
                "categorias": dict(Counter(self._categoria(noticia) for noticia in self.noticias)),
                "sentimiento_promedio": promedio,
                "tono_general": self._tono_general(promedio),
                "triples_rdf": int((grafo_info or {}).get("total_triples", self._total_triples()) or 0),
            },
            "pipeline": estado_pipeline or {},
            "evidencias_ac": evidencias_ac or {},
            "analisis": analisis or {},
            "grafo": grafo_info or {},
            "archivos_generados": archivos_generados or [],
        }
        return guardar_json(_serializable(data), ruta)

    def _agregar_estado_pipeline(self, lineas: list[str], estado_pipeline: dict[str, str]) -> None:
        if not estado_pipeline:
            return
        lineas.extend(["## Estado del pipeline", "", "| Etapa | Estado |", "|---|---|"])
        for etapa, estado in estado_pipeline.items():
            lineas.append(f"| {etapa} | {estado} |")
        lineas.append("")

    def _agregar_evidencia_academica(self, lineas: list[str], evidencias_ac: dict[str, dict]) -> None:
        if not evidencias_ac:
            return
        lineas.extend(["## Evidencia academica integrada", "", "| Criterio | Estado | Ejecutado desde | Archivo/Evidencia |", "|---|---|---|---|"])
        for clave, evidencia in sorted(evidencias_ac.items()):
            archivo = (
                evidencia.get("archivo_json")
                or evidencia.get("archivo_ttl")
                or evidencia.get("archivo")
                or evidencia.get("observacion")
                or "N/D"
            )
            lineas.append(
                f"| {clave} | {evidencia.get('estado', 'N/D')} | "
                f"{evidencia.get('ejecutado_desde', 'N/D')} | {archivo} |"
            )
        lineas.append("")

    def _agregar_ac3(self, lineas: list[str], analisis: dict) -> None:
        clasificacion = analisis.get("clasificacion", {})
        ac3 = clasificacion.get("ac3", {}) if isinstance(clasificacion, dict) else {}
        if not ac3:
            return
        lineas.extend(
            [
                "## Clasificacion multimodelo (AC-3)",
                "",
                f"- Estado: {ac3.get('estado', 'N/D')}",
                f"- Mejor modelo: {ac3.get('mejor_modelo', ac3.get('modelo', 'N/D'))}",
                f"- Accuracy promedio: {self._fmt(ac3.get('accuracy_promedio'))}",
                f"- Desviacion estandar: {self._fmt(ac3.get('accuracy_std'))}",
                f"- Archivo de evidencia: {ac3.get('archivo_json', 'N/D')}",
                "",
            ]
        )

    def _agregar_ac5(self, lineas: list[str], analisis: dict) -> None:
        evaluacion = analisis.get("evaluacion_busqueda", {})
        if not evaluacion:
            return
        lineas.extend(
            [
                "## Evaluacion del motor de busqueda (AC-5)",
                "",
                f"- Estado: {evaluacion.get('estado', 'N/D')}",
                f"- Consultas evaluadas: {evaluacion.get('total_consultas', 0)}",
                f"- Ganador por F1: {evaluacion.get('ganador_f1', 'N/D')}",
                f"- Ganador por MAP: {evaluacion.get('ganador_map', 'N/D')}",
                f"- MAP booleano: {self._fmt(evaluacion.get('map_booleano'))}",
                f"- MAP vectorial: {self._fmt(evaluacion.get('map_vectorial'))}",
                f"- Archivo de evidencia: {evaluacion.get('archivo_json', 'N/D')}",
                "",
            ]
        )

    def _agregar_ac7(self, lineas: list[str], grafo_info: dict) -> None:
        evidencia = grafo_info.get("evidencia_ac7", {})
        if not evidencia:
            return
        lineas.extend(
            [
                "## Knowledge Graph y Wikidata (AC-7)",
                "",
                f"- Estado: {evidencia.get('estado', 'N/D')}",
                f"- Entidades evaluadas: {evidencia.get('entidades_evaluadas', 0)}",
                f"- Enlaces externos creados: {evidencia.get('total_enlaces_externos', 0)}",
                f"- Endpoint: {evidencia.get('endpoint', 'N/D')}",
                f"- Archivo RDF enriquecido: {evidencia.get('archivo_ttl', 'N/D')}",
                "",
            ]
        )

    def _agregar_tendencias(self, lineas: list[str], tendencias: dict | None) -> None:
        if not tendencias:
            lineas.append("No se generaron tendencias para este corpus.")
            return
        lineas.append(f"Granularidad: {tendencias.get('granularidad', 'N/D')}")
        lineas.extend(["", "| Categoria | Periodo | Noticias |", "|---|---|---:|"])
        for fila in tendencias.get("tabla", []):
            lineas.append(f"| {fila.get('categoria', 'N/D')} | {fila.get('periodo', 'N/D')} | {fila.get('noticias', 0)} |")
        conclusion = tendencias.get("conclusion")
        if conclusion:
            lineas.extend(["", str(conclusion)])

    def _agregar_consultas(self, lineas: list[str], consultas_busqueda: list[dict] | None) -> None:
        if not consultas_busqueda:
            lineas.append("No se registraron consultas de busqueda.")
            return
        for item in consultas_busqueda:
            lineas.append(f"### {item.get('consulta', 'Consulta')}")
            resultados = item.get("resultados", [])
            if not resultados:
                lineas.append("Sin resultados.")
            for resultado in resultados:
                score = resultado.get("score", resultado.get("relevancia", 0.0))
                lineas.append(
                    f"- [{self._fmt(score)}] {resultado.get('titulo', '')} "
                    f"({resultado.get('categoria', '?')}, {resultado.get('fecha', '')})"
                )

    def _agregar_chatbot(self, lineas: list[str], respuestas_chatbot: list[dict] | None) -> None:
        if not respuestas_chatbot:
            lineas.append("No se registraron respuestas del chatbot.")
            return
        for item in respuestas_chatbot:
            lineas.append(f"- Pregunta: {item.get('pregunta', '')}")
            lineas.append(f"  Respuesta: {item.get('respuesta', '')}")

    @staticmethod
    def _categoria(noticia: dict) -> str:
        return str(noticia.get("categoria_predicha") or noticia.get("categoria") or noticia.get("categoria_original") or "general")

    @staticmethod
    def _titulo(noticia: dict) -> str:
        return str(noticia.get("titulo") or noticia.get("title") or "Sin titulo")

    @staticmethod
    def _fecha(noticia: dict) -> str:
        return str(noticia.get("fecha") or noticia.get("fecha_publicacion") or "sin_fecha")

    @staticmethod
    def _valor(noticia: dict, campo: str) -> str:
        return str(noticia.get(campo) or "?")

    @staticmethod
    def _compound(noticia: dict) -> float | None:
        sentimiento = noticia.get("sentimiento")
        if not isinstance(sentimiento, dict):
            return None
        valor = sentimiento.get("compound", sentimiento.get("score"))
        try:
            return float(valor)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _etiqueta_sentimiento(noticia: dict) -> str | None:
        sentimiento = noticia.get("sentimiento")
        if not isinstance(sentimiento, dict):
            return None
        etiqueta = sentimiento.get("etiqueta") or sentimiento.get("label")
        return str(etiqueta) if etiqueta else None

    def _total_triples(self) -> int:
        if self.kg is None:
            return 0
        total = getattr(self.kg, "total_triples", None)
        if callable(total):
            try:
                return int(total())
            except (TypeError, ValueError):
                return 0
        return 0

    @staticmethod
    def _fmt(valor: object) -> str:
        try:
            return f"{float(valor):.3f}"
        except (TypeError, ValueError):
            return "N/D"

    @staticmethod
    def _escape(valor: object) -> str:
        return str(valor).replace("|", "\\|").replace("\n", " ")

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


def _serializable(valor: Any) -> Any:
    if is_dataclass(valor):
        return _serializable(asdict(valor))
    if isinstance(valor, Path):
        return str(valor)
    if isinstance(valor, dict):
        return {str(clave): _serializable(item) for clave, item in valor.items()}
    if isinstance(valor, (list, tuple, set)):
        return [_serializable(item) for item in valor]
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    if hasattr(valor, "__dict__"):
        return _serializable(vars(valor))
    return str(valor)
