from __future__ import annotations

import json
from pathlib import Path

import customtkinter as ctk

from src.simanw_app_service import ResultadoAnalisis, SIMANWAppService, SIMANWPipelineStatus
from src.tendencias_temporales import TendenciasTemporales
from src.ui.content_header import ContentHeaderFrame
from src.ui.seccion_busqueda import SeccionBusquedaQA
from src.ui.seccion_cargar import SeccionCargar
from src.ui.seccion_dashboard import SeccionDashboard
from src.ui.seccion_evidencia import SeccionEvidencia
from src.ui.seccion_explorador import SeccionExplorador
from src.ui.seccion_exportar import SeccionExportar
from src.ui.seccion_grafo import SeccionGrafo
from src.ui.seccion_resultados import SeccionResultados
from src.ui.sidebar import SidebarFrame
from src.ui.status_bar import StatusBarFrame
from src.ui_theme import FONT_BODY, FONT_H1, THEME


class PlaceholderFrame(ctk.CTkFrame):
    def __init__(self, master, nombre: str) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        panel = ctk.CTkFrame(self, fg_color=THEME["bg_surface"], corner_radius=8)
        panel.grid(row=0, column=0, padx=18, pady=18, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text=nombre, font=FONT_H1, text_color=THEME["text_1"]).grid(
            row=0, column=0, pady=(28, 4)
        )
        ctk.CTkLabel(panel, text="Module reserved.", font=FONT_BODY, text_color=THEME["text_2"]).grid(
            row=1, column=0
        )


_SECTION_META: dict[str, tuple[str, str]] = {
    "dashboard": ("Dashboard", "Operational summary of the current news corpus."),
    "cargar": ("Load / Analyze News", "Select a source and run the complete SIMANW pipeline."),
    "resultados": ("Smart Results", "Categories, sentiment, frequent terms and NLP evidence."),
    "explorador": ("News Explorer", "Browse analyzed news and document details."),
    "busqueda": ("Search & Q&A", "Search the corpus and ask questions grounded in loaded news."),
    "grafo": ("Knowledge Graph", "RDF/SPARQL graph generated from the corpus."),
    "exportar": ("Reports & Exports", "Generated files and re-export actions."),
    "evidencia": ("Academic Evidence", "Internal phase status, warnings, errors and artifacts."),
}


