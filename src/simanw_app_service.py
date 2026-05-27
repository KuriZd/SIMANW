from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from src.exportador import guardar_json
from src.fase1_service import Fase1Service
from src.fase2_service import Fase2Service
from src.fase3_service import Fase3Service
from src.fase4_service import Fase4Service
from src.fase5_service import Fase5Service
from src.fase6_service import Fase6Service
from src.fase7_service import Fase7Service


@dataclass
class SIMANWPipelineStatus:
    extraction: str = "pending"
    nlp: str = "pending"
    analysis: str = "pending"
    search: str = "pending"
    qa: str = "pending"
    graph: str = "pending"
    reports: str = "pending"


@dataclass
class SIMANWAppResult:
    noticias: list[dict]
    corpus_procesado: list[dict]
    analisis: dict
    resultados_busqueda: list[dict]
    respuesta_qa: str | None
    grafo_info: dict
    reporte_info: dict
    archivos_generados: list[str]
    estado_pipeline: SIMANWPipelineStatus
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    _grafo_obj: object | None = field(default=None, repr=False)

    @property
    def corpus(self) -> list[dict]:
        return self.corpus_procesado

    @property
    def estadisticas(self) -> dict:
        nlp_stats = self.analisis.get("nlp", {}) if isinstance(self.analisis, dict) else {}
        return nlp_stats if isinstance(nlp_stats, dict) else {}

    @property
    def rutas(self) -> dict[str, str]:
        return self.reporte_info.get("rutas", {})

    @property
    def pipeline_estado(self) -> dict[str, str]:
        return {
            "extraccion": self.estado_pipeline.extraction,
            "nlp": self.estado_pipeline.nlp,
            "analisis": self.estado_pipeline.analysis,
            "busqueda": self.estado_pipeline.search,
            "qa": self.estado_pipeline.qa,
            "grafo": self.estado_pipeline.graph,
            "reportes": self.estado_pipeline.reports,
        }


# Alias de compatibilidad con la UI previa.
ResultadoAnalisis = SIMANWAppResult


