from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from src.exportador import guardar_json
from src.alertas_consulta import ConsultaGuardada, SistemaAlertasConsulta, consultas_demo
from src.analisis_discurso import AnalisisDiscurso, generar_nube_palabras
from src.analizador_hilo import AnalizadorHiloDiscusion, HILO_IA_ES, cargar_hilo_desde_json
from src.control_calidad import ControlCalidadCorpus
from src.fase1_service import Fase1Service
from src.fase2_service import Fase2Service
from src.fase3_service import Fase3Service
from src.fase4_service import Fase4Service
from src.fase5_service import Fase5Service
from src.fase6_service import Fase6Service
from src.fase7_service import Fase7Service
from src.knowledge_graph import (
    QUERY_AC13_AUTORES_PRODUCTIVOS,
    QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
    QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
)
from src.trazabilidad import TrazabilidadPipeline
from src.usabilidad import EstudioUsabilidad, estudio_demo


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
    evidencias_ac: dict[str, dict] = field(default_factory=dict)
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
        self.alertas_consulta = SistemaAlertasConsulta(consultas_demo())
        self._eventos: list[dict] = []

    def analizar_noticias(
        self,
        source: str = "demo",
        url: str | None = None,
        fuente_id: str | None = None,
        archivo: str | None = None,
        paginado_config: dict | None = None,
        limite_noticias: int | None = None,
        on_progreso: Callable[[str], None] | None = None,
    ) -> SIMANWAppResult:
        errores: list[str] = []
        advertencias: list[str] = []
        archivos: list[str] = []
        rutas: dict[str, str] = {}
        evidencias_ac: dict[str, dict] = {}
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
            noticias = self._cargar_noticias(
                source,
                url=url,
                fuente_id=fuente_id,
                archivo=archivo,
                paginado_config=paginado_config,
                limite_noticias=limite_noticias,
            )
            if not noticias:
                detalle = "; ".join(self.fase1_service.errores) or "La fuente no devolvio articulos con los selectores configurados."
                raise ValueError(f"No se extrajeron noticias en Fase 1. {detalle}")
            rutas["noticias_json"] = str(self.fase1_service.exportar_json(noticias))
            rutas["noticias_csv"] = str(self.fase1_service.exportar_csv(noticias))
            archivos.extend([rutas["noticias_json"], rutas["noticias_csv"]])
            if self.fase1_service.ultima_evidencia:
                evidencia = dict(self.fase1_service.ultima_evidencia)
                evidencia["ultima_ejecucion"] = datetime.now(timezone.utc).isoformat()
                evidencia["archivo_json"] = rutas["noticias_json"]
                evidencias_ac["AC-1"] = evidencia
            noticias, evidencia_ac8 = self._ejecutar_ac8(noticias)
            if evidencia_ac8:
                evidencias_ac["AC-8"] = evidencia_ac8
                for clave, ruta in evidencia_ac8.get("archivos", {}).items():
                    rutas[f"ac8_{clave}"] = ruta
                    archivos.append(ruta)
            status.extraction = "completed"
        except Exception as exc:
            status.extraction = "error"
            errores.append(f"Extraction: {exc}")
            return self._resultado_parcial(noticias, corpus, analisis, resultados_busqueda, respuesta_qa, grafo_info, rutas, archivos, status, errores, advertencias, evidencias_ac)

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
            evidencia_ac2 = self._generar_evidencia_ac2(corpus)
            if evidencia_ac2:
                evidencias_ac["AC-2"] = evidencia_ac2
                ruta_ac2 = evidencia_ac2.get("archivo_json")
                if ruta_ac2:
                    rutas["analisis_ac2_json"] = ruta_ac2
                    archivos.append(ruta_ac2)
                ruta_nube_ac2 = evidencia_ac2.get("archivo_nube")
                if ruta_nube_ac2:
                    rutas["nube_ac2_png"] = ruta_nube_ac2
                    archivos.append(ruta_nube_ac2)
            evidencia_ac4 = self._generar_evidencia_ac4(corpus)
            if evidencia_ac4:
                evidencias_ac["AC-4"] = evidencia_ac4
                ruta_ac4 = evidencia_ac4.get("archivo_json")
                if ruta_ac4:
                    rutas["analisis_ac4_json"] = ruta_ac4
                    archivos.append(ruta_ac4)
            status.nlp = "partial" if resultado_f2.errores else "completed"
        except Exception as exc:
            status.nlp = "error"
            errores.append(f"NLP: {exc}")

        notify(2)
        if corpus:
            try:
                noticias, corpus, analisis_f3 = self.fase3_service.analizar(noticias, corpus)
                analisis.update(analisis_f3)
                evidencia_ac3 = analisis_f3.get("clasificacion", {}).get("ac3", {})
                if evidencia_ac3:
                    evidencias_ac["AC-3"] = evidencia_ac3
                    ruta_ac3 = evidencia_ac3.get("archivo_json")
                    if ruta_ac3:
                        rutas["resultados_ac3_json"] = ruta_ac3
                        archivos.append(ruta_ac3)
                    for clave_ruta in ("modelo", "vectorizer"):
                        ruta_modelo = evidencia_ac3.get(clave_ruta)
                        if ruta_modelo:
                            rutas[f"ac3_{clave_ruta}"] = ruta_modelo
                            archivos.append(ruta_modelo)
                errores.extend(analisis_f3.get("errores", []))
                advertencias.extend(analisis_f3.get("advertencias", []))
                ruta_analisis = self.fase3_service.exportar(analisis)
                rutas["analisis_json"] = str(ruta_analisis)
                archivos.append(str(ruta_analisis))
                ruta_t_csv = self.fase3_service.exportar_tendencias_csv(analisis)
                ruta_t_png = self.fase3_service.exportar_tendencias_png(analisis)
                ruta_t_json = self.fase3_service.exportar_tendencias_json(analisis)
                ruta_t_md = self.fase3_service.exportar_tendencias_markdown(analisis)
                if ruta_t_csv:
                    rutas["tendencias_csv"] = str(ruta_t_csv)
                    archivos.append(str(ruta_t_csv))
                if ruta_t_png:
                    rutas["tendencias_png"] = str(ruta_t_png)
                    archivos.append(str(ruta_t_png))
                if ruta_t_json:
                    rutas["tendencias_json"] = str(ruta_t_json)
                    archivos.append(str(ruta_t_json))
                if ruta_t_md:
                    rutas["tendencias_conclusion_md"] = str(ruta_t_md)
                    archivos.append(str(ruta_t_md))
                evidencia_ac9 = self._generar_evidencia_ac9(
                    analisis,
                    ruta_t_csv,
                    ruta_t_png,
                    ruta_t_json,
                    ruta_t_md,
                )
                if evidencia_ac9:
                    evidencias_ac["AC-9"] = evidencia_ac9
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
                analisis["consulta_busqueda_reporte"] = "noticias tecnologia economia"
                evidencia_ac5 = self.fase4_service.evaluar_modelos_busqueda()
                if evidencia_ac5:
                    evidencias_ac["AC-5"] = {
                        "estado": evidencia_ac5.get("estado", "pendiente"),
                        "ultima_ejecucion": evidencia_ac5.get("ultima_ejecucion"),
                        "ejecutado_desde": evidencia_ac5.get("ejecutado_desde", "Search & Q&A"),
                        "total_documentos": evidencia_ac5.get("total_documentos", len(corpus)),
                        "total_consultas": evidencia_ac5.get("total_consultas", 0),
                        "ganador_f1": evidencia_ac5.get("ganador_f1"),
                        "ganador_map": evidencia_ac5.get("ganador_map"),
                        "map_booleano": evidencia_ac5.get("map_booleano"),
                        "map_vectorial": evidencia_ac5.get("map_vectorial"),
                        "origen_consultas": evidencia_ac5.get("origen_consultas"),
                        "criterio_relevancia": evidencia_ac5.get("criterio_relevancia"),
                        "archivo_json": evidencia_ac5.get("archivo_json"),
                        "observacion": evidencia_ac5.get("observacion"),
                    }
                    analisis["evaluacion_busqueda"] = evidencia_ac5
                    ruta_ac5 = evidencia_ac5.get("archivo_json")
                    if ruta_ac5:
                        rutas["resultados_ac5_json"] = ruta_ac5
                        archivos.append(ruta_ac5)
                status.search = "completed"
            except Exception as exc:
                status.search = "error"
                errores.append(f"Search: {exc}")

        if corpus:
            try:
                evidencia_ac10 = self._ejecutar_ac10(corpus)
                evidencias_ac["AC-10"] = evidencia_ac10
                for clave, ruta in evidencia_ac10.get("archivos", {}).items():
                    rutas[f"ac10_{clave}"] = ruta
                    archivos.append(ruta)
            except Exception as exc:
                advertencias.append(f"AC-10 alertas: {exc}")

        notify(4)
        if corpus:
            try:
                self.fase5_service.preparar(corpus, self.motor_busqueda)
                self.chatbot = self.fase5_service
                respuesta_qa = self.fase5_service.responder("Dame un resumen del corpus")
                self.fase5_service.responder("Que noticias hay de tecnologia?")
                self.fase5_service.responder("Cuentame mas sobre eso")
                evidencia_ac6 = self._generar_evidencia_ac6()
                evidencias_ac["AC-6"] = evidencia_ac6
                ruta_ac6 = evidencia_ac6.get("archivo_json")
                if ruta_ac6:
                    rutas["sesion_chatbot_ac6"] = ruta_ac6
                    archivos.append(ruta_ac6)
                status.qa = "completed"
            except Exception as exc:
                status.qa = "error"
                errores.append(f"Q&A: {exc}")

        try:
            evidencia_ac11 = self._ejecutar_ac11()
            evidencias_ac["AC-11"] = evidencia_ac11
            for clave, ruta in evidencia_ac11.get("archivos", {}).items():
                rutas[f"ac11_{clave}"] = ruta
                archivos.append(ruta)
        except Exception as exc:
            advertencias.append(f"AC-11 usabilidad: {exc}")

        notify(5)
        if corpus:
            try:
                grafo_info = self.fase6_service.construir_grafo(corpus, analisis)
                ttl = self.fase6_service.exportar_ttl()
                jsonld = self.fase6_service.exportar_jsonld()
                rutas["grafo_ttl"] = str(ttl)
                rutas["grafo_jsonld"] = str(jsonld)
                archivos.extend([str(ttl), str(jsonld)])
                evidencia_ac7 = grafo_info.get("evidencia_ac7", {})
                if evidencia_ac7:
                    evidencias_ac["AC-7"] = {
                        "estado": evidencia_ac7.get("estado", "pendiente"),
                        "ultima_ejecucion": evidencia_ac7.get("ultima_ejecucion"),
                        "ejecutado_desde": "Knowledge Graph",
                        "endpoint": evidencia_ac7.get("endpoint"),
                        "wikidata_online": evidencia_ac7.get("wikidata_online", False),
                        "modo": evidencia_ac7.get("modo", "offline"),
                        "entidades_evaluadas": evidencia_ac7.get("entidades_evaluadas"),
                        "total_enlaces_externos": evidencia_ac7.get("total_enlaces_externos"),
                        "triples_antes": evidencia_ac7.get("triples_antes"),
                        "triples_despues": evidencia_ac7.get("triples_despues"),
                        "archivo_ttl": evidencia_ac7.get("archivo_ttl"),
                        "archivo_json": evidencia_ac7.get("archivo_json"),
                        "observacion": evidencia_ac7.get("observacion"),
                        "errores": evidencia_ac7.get("errores", []),
                    }
                    if evidencia_ac7.get("archivo_ttl"):
                        rutas["kg_enriquecido_ac7_ttl"] = evidencia_ac7["archivo_ttl"]
                        archivos.append(evidencia_ac7["archivo_ttl"])
                    if evidencia_ac7.get("archivo_json"):
                        rutas["enlaces_wikidata_ac7_json"] = evidencia_ac7["archivo_json"]
                        archivos.append(evidencia_ac7["archivo_json"])
                grafo_info["formatos_exportados"] = ["ttl", "jsonld"]
                evidencia_ac13 = self.fase6_service.publicar_semanticamente()
                grafo_info["evidencia_ac13"] = evidencia_ac13
                evidencias_ac["AC-13"] = evidencia_ac13
                for clave, ruta in evidencia_ac13.get("archivos", {}).items():
                    rutas[f"ac13_{clave}"] = ruta
                    archivos.append(ruta)
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
            evidencias_ac=evidencias_ac,
        )
        try:
            reporte = self.fase7_service.generar_reporte_final(resultado)
            resultado.archivos_generados.append(str(reporte))
            rutas["reporte_final"] = str(reporte)
            reporte_json = self.fase7_service.generar_reporte_json(resultado)
            resultado.archivos_generados.append(str(reporte_json))
            rutas["reporte_final_json"] = str(reporte_json)
            manifiesto = self.fase7_service.generar_manifiesto(resultado)
            log = self.fase7_service.generar_log_pipeline(self._eventos_ac12(resultado))
            resultado.archivos_generados.extend([str(manifiesto), str(log)])
            rutas["manifest"] = str(manifiesto)
            rutas["pipeline_log"] = str(log)
            evidencia_ac12 = self._ejecutar_ac12(resultado, manifiesto, log)
            evidencias_ac["AC-12"] = evidencia_ac12
            for clave, ruta in evidencia_ac12.get("archivos", {}).items():
                rutas[f"ac12_{clave}"] = ruta
                resultado.archivos_generados.append(ruta)
            status.reports = "completed"
            evidencias_ac["Fase-7"] = {
                "estado": "completo",
                "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
                "ejecutado_desde": "Reports & Exports",
                "noticias_procesadas": len(resultado.noticias),
                "documentos_nlp": len(resultado.corpus_procesado),
                "triples_rdf": resultado.grafo_info.get("total_triples", 0),
                "archivo_markdown": str(reporte),
                "archivo_json": str(reporte_json),
                "manifest": str(manifiesto),
                "pipeline_log": str(log),
                "consulta_busqueda_reporte": analisis.get("consulta_busqueda_reporte", "sin consulta registrada"),
            }
            self.fase7_service.generar_reporte_final(resultado)
            self.fase7_service.generar_reporte_json(resultado)
        except Exception as exc:
            status.reports = "error"
            errores.append(f"Reports: {exc}")

        notify(7)
        if evidencias_ac:
            ruta_evidencia = guardar_json(evidencias_ac, "outputs/evidence/academic_evidence.json")
            resultado.archivos_generados.append(str(ruta_evidencia))
            rutas["academic_evidence"] = str(ruta_evidencia)
        resultado.archivos_generados = list(dict.fromkeys(resultado.archivos_generados))
        resultado.reporte_info["rutas"] = rutas
        self.estado_actual = resultado
        return resultado

    def buscar(self, consulta: str, modelo: str = "natural") -> list[dict]:
        if self.fase4_service is None:
            return []
        return self.fase4_service.buscar_con_modelo(consulta, modelo=modelo, top_k=10)

    def preguntar(self, pregunta: str) -> str:
        if self.fase5_service is None:
            return "No hay corpus cargado para responder."
        respuesta = self.fase5_service.responder(pregunta)
        if self.estado_actual is not None:
            evidencia = self._generar_evidencia_ac6()
            self.estado_actual.evidencias_ac["AC-6"] = evidencia
            ruta = evidencia.get("archivo_json")
            if ruta:
                self.estado_actual.reporte_info.setdefault("rutas", {})["sesion_chatbot_ac6"] = ruta
                self.estado_actual.archivos_generados.append(ruta)
                self.estado_actual.archivos_generados = list(dict.fromkeys(self.estado_actual.archivos_generados))
            guardar_json(self.estado_actual.evidencias_ac, "outputs/evidence/academic_evidence.json")
        return respuesta

    def ejecutar_alertas_guardadas(self) -> dict:
        if not self.estado_actual:
            return {}
        evidencia = self._ejecutar_ac10(self.estado_actual.corpus_procesado)
        self.estado_actual.evidencias_ac["AC-10"] = evidencia
        for ruta in evidencia.get("archivos", {}).values():
            if ruta:
                self.estado_actual.archivos_generados.append(ruta)
        self.estado_actual.archivos_generados = list(dict.fromkeys(self.estado_actual.archivos_generados))
        guardar_json(self.estado_actual.evidencias_ac, "outputs/evidence/academic_evidence.json")
        return evidencia

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

    def _generar_evidencia_ac6(self) -> dict:
        historial = self.fase5_service.obtener_historial()
        stats = self.fase5_service.estadisticas_contexto()
        respuestas_contextuales = [
            item for item in historial if item.get("tipo") == "contextual" or item.get("consulta_expandida")
        ]
        usa_memoria = bool(respuestas_contextuales)
        ruta = Path("data/sesion_chatbot_ac6.json")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        evidencia = {
            "actividad": "AC-6",
            "estado": "completo" if usa_memoria else "parcial",
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Search & Q&A",
            "interacciones": len(historial),
            "tiene_contexto": stats.get("tiene_contexto", False),
            "respuestas_contextuales": len(respuestas_contextuales),
            "temas_interes": stats.get("temas_interes", {}),
            "tipos_respuesta": stats.get("tipos_respuesta", {}),
            "ultima_consulta_expandida": stats.get("ultima_consulta_expandida", ""),
            "historial": historial,
            "archivo_json": str(ruta),
            "observacion": (
                "El chatbot expandio una pregunta de seguimiento usando la conversacion previa."
                if usa_memoria
                else "No se ha registrado una pregunta de seguimiento que use memoria contextual."
            ),
        }
        ruta.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2), encoding="utf-8")
        return evidencia

    def _ejecutar_ac8(self, noticias: list[dict]) -> tuple[list[dict], dict]:
        control = ControlCalidadCorpus()
        corpus_calidad = [self._normalizar_para_calidad(noticia, idx) for idx, noticia in enumerate(noticias, start=1)]
        depurado = control.validar(corpus_calidad)
        informe = control.generar_informe()
        ruta_informe = control.guardar_informe("data/ac8_informe_calidad.json")
        ruta_depurado = control.guardar_corpus_depurado("data/corpus_depurado_ac8.json")
        ruta_rechazados = control.guardar_rechazados("data/registros_rechazados_ac8.json")
        ruta_resumen = control.guardar_resumen_markdown("reports/resumen_calidad_ac8.md")

        if depurado:
            noticias_depuradas = [self._restaurar_desde_calidad(noticia) for noticia in depurado]
        else:
            noticias_depuradas = noticias

        estado = "completo" if depurado else "parcial"
        evidencia = {
            "actividad": "AC-8",
            "estado": estado,
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Load / Analyze News",
            "total_registros": informe["total_registros"],
            "registros_validos": informe["registros_validos"],
            "registros_rechazados": informe["registros_rechazados"],
            "duplicados_exactos": informe["duplicados_exactos_url"],
            "duplicados_casi_identicos": informe["duplicados_casi_identicos_titulo"],
            "explicacion_descartes": control.parrafo_resumen(),
            "archivos": {
                "informe_json": str(ruta_informe),
                "corpus_depurado": str(ruta_depurado),
                "rechazados": str(ruta_rechazados),
                "resumen_md": str(ruta_resumen),
            },
            "archivo_json": str(ruta_informe),
        }
        if not depurado:
            evidencia["observacion"] = "El control de calidad no produjo corpus valido; se continuo con el corpus original para no romper el pipeline."
        return noticias_depuradas, evidencia

    def _generar_evidencia_ac9(
        self,
        analisis: dict,
        ruta_csv: Path | None,
        ruta_png: Path | None,
        ruta_json: Path | None = None,
        ruta_markdown: Path | None = None,
    ) -> dict | None:
        tendencias = analisis.get("tendencias", {}) if isinstance(analisis, dict) else {}
        if not tendencias:
            return None
        tabla = tendencias.get("tabla", [])
        temas = sorted({fila.get("categoria", "") for fila in tabla if fila.get("categoria")})
        pico = tendencias.get("pico", {})
        conclusion = str(tendencias.get("conclusion", ""))
        tendencias_terminos = tendencias.get("tendencias_terminos", {})
        temas_con_cambios = [
            tema
            for tema, data in tendencias_terminos.items()
            if data.get("aumentan") or data.get("disminuyen")
        ]
        return {
            "actividad": "AC-9",
            "estado": "completo" if tabla and len(temas) >= 3 and pico.get("titulos") else "parcial",
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Smart Results",
            "granularidad": tendencias.get("granularidad", "mes"),
            "justificacion_granularidad": (
                "Se usa agrupación mensual para corpus de tamaño medio porque conserva periodos "
                "comparables sin fragmentar excesivamente las noticias; semana queda disponible "
                "para corpus de alta frecuencia."
            ),
            "temas_analizados": temas,
            "total_temas": len(temas),
            "tendencias_terminos": tendencias_terminos,
            "temas_con_cambios_lexicos": len(temas_con_cambios),
            "pico_notable": pico,
            "conclusion_breve": conclusion[:500],
            "archivo_csv": str(ruta_csv) if ruta_csv else "",
            "archivo_png": str(ruta_png) if ruta_png else "",
            "archivo_json": str(ruta_json) if ruta_json else "",
            "archivo_markdown": str(ruta_markdown) if ruta_markdown else "",
            "archivos": {
                "csv": str(ruta_csv) if ruta_csv else "",
                "png": str(ruta_png) if ruta_png else "",
                "json": str(ruta_json) if ruta_json else "",
                "conclusion_md": str(ruta_markdown) if ruta_markdown else "",
            },
        }

    def _ejecutar_ac10(self, corpus: list[dict]) -> dict:
        consultas, origen_consultas = self._cargar_consultas_ac10()
        sistema = SistemaAlertasConsulta(consultas)
        sin_noticias = sistema.procesar_noticias_nuevas([])
        noticias_alertas = [self._noticia_para_alerta(item, idx) for idx, item in enumerate(corpus, start=1)]
        alertas = sistema.procesar_noticias_nuevas(noticias_alertas)
        repetidas = sistema.procesar_noticias_nuevas(noticias_alertas)
        duplicadas_evitadas = max(len(alertas) - len(repetidas), 0)
        self.alertas_consulta = sistema

        ruta_consultas = sistema.guardar_consultas("data/ac10_consultas_guardadas.json")
        ruta_historial = sistema.guardar_historial("data/ac10_historial_alertas.json")
        ruta_reporte = sistema.guardar_reporte_markdown("reports/alertas_ac10.md")
        estado = "completo" if alertas else "parcial"
        if origen_consultas != "archivo_configurado":
            estado = "parcial"
        return {
            "actividad": "AC-10",
            "estado": estado,
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Search & Q&A",
            "origen_consultas": origen_consultas,
            "consultas_reales": origen_consultas == "archivo_configurado",
            "consultas_guardadas": [consulta.nombre for consulta in sistema.consultas],
            "numero_consultas": len(sistema.consultas),
            "historial_alertas": len(sistema.historial_alertas),
            "alertas_generadas": len(alertas),
            "alertas_primera_ejecucion": len(alertas),
            "alertas_segunda_ejecucion": len(repetidas),
            "alertas_duplicadas_evitadas": duplicadas_evitadas,
            "ejecucion_sin_noticias_nuevas": len(sin_noticias),
            "ejecucion_con_noticias_nuevas": len(alertas),
            "noticias_procesadas_sin_nuevas": 0,
            "noticias_procesadas_con_nuevas": len(noticias_alertas),
            "duplicados_documentados": True,
            "deduplicacion": sistema.documentar_deduplicacion(),
            "archivos": {
                "consultas": str(ruta_consultas),
                "historial": str(ruta_historial),
                "reporte_md": str(ruta_reporte),
            },
            "archivo_json": str(ruta_historial),
        }

    def _ejecutar_ac11(self) -> dict:
        estudio, origen = self._cargar_estudio_usabilidad()
        ruta_csv = estudio.exportar_csv("data/ac11_resultados_usabilidad.csv")
        ruta_reporte = estudio.guardar_reporte_markdown("reports/usabilidad_ac11.md")
        ruta_reflexion = estudio.guardar_reflexion_etica("reports/reflexion_etica_ac11.md")
        participantes = len(estudio.participantes)
        datos_reales = origen == "archivo_real"
        estado = "completo" if datos_reales and participantes >= 3 else "parcial"
        return {
            "actividad": "AC-11",
            "estado": estado,
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Academic Evidence / Reports & Exports",
            "participantes": participantes,
            "datos": "reales_anonimizados" if datos_reales else "demo",
            "tareas": estudio.tareas,
            "items_cuestionario": estudio.items,
            "promedios": estudio.promedios() if participantes else {},
            "problemas_detectados": [item["problema"] for item in estudio.problemas_y_mejoras()],
            "mejoras_propuestas": [item["mejora"] for item in estudio.problemas_y_mejoras()],
            "reflexion_consentimiento": estudio.reflexion_consentimiento(),
            "observacion": "" if datos_reales else "No se encontro data/usabilidad_participantes.json; se reporta evidencia demo y queda pendiente evidencia humana real.",
            "archivos": {
                "csv": str(ruta_csv),
                "reporte_md": str(ruta_reporte),
                "reflexion_md": str(ruta_reflexion),
            },
            "archivo_json": "",
        }

    def _ejecutar_ac12(self, resultado: SIMANWAppResult, manifiesto: Path, log: Path) -> dict:
        rutas = resultado.reporte_info.get("rutas", {})
        fuente_noticias = (
            rutas.get("noticias_json")
            or rutas.get("ac8_corpus_depurado")
            or rutas.get("corpus_json")
            or "fuente-no-registrada"
        )
        traza = TrazabilidadPipeline(fuente_noticias)
        checklist = traza.guardar_checklist("reports/checklist_ac12.md", "KuriZd")
        limitaciones = traza.guardar_limitaciones("reports/limitaciones_ac12.md")
        documentos_por_etapa = {
            "extraccion": len(resultado.noticias),
            "nlp": len(resultado.corpus_procesado),
            "analisis": len(resultado.corpus_procesado) if resultado.analisis else 0,
            "busqueda": len(resultado.resultados_busqueda),
            "grafo": int(resultado.grafo_info.get("total_triples", 0) or 0),
            "reporte": 1,
        }
        return {
            "actividad": "AC-12",
            "estado": "completo",
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Reports & Exports",
            "fecha_hora": datetime.now(timezone.utc).isoformat(),
            "version_proyecto": traza.version_proyecto,
            "fuente_noticias": traza.fuente_noticias,
            "documentos_por_etapa": documentos_por_etapa,
            "archivos_salida": dict(resultado.rutas),
            "log_estructurado": str(log),
            "checklist": str(checklist),
            "limitaciones": str(limitaciones),
            "archivos": {
                "manifest": str(manifiesto),
                "log": str(log),
                "checklist": str(checklist),
                "limitaciones": str(limitaciones),
            },
            "archivo_json": str(manifiesto),
        }

    @staticmethod
    def _eventos_ac12(resultado: SIMANWAppResult) -> list[dict]:
        rutas = resultado.reporte_info.get("rutas", {})
        ahora = datetime.now(timezone.utc).isoformat()
        eventos = [
            {
                "etapa": "rastreo",
                "documentos_entrada": 0,
                "documentos_salida": len(resultado.noticias),
                "artefacto": rutas.get("noticias_json", ""),
                "marca_tiempo": ahora,
                "estado": resultado.estado_pipeline.extraction,
            },
            {
                "etapa": "procesamiento",
                "documentos_entrada": len(resultado.noticias),
                "documentos_salida": len(resultado.corpus_procesado),
                "artefacto": rutas.get("corpus_json", ""),
                "marca_tiempo": ahora,
                "estado": resultado.estado_pipeline.nlp,
            },
            {
                "etapa": "analisis",
                "documentos_entrada": len(resultado.corpus_procesado),
                "documentos_salida": len(resultado.corpus_procesado) if resultado.analisis else 0,
                "artefacto": rutas.get("analisis_json", ""),
                "marca_tiempo": ahora,
                "estado": resultado.estado_pipeline.analysis,
            },
            {
                "etapa": "busqueda",
                "documentos_entrada": len(resultado.corpus_procesado),
                "documentos_salida": len(resultado.resultados_busqueda),
                "artefacto": rutas.get("resultados_ac5_json", "indice_busqueda_en_memoria"),
                "marca_tiempo": ahora,
                "estado": resultado.estado_pipeline.search,
            },
            {
                "etapa": "grafo",
                "documentos_entrada": len(resultado.corpus_procesado),
                "documentos_salida": int(resultado.grafo_info.get("total_triples", 0) or 0),
                "artefacto": rutas.get("grafo_ttl", ""),
                "marca_tiempo": ahora,
                "estado": resultado.estado_pipeline.graph,
            },
            {
                "etapa": "reporte",
                "documentos_entrada": len(resultado.corpus_procesado),
                "documentos_salida": 1 if rutas.get("reporte_final") else 0,
                "artefacto": rutas.get("reporte_final", ""),
                "marca_tiempo": ahora,
                "estado": resultado.estado_pipeline.reports,
            },
        ]
        return eventos

    def _generar_evidencia_ac2(self, corpus: list[dict]) -> dict:
        textos = [
            {"titulo": item.get("titulo", f"Documento {idx + 1}"), "texto": item.get("texto_original", "")}
            for idx, item in enumerate(corpus)
            if len((item.get("texto_original") or "").split()) >= 20
        ]
        if not textos and corpus:
            textos = [
                {"titulo": item.get("titulo", f"Documento {idx + 1}"), "texto": item.get("texto_original", "")}
                for idx, item in enumerate(corpus[:3])
                if (item.get("texto_original") or "").strip()
            ]
        if not textos:
            return {
                "estado": "pendiente",
                "ejecutado_desde": "Smart Results",
                "observacion": "No hubo textos suficientes para analisis de discurso.",
            }

        analizador = AnalisisDiscurso()
        analisis_textos = [analizador.analizar(item["texto"], item["titulo"]) for item in textos[:5]]
        comparativa = analizador.comparar_textos(analisis_textos)
        ruta = "data/analisis_ac2.json"
        ruta_nube = "data/nube_ac2.png"
        tokens_nube = [
            token
            for analisis in analisis_textos
            for token in analisis.get("_tokens_filtrados", [])
        ]
        nube_generada = generar_nube_palabras(tokens_nube, ruta_nube) if tokens_nube else False
        AnalisisDiscurso.guardar_json(ruta, analisis_textos, comparativa)
        total_unigramas = sum(len(a.get("top_unigramas", [])) for a in analisis_textos)
        total_bigramas = sum(len(a.get("top_bigramas", [])) for a in analisis_textos)
        total_trigramas = sum(len(a.get("top_trigramas", [])) for a in analisis_textos)
        return {
            "estado": "completo" if analisis_textos else "pendiente",
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ejecutado_desde": "Smart Results",
            "textos_analizados": len(analisis_textos),
            "unigramas": total_unigramas,
            "bigramas": total_bigramas,
            "trigramas": total_trigramas,
            "riqueza_promedio": round(
                sum(a.get("riqueza_lexica_global", 0.0) for a in analisis_textos) / max(len(analisis_textos), 1),
                4,
            ),
            "archivo_json": ruta,
            "archivo_nube": ruta_nube if nube_generada else "",
            "nube_generada": nube_generada,
        }

    def _generar_evidencia_ac4(self, corpus: list[dict]) -> dict:
        ruta_hilo = Path("data/hilo_discusion.json")
        origen = "archivo_real" if ruta_hilo.exists() else "hilo_simulado"
        try:
            if ruta_hilo.exists():
                mensajes = cargar_hilo_desde_json(ruta_hilo)
            else:
                mensajes = [dict(mensaje) for mensaje in HILO_IA_ES]
                if not mensajes:
                    origen = "corpus_derivado"
                    mensajes = self._mensajes_desde_corpus(corpus)
            if not mensajes:
                return {
                    "actividad": "AC-4",
                    "estado": "pendiente",
                    "ejecutado_desde": "Smart Results",
                    "origen_datos": origen,
                    "observacion": "No hay mensajes o noticias suficientes para analizar un hilo.",
                }

            analizador = AnalizadorHiloDiscusion(idioma="spanish")
            analizador.cargar_hilo(mensajes)
            resumen = analizador.resumen_hilo()
            evolucion = analizador.evolucion_sentimiento(ventana=3)
            subtemas = analizador.detectar_subtemas(n_clusters=min(3, max(1, len(mensajes))))
            resumen_textual = analizador.generar_resumen_textual()
            ruta = Path("data/analisis_ac4.json")
            analizador.guardar_json(ruta)
            estado = "completo" if origen in {"archivo_real", "hilo_simulado"} and len(mensajes) >= 8 else "parcial"
            observacion = ""
            if origen == "hilo_simulado":
                observacion = (
                    "Se uso un hilo simulado de discusion sobre IA porque no existe data/hilo_discusion.json. "
                    "El requisito AC-4 permite rastreo o simulacion de hilo."
                )
            elif estado != "completo":
                observacion = "No hay mensajes suficientes para defender AC-4 como completo."
            return {
                "actividad": "AC-4",
                "estado": estado,
                "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
                "ejecutado_desde": "Smart Results",
                "origen_datos": origen,
                "total_mensajes": resumen.get("total_mensajes", 0),
                "participantes": resumen.get("participantes", 0),
                "tono": resumen.get("tono", "mixto"),
                "sentimiento_promedio": resumen.get("sentimiento_promedio", 0.0),
                "subtemas_detectados": len(subtemas),
                "evolucion_puntos": len(evolucion),
                "resumen_textual": resumen_textual,
                "hashtags_top": resumen.get("hashtags_top", []),
                "usuarios_activos": resumen.get("usuarios_activos", []),
                "archivo_json": str(ruta),
                "observacion": observacion,
            }
        except Exception as exc:
            return {
                "actividad": "AC-4",
                "estado": "parcial",
                "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
                "ejecutado_desde": "Smart Results",
                "origen_datos": origen,
                "observacion": f"No se pudo analizar AC-4: {exc}",
            }

    @staticmethod
    def _normalizar_para_calidad(noticia: dict, indice: int) -> dict:
        url = str(noticia.get("url") or f"https://simanw.local/noticia/{indice}").strip()
        fuente = str(noticia.get("fuente") or noticia.get("fuente_nombre") or "").strip()
        if not fuente:
            parsed = urlparse(url)
            fuente = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "https://simanw.local"
        if not fuente.startswith(("http://", "https://")):
            fuente = f"https://{fuente.strip('/')}"
        return {
            **noticia,
            "titulo": str(noticia.get("titulo") or f"Noticia {indice}").strip(),
            "cuerpo": str(noticia.get("cuerpo") or noticia.get("resumen") or noticia.get("texto_original") or "").strip(),
            "fecha": str(noticia.get("fecha") or "2026-01-01").strip()[:10],
            "autor": str(noticia.get("autor") or "Autor desconocido").strip(),
            "categoria_original": str(
                noticia.get("categoria_original") or noticia.get("categoria") or noticia.get("categoria_predicha") or "general"
            ).strip(),
            "url": url,
            "fuente": fuente,
        }

    @staticmethod
    def _restaurar_desde_calidad(noticia: dict) -> dict:
        restaurada = dict(noticia)
        restaurada["categoria"] = noticia.get("categoria") or noticia.get("categoria_original") or "general"
        return restaurada

    @staticmethod
    def _noticia_para_alerta(item: dict, indice: int) -> dict:
        return {
            "id": item.get("id", indice),
            "titulo": item.get("titulo", f"Documento {indice}"),
            "cuerpo": item.get("cuerpo") or item.get("texto_original") or item.get("texto_limpio") or "",
            "url": item.get("url") or f"https://simanw.local/alertas/{indice}",
        }

    @staticmethod
    def _mensajes_desde_corpus(corpus: list[dict]) -> list[dict]:
        mensajes: list[dict] = []
        for indice, item in enumerate(corpus[:20], start=1):
            texto = " ".join(
                str(item.get(campo, "") or "")
                for campo in ("titulo", "texto_original", "cuerpo", "texto_limpio")
            ).strip()
            if not texto:
                continue
            mensajes.append(
                {
                    "usuario": item.get("autor") or item.get("fuente") or f"fuente_{indice}",
                    "texto": texto[:500],
                    "timestamp": str(item.get("fecha") or indice),
                }
            )
        return mensajes

    @staticmethod
    def _cargar_estudio_usabilidad() -> tuple[EstudioUsabilidad, str]:
        ruta = Path("data/usabilidad_participantes.json")
        if not ruta.exists():
            ruta_csv = Path("data/usabilidad_participantes.csv")
            if ruta_csv.exists():
                import csv

                estudio = EstudioUsabilidad()
                with ruta_csv.open("r", encoding="utf-8", newline="") as archivo:
                    for fila in csv.DictReader(archivo):
                        codigo = str(fila.get("participante") or fila.get("codigo") or "P?")
                        respuestas = {
                            item: int(fila[item])
                            for item in estudio.items
                            if str(fila.get(item, "")).strip()
                        }
                        problemas_raw = str(fila.get("problemas") or "").strip()
                        problemas = [p.strip() for p in problemas_raw.split("|") if p.strip()]
                        estudio.registrar_participante(codigo, respuestas, problemas)
                return estudio, "archivo_real"
            return estudio_demo(), "demo"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        estudio = EstudioUsabilidad()
        if not isinstance(datos, list):
            raise ValueError("data/usabilidad_participantes.json debe contener una lista de participantes.")
        for item in datos:
            estudio.registrar_participante(
                str(item.get("participante") or item.get("codigo") or "P?"),
                dict(item.get("respuestas", {})),
                list(item.get("problemas", [])),
            )
        return estudio, "archivo_real"

    @staticmethod
    def _cargar_consultas_ac10() -> tuple[list[ConsultaGuardada], str]:
        rutas = [
            (Path("config/consultas_ac10.json"), "archivo_configurado"),
            (Path("data/ac10_consultas_guardadas.json"), "archivo_guardado"),
        ]
        for ruta, origen in rutas:
            if not ruta.exists() or ruta.stat().st_size == 0:
                continue
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(datos, list):
                continue
            consultas: list[ConsultaGuardada] = []
            for item in datos:
                if not isinstance(item, dict):
                    continue
                nombre = str(item.get("nombre") or item.get("consulta") or "").strip()
                expresion = str(item.get("expresion") or item.get("query") or "").strip()
                fecha = str(item.get("fecha_creacion") or datetime.now(timezone.utc).isoformat())
                if nombre and expresion:
                    consultas.append(ConsultaGuardada(nombre, expresion, fecha))
            if consultas:
                return consultas, origen
        return consultas_demo(), "plantilla_demo"

    def _cargar_noticias(
        self,
        source: str,
        url: str | None = None,
        fuente_id: str | None = None,
        archivo: str | None = None,
        paginado_config: dict | None = None,
        limite_noticias: int | None = None,
    ) -> list[dict]:
        limite = max(int(limite_noticias or 0), 1) if limite_noticias else None
        source_norm = (source or "demo").strip().lower()
        if source_norm in {"archivo", "file"}:
            ruta = Path(archivo or url or "")
            if not ruta.exists():
                raise ValueError(f"Archivo no encontrado: {ruta}")
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            if not isinstance(datos, list):
                raise ValueError("El archivo debe contener una lista de noticias.")
            noticias = [Fase1Service._normalizar_noticia(n, idx) for idx, n in enumerate(datos, start=1)]
            if limite:
                noticias = noticias[:limite]
            self.fase1_service.noticias = noticias
            return noticias
        if source_norm in {"predefinida", "predefined"}:
            return self.fase1_service.ejecutar_fuente_predefinida(fuente_id or url or "", limite_noticias=limite)
        if source_norm == "paginado" and paginado_config:
            resultado = self.fase1_service.ejecutar_paginado_configurado(paginado_config)
            if resultado.errores:
                self._eventos.append({"paso": "extraction", "estado": "warning", "errores": resultado.errores})
            return resultado.noticias
        resultado = self.fase1_service.ejecutar(source_norm, url or "", limite_noticias=limite)
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
        evidencias_ac: dict[str, dict] | None = None,
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
            evidencias_ac=evidencias_ac or {},
            _grafo_obj=self.fase6_service,
        )
        self.estado_actual = resultado
        return resultado