class SIMANWDesktopApp(ctk.CTk):
    """Desktop application shell. Business logic lives in service classes."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        super().__init__(fg_color=THEME["bg_base"])
        self.title("SIMANW - Monitor de Noticias Web")
        self.geometry("1220x760")
        self.minsize(1040, 640)

        self.current_content: ctk.CTkFrame | None = None
        self.total_noticias = 0
        self.simanw_service = SIMANWAppService()
        self.resultado_actual: ResultadoAnalisis | None = None
        self.load_form_state: dict = {}

        self.noticias: list[dict] = []
        self.corpus_procesado: list[dict] = []
        self.estadisticas_fase2: dict = {}
        self.analisis: dict = {}
        self.grafo_info: dict = {}
        self.rutas_exportacion: dict = {}
        self.pipeline_estado: dict = {}

        self._build_layout()
        self._precargar_datos_previos()
        self.show_section("cargar")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar = SidebarFrame(self, self.show_section)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsw")

        self.header = ContentHeaderFrame(self)
        self.header.grid(row=0, column=1, sticky="ew")

        self.content_host = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        self.content_host.grid(row=1, column=1, sticky="nsew")
        self.content_host.grid_columnconfigure(0, weight=1)
        self.content_host.grid_rowconfigure(0, weight=1)

        self.status_bar = StatusBarFrame(self)
        self.status_bar.grid(row=2, column=1, sticky="ew")

    def show_section(self, section_id: str) -> None:
        if self.current_content is not None:
            if isinstance(self.current_content, SeccionCargar):
                self.load_form_state = self.current_content.get_form_state()
            self.current_content.destroy()

        titulo, desc = _SECTION_META.get(section_id, ("Module", "Not available."))
        self.header.set_content(titulo, desc)

        if section_id == "cargar":
            self.current_content = SeccionCargar(self.content_host, root_app=self)
        elif section_id == "dashboard":
            self.current_content = SeccionDashboard(self.content_host, root_app=self)
        elif section_id == "explorador":
            self.current_content = SeccionExplorador(self.content_host, root_app=self)
        elif section_id == "resultados":
            self.current_content = SeccionResultados(self.content_host, root_app=self)
        elif section_id == "busqueda":
            self.current_content = SeccionBusquedaQA(self.content_host, root_app=self)
        elif section_id == "grafo":
            self.current_content = SeccionGrafo(self.content_host, root_app=self)
        elif section_id == "exportar":
            self.current_content = SeccionExportar(self.content_host, root_app=self)
        elif section_id == "evidencia":
            self.current_content = SeccionEvidencia(self.content_host, root_app=self)
        else:
            self.current_content = PlaceholderFrame(self.content_host, titulo)

        self.current_content.grid(row=0, column=0, sticky="nsew")
        self.hide_progress()
        self.sidebar.set_active(section_id)

        if not self.noticias and section_id not in ("cargar",):
            self.set_estado("No data loaded. Run Load / Analyze News first.", "warning", total_noticias=0)
        else:
            self.set_estado(f"{titulo} ready.", "ok", total_noticias=self.total_noticias)

    def set_resultado_analisis(self, resultado: ResultadoAnalisis) -> None:
        self.resultado_actual = resultado
        self.noticias = resultado.noticias
        self.total_noticias = len(resultado.noticias)
        self.corpus_procesado = resultado.corpus
        self.estadisticas_fase2 = resultado.estadisticas
        self.analisis = resultado.analisis
        self.grafo_info = resultado.grafo_info
        self.rutas_exportacion = resultado.rutas
        self.pipeline_estado = resultado.pipeline_estado

    def set_noticias(self, noticias: list[dict]) -> None:
        self.noticias = noticias
        self.total_noticias = len(noticias)

    def set_corpus(self, corpus: list[dict], estadisticas: dict) -> None:
        self.corpus_procesado = corpus
        self.estadisticas_fase2 = estadisticas

    def set_estado(self, mensaje: str, nivel: str = "ok", total_noticias: int | None = None) -> None:
        if total_noticias is not None:
            self.total_noticias = total_noticias
        self.status_bar.set_estado(mensaje, nivel, total_noticias=self.total_noticias)

    def show_progress(self) -> None:
        self.header.show_progress()

    def hide_progress(self) -> None:
        self.header.hide_progress()

    def _precargar_datos_previos(self) -> None:
        noticias = self._leer_lista_json(Path("data/noticias_extraidas.json"))
        corpus = self._leer_lista_json(Path("data/processed/corpus_procesado.json"))
        if not noticias and not corpus:
            return
        if not corpus:
            corpus = [_corpus_minimo(noticia) for noticia in noticias]
        if not noticias:
            noticias = [_noticia_desde_corpus(item) for item in corpus]

        estadisticas = _estadisticas_precargadas(corpus)
        analisis_extra, rutas_extra, archivos_extra, evidencias_extra, grafo_info = self._generar_artefactos_precargados(
            noticias,
            corpus,
        )
        rutas = {
            "noticias_json": "data/noticias_extraidas.json",
            "noticias_csv": "data/noticias_extraidas.csv",
            "corpus_json": "data/processed/corpus_procesado.json",
            "corpus_csv": "data/processed/corpus_procesado.csv",
        }
        rutas.update(rutas_extra)
        archivos = [ruta for ruta in rutas.values() if Path(ruta).exists()]
        archivos.extend(archivos_extra)
        pipeline = SIMANWPipelineStatus(
            extraction="completed" if noticias else "pending",
            nlp="completed" if corpus else "pending",
            analysis="partial" if analisis_extra else "pending",
            search="completed",
            qa="completed",
            graph="completed" if grafo_info and not grafo_info.get("errores") else "warning" if grafo_info else "pending",
            reports="pending",
        )
        resultado = ResultadoAnalisis(
            noticias=noticias,
            corpus_procesado=corpus,
            analisis={"nlp": estadisticas, **analisis_extra},
            resultados_busqueda=[],
            respuesta_qa=None,
            grafo_info=grafo_info,
            reporte_info={"rutas": rutas},
            archivos_generados=archivos,
            estado_pipeline=pipeline,
            advertencias=["Datos precargados desde archivos locales; ejecuta Load para refrescar el pipeline completo."],
            evidencias_ac=evidencias_extra,
        )
        self.simanw_service.fase1_service.noticias = noticias
        self.simanw_service.fase2_service.corpus = corpus
        try:
            self.simanw_service.fase4_service.construir_indice(corpus)
            self.simanw_service.motor_busqueda = self.simanw_service.fase4_service.motor
            self.simanw_service.fase5_service.preparar(corpus, self.simanw_service.motor_busqueda)
        except Exception as exc:
            resultado.advertencias.append(f"No se pudo reconstruir busqueda/Q&A precargada: {exc}")
            resultado.estado_pipeline.search = "warning"
            resultado.estado_pipeline.qa = "warning"
        self.simanw_service.estado_actual = resultado
        self.set_resultado_analisis(resultado)
        self.set_estado(
            f"Datos previos precargados: {len(noticias)} noticias",
            "ok",
            total_noticias=len(noticias),
        )

    def _generar_artefactos_precargados(
        self,
        noticias: list[dict],
        corpus: list[dict],
    ) -> tuple[dict, dict[str, str], list[str], dict[str, dict], dict]:
        analisis: dict = {}
        rutas: dict[str, str] = {}
        archivos: list[str] = []
        evidencias: dict[str, dict] = {}
        grafo_info: dict = {}

        try:
            ac2 = self.simanw_service._generar_evidencia_ac2(corpus)
        except Exception as exc:
            ac2 = {
                "estado": "pendiente",
                "observacion": f"No se pudieron generar nubes AC-2 desde datos guardados: {exc}",
            }
        if ac2:
            evidencias["AC-2"] = ac2
            if ac2.get("archivo_json"):
                rutas["analisis_ac2_json"] = ac2["archivo_json"]
                archivos.append(ac2["archivo_json"])
            if ac2.get("archivo_nube"):
                rutas["nube_ac2_png"] = ac2["archivo_nube"]
                archivos.append(ac2["archivo_nube"])
            if ac2.get("archivo_nubes_categoria_json"):
                rutas["nubes_ac2_categorias"] = ac2["archivo_nubes_categoria_json"]
                archivos.append(ac2["archivo_nubes_categoria_json"])
            for ruta in ac2.get("archivos_nube_categoria", {}).values():
                if ruta:
                    archivos.append(str(ruta))

        try:
            tend = TendenciasTemporales()
            tend.cargar_noticias(corpus or noticias)
            tabla = tend.tabla_resumen()
            if tabla:
                ruta_csv = tend.exportar_csv("outputs/tendencias.csv")
                ruta_png = tend.exportar_png("outputs/tendencias.png")
                ruta_json = tend.guardar_reporte_json("reports/tendencias_ac9.json")
                ruta_md = tend.guardar_conclusion_markdown("reports/conclusion_tendencias_ac9.md")
                tendencias = {
                    "granularidad": tend.granularidad,
                    "tabla": tabla,
                    "pico": tend.pico_notable(),
                    "tendencias_terminos": tend.tendencias_terminos_por_categoria(minimo_categorias=3),
                    "conclusion": tend.conclusion(),
                }
                analisis["tendencias"] = tendencias
                rutas.update(
                    {
                        "tendencias_csv": str(ruta_csv),
                        "tendencias_png": str(ruta_png),
                        "tendencias_json": str(ruta_json),
                        "tendencias_conclusion_md": str(ruta_md),
                    }
                )
                archivos.extend([str(ruta_csv), str(ruta_png), str(ruta_json), str(ruta_md)])
                evidencias["AC-9"] = {
                    "actividad": "AC-9",
                    "estado": "parcial",
                    "ejecutado_desde": "Precarga local",
                    "granularidad": tend.granularidad,
                    "total_filas": len(tabla),
                    "pico": tendencias["pico"],
                    "temas_analizados": list(tendencias["tendencias_terminos"].keys()),
                    "tendencias_terminos": tendencias["tendencias_terminos"],
                    "archivo_csv": str(ruta_csv),
                    "archivo_png": str(ruta_png),
                    "archivo_json": str(ruta_json),
                    "archivo_markdown": str(ruta_md),
                }
        except Exception as exc:
            evidencias["AC-9"] = {
                "actividad": "AC-9",
                "estado": "pendiente",
                "ejecutado_desde": "Precarga local",
                "observacion": f"No se pudo generar grafica AC-9 desde datos guardados: {exc}",
            }

        try:
            grafo_info = self.simanw_service.fase6_service.construir_grafo(
                corpus,
                {"categorias": {}, "sentimientos": {}, **analisis},
            )
            ttl = self.simanw_service.fase6_service.exportar_ttl()
            jsonld = self.simanw_service.fase6_service.exportar_jsonld()
            grafo_info["formatos_exportados"] = ["ttl", "jsonld"]
            rutas["grafo_ttl"] = str(ttl)
            rutas["grafo_jsonld"] = str(jsonld)
            archivos.extend([str(ttl), str(jsonld)])
            evidencia_ac7 = grafo_info.get("evidencia_ac7", {})
            if evidencia_ac7:
                evidencias["AC-7"] = {
                    **evidencia_ac7,
                    "actividad": "AC-7",
                    "estado": "parcial",
                    "ejecutado_desde": "Precarga local",
                }
                if evidencia_ac7.get("archivo_ttl"):
                    rutas["kg_enriquecido_ac7_ttl"] = evidencia_ac7["archivo_ttl"]
                    archivos.append(evidencia_ac7["archivo_ttl"])
                if evidencia_ac7.get("archivo_json"):
                    rutas["enlaces_wikidata_ac7_json"] = evidencia_ac7["archivo_json"]
                    archivos.append(evidencia_ac7["archivo_json"])
        except Exception as exc:
            grafo_info = {
                "total_triples": 0,
                "formatos_exportados": [],
                "entidades": {},
                "consultas_ejemplo": [],
                "evidencia_ac7": {},
                "errores": [f"No se pudo reconstruir el grafo desde datos guardados: {exc}"],
            }

        return analisis, rutas, list(dict.fromkeys(archivos)), evidencias, grafo_info

    @staticmethod
    def _leer_lista_json(ruta: Path) -> list[dict]:
        if not ruta.exists():
            return []
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(datos, list):
            return []
        return [item for item in datos if isinstance(item, dict)]


def _corpus_minimo(noticia: dict) -> dict:
    titulo = str(noticia.get("titulo") or "Sin titulo")
    cuerpo = str(noticia.get("cuerpo") or noticia.get("resumen") or titulo)
    categoria = str(noticia.get("categoria") or noticia.get("categoria_original") or "sin_categoria")
    tokens = [token for token in f"{titulo} {cuerpo}".lower().split() if token]
    return {
        **noticia,
        "titulo": titulo,
        "cuerpo": cuerpo,
        "texto_original": cuerpo,
        "texto_limpio": cuerpo,
        "categoria": categoria,
        "categoria_original": categoria,
        "tokens": tokens,
        "terminos": tokens,
        "terminos_relevantes": tokens[:10],
        "num_tokens": len(tokens),
        "num_terminos": len(tokens),
        "num_oraciones": max(cuerpo.count(".") + cuerpo.count("?") + cuerpo.count("!"), 1),
        "vocabulario_unico": len(set(tokens)),
        "riqueza_lexica": len(set(tokens)) / max(len(tokens), 1),
    }


def _noticia_desde_corpus(item: dict) -> dict:
    return {
        "titulo": item.get("titulo", "Sin titulo"),
        "cuerpo": item.get("cuerpo") or item.get("texto_original") or item.get("texto_limpio") or "",
        "fecha": item.get("fecha", "sin_fecha"),
        "autor": item.get("autor", "Autor desconocido"),
        "categoria": item.get("categoria_predicha") or item.get("categoria") or item.get("categoria_original") or "sin_categoria",
        "url": item.get("url", ""),
        "fuente_nombre": item.get("fuente_nombre", ""),
        "sentimiento": item.get("sentimiento", {}),
    }


def _estadisticas_precargadas(corpus: list[dict]) -> dict:
    total_tokens = sum(int(item.get("num_tokens", len(item.get("tokens", []))) or 0) for item in corpus)
    total_terminos = sum(int(item.get("num_terminos", len(item.get("terminos", []))) or 0) for item in corpus)
    vocabulario = set()
    for item in corpus:
        vocabulario.update(str(term) for term in item.get("terminos", []))
    total_documentos = len(corpus)
    return {
        "total_documentos": total_documentos,
        "total_tokens": total_tokens,
        "stems_unicos": len(vocabulario),
        "vocabulario_total": len(vocabulario),
        "promedio_tokens_doc": total_tokens / max(total_documentos, 1),
        "terminos_filtrados": total_terminos,
    }


def main() -> None:
    app = SIMANWDesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