class SIMANWAppService:
    """Orquesta todas las fases internas para la app desktop."""

    PASOS = [
        "Loading news...",
        "Processing text...",
        "Analyzing sentiment and categories...",
        "Building search index...",
        "Preparing Q&A...",
        "Building knowledge graph...",
        "Generating reports...",
        "Done.",
    ]

    def __init__(self) -> None:
        self.fase1_service = Fase1Service()
        self.fase2_service = Fase2Service()
        self.fase3_service = Fase3Service()
        self.fase4_service = Fase4Service()
        self.fase5_service = Fase5Service()
        self.fase6_service = Fase6Service()
        self.fase7_service = Fase7Service()
        self.estado_actual: SIMANWAppResult | None = None
        self.motor_busqueda = None
        self.chatbot = None
        self.grafo = None
        self._eventos: list[dict] = []

    def analizar_noticias(
        self,
        source: str = "demo",
        url: str | None = None,
        fuente_id: str | None = None,
        archivo: str | None = None,
        on_progreso: Callable[[str], None] | None = None,
    ) -> SIMANWAppResult:
        errores: list[str] = []
        advertencias: list[str] = []
        archivos: list[str] = []
        rutas: dict[str, str] = {}
        status = SIMANWPipelineStatus()
        self._eventos = []

        def notify(index: int) -> None:
            mensaje = self.PASOS[index]
            self._eventos.append({"paso": index + 1, "mensaje": mensaje, "estado": "running"})
            if on_progreso:
                on_progreso(mensaje)

        noticias: list[dict] = []
        corpus: list[dict] = []
        analisis: dict = {}
        resultados_busqueda: list[dict] = []
        respuesta_qa: str | None = None
        grafo_info: dict = {"total_triples": 0, "formatos_exportados": [], "entidades": {}, "consultas_ejemplo": [], "errores": []}

        notify(0)
        try:
            noticias = self._cargar_noticias(source, url=url, fuente_id=fuente_id, archivo=archivo)
            rutas["noticias_json"] = str(self.fase1_service.exportar_json(noticias))
            rutas["noticias_csv"] = str(self.fase1_service.exportar_csv(noticias))
            archivos.extend([rutas["noticias_json"], rutas["noticias_csv"]])
            status.extraction = "completed"
        except Exception as exc:
            status.extraction = "error"
            errores.append(f"Extraction: {exc}")
            return self._resultado_parcial(noticias, corpus, analisis, resultados_busqueda, respuesta_qa, grafo_info, rutas, archivos, status, errores, advertencias)

        notify(1)
        try:
            resultado_f2 = self.fase2_service.procesar_corpus(noticias)
            corpus = resultado_f2.corpus
            analisis["nlp"] = resultado_f2.estadisticas
            advertencias.extend(resultado_f2.errores)
            rutas_proc = self.fase2_service.exportar_todo(corpus)
            rutas["corpus_json"] = str(rutas_proc["json"])
            rutas["corpus_csv"] = str(rutas_proc["csv"])
            archivos.extend([rutas["corpus_json"], rutas["corpus_csv"]])
            status.nlp = "partial" if resultado_f2.errores else "completed"
        except Exception as exc:
            status.nlp = "error"
            errores.append(f"NLP: {exc}")

        notify(2)
        if corpus:
            try:
                noticias, corpus, analisis_f3 = self.fase3_service.analizar(noticias, corpus)
                analisis.update(analisis_f3)
                errores.extend(analisis_f3.get("errores", []))
                advertencias.extend(analisis_f3.get("advertencias", []))
                ruta_analisis = self.fase3_service.exportar(analisis)
                rutas["analisis_json"] = str(ruta_analisis)
                archivos.append(str(ruta_analisis))
                ruta_t_csv = self.fase3_service.exportar_tendencias_csv(analisis)
                ruta_t_png = self.fase3_service.exportar_tendencias_png(analisis)
                if ruta_t_csv:
                    rutas["tendencias_csv"] = str(ruta_t_csv)
                    archivos.append(str(ruta_t_csv))
                if ruta_t_png:
                    rutas["tendencias_png"] = str(ruta_t_png)
                    archivos.append(str(ruta_t_png))
                guardar_json(corpus, "data/processed/corpus_procesado.json")
                status.analysis = "partial" if analisis_f3.get("errores") else "completed"
            except Exception as exc:
                status.analysis = "error"
                errores.append(f"Analysis: {exc}")

        notify(3)
        if corpus:
            try:
                self.fase4_service.construir_indice(corpus)
                self.motor_busqueda = self.fase4_service.motor
                resultados_busqueda = self.fase4_service.buscar("noticias tecnologia economia", top_k=5)
                status.search = "completed"
            except Exception as exc:
                status.search = "error"
                errores.append(f"Search: {exc}")

        notify(4)
        if corpus:
            try:
                self.fase5_service.preparar(corpus, self.motor_busqueda)
                self.chatbot = self.fase5_service
                respuesta_qa = self.fase5_service.responder("Dame un resumen del corpus")
                status.qa = "completed"
            except Exception as exc:
                status.qa = "error"
                errores.append(f"Q&A: {exc}")

        notify(5)
        if corpus:
            try:
                grafo_info = self.fase6_service.construir_grafo(corpus, analisis)
                ttl = self.fase6_service.exportar_ttl()
                jsonld = self.fase6_service.exportar_jsonld()
                rutas["grafo_ttl"] = str(ttl)
                rutas["grafo_jsonld"] = str(jsonld)
                archivos.extend([str(ttl), str(jsonld)])
                grafo_info["formatos_exportados"] = ["ttl", "jsonld"]
                self.grafo = self.fase6_service
                status.graph = "partial" if grafo_info.get("errores") else "completed"
                advertencias.extend(grafo_info.get("errores", []))
            except Exception as exc:
                status.graph = "error"
                errores.append(f"Graph: {exc}")

        notify(6)
        reporte_info = {"rutas": rutas}
        resultado = SIMANWAppResult(
            noticias=noticias,
            corpus_procesado=corpus,
            analisis=analisis,
            resultados_busqueda=resultados_busqueda,
            respuesta_qa=respuesta_qa,
            grafo_info=grafo_info,
            reporte_info=reporte_info,
            archivos_generados=list(dict.fromkeys(archivos)),
            estado_pipeline=status,
            errores=errores,
            advertencias=advertencias,
            _grafo_obj=self.fase6_service,
        )
        try:
            reporte = self.fase7_service.generar_reporte_final(resultado)
            resultado.archivos_generados.append(str(reporte))
            rutas["reporte_final"] = str(reporte)
            manifiesto = self.fase7_service.generar_manifiesto(resultado)
            log = self.fase7_service.generar_log_pipeline(self._eventos)
            resultado.archivos_generados.extend([str(manifiesto), str(log)])
            rutas["manifest"] = str(manifiesto)
            rutas["pipeline_log"] = str(log)
            status.reports = "completed"
        except Exception as exc:
            status.reports = "error"
            errores.append(f"Reports: {exc}")

        notify(7)
        resultado.archivos_generados = list(dict.fromkeys(resultado.archivos_generados))
        resultado.reporte_info["rutas"] = rutas
        self.estado_actual = resultado
        return resultado

    def buscar(self, consulta: str) -> list[dict]:
        if self.fase4_service is None:
            return []
        return self.fase4_service.buscar(consulta, top_k=10)

    def preguntar(self, pregunta: str) -> str:
        if self.fase5_service is None:
            return "No hay corpus cargado para responder."
        return self.fase5_service.responder(pregunta)

    def exportar_todo(self) -> dict[str, str]:
        if not self.estado_actual:
            return {}
        rutas: dict[str, str] = {}
        rutas["noticias_json"] = str(self.fase1_service.exportar_json(self.estado_actual.noticias))
        rutas["noticias_csv"] = str(self.fase1_service.exportar_csv(self.estado_actual.noticias))
        rutas_proc = self.fase2_service.exportar_todo(self.estado_actual.corpus_procesado)
        rutas["corpus_json"] = str(rutas_proc["json"])
        rutas["corpus_csv"] = str(rutas_proc["csv"])
        return rutas

    def _cargar_noticias(
        self,
        source: str,
        url: str | None = None,
        fuente_id: str | None = None,
        archivo: str | None = None,
    ) -> list[dict]:
        source_norm = (source or "demo").strip().lower()
        if source_norm in {"archivo", "file"}:
            ruta = Path(archivo or url or "")
            if not ruta.exists():
                raise ValueError(f"Archivo no encontrado: {ruta}")
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            if not isinstance(datos, list):
                raise ValueError("El archivo debe contener una lista de noticias.")
            noticias = [Fase1Service._normalizar_noticia(n, idx) for idx, n in enumerate(datos, start=1)]
            self.fase1_service.noticias = noticias
            return noticias
        if source_norm in {"predefinida", "predefined"}:
            return self.fase1_service.ejecutar_fuente_predefinida(fuente_id or url or "")
        resultado = self.fase1_service.ejecutar(source_norm, url or "")
        if resultado.errores:
            self._eventos.append({"paso": "extraction", "estado": "warning", "errores": resultado.errores})
        return resultado.noticias

    def _resultado_parcial(
        self,
        noticias: list[dict],
        corpus: list[dict],
        analisis: dict,
        resultados_busqueda: list[dict],
        respuesta_qa: str | None,
        grafo_info: dict,
        rutas: dict[str, str],
        archivos: list[str],
        status: SIMANWPipelineStatus,
        errores: list[str],
        advertencias: list[str],
    ) -> SIMANWAppResult:
        resultado = SIMANWAppResult(
            noticias=noticias,
            corpus_procesado=corpus,
            analisis=analisis,
            resultados_busqueda=resultados_busqueda,
            respuesta_qa=respuesta_qa,
            grafo_info=grafo_info,
            reporte_info={"rutas": rutas},
            archivos_generados=archivos,
            estado_pipeline=status,
            errores=errores,
            advertencias=advertencias,
            _grafo_obj=self.fase6_service,
        )
        self.estado_actual = resultado
        return resultado
