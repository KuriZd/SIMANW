from __future__ import annotations

import customtkinter as ctk

from src.simanw_app_service import ResultadoAnalisis
from src.ui.content_header import ContentHeaderFrame
from src.ui.seccion_cargar import SeccionCargar
from src.ui.seccion_dashboard import SeccionDashboard
from src.ui.seccion_explorador import SeccionExplorador
from src.ui.seccion_exportar import SeccionExportar
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
        panel.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(panel, text=nombre, font=FONT_H1, text_color=THEME["text_1"]).grid(
            row=0, column=0, pady=(28, 4)
        )
        ctk.CTkLabel(
            panel,
            text="Módulo reservado para una fase futura.",
            font=FONT_BODY,
            text_color=THEME["text_2"],
        ).grid(row=1, column=0)


_SECTION_META: dict[str, tuple[str, str]] = {
    "cargar":     ("Cargar noticias",    "Selecciona la fuente y lanza el análisis completo."),
    "dashboard":  ("Dashboard",          "Resumen del análisis: estadísticas y términos clave."),
    "explorador": ("Explorador",         "Navega las noticias crudas extraídas."),
    "resultados": ("Resultados NLP",     "Corpus procesado: tokens, stems y términos TF-IDF."),
    "busqueda":   ("Búsqueda y Q&A",     "Motor de búsqueda semántico. (Fase futura)"),
    "grafo":      ("Grafo de conocimiento", "Visualización RDF/SPARQL. (Fase futura)"),
    "exportar":   ("Exportar",           "Archivos generados y opciones de re-exportación."),
}


class SIMANWDesktopApp(ctk.CTk):
    """Aplicación de escritorio SIMANW. Navegación centrada en el usuario."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        super().__init__(fg_color=THEME["bg_base"])
        self.title("SIMANW - Monitor de Noticias Web")
        self.geometry("1220x760")
        self.minsize(1040, 640)

        self.current_content: ctk.CTkFrame | None = None
        self.total_noticias = 0

        # Estado compartido entre secciones
        self.noticias:            list[dict] = []
        self.corpus_procesado:    list[dict] = []
        self.estadisticas_fase2:  dict       = {}
        self.rutas_exportacion:   dict       = {}
        self.pipeline_estado:     dict       = {}

        self._build_layout()
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
            self.current_content.destroy()

        titulo, desc = _SECTION_META.get(section_id, ("Módulo futuro", "No integrado aún."))
        self.header.set_content(titulo, desc)

        if section_id == "cargar":
            self.current_content = SeccionCargar(self.content_host, root_app=self)
        elif section_id == "dashboard":
            self.current_content = SeccionDashboard(self.content_host, root_app=self)
        elif section_id == "explorador":
            self.current_content = SeccionExplorador(self.content_host, root_app=self)
        elif section_id == "resultados":
            self.current_content = SeccionResultados(self.content_host, root_app=self)
        elif section_id == "exportar":
            self.current_content = SeccionExportar(self.content_host, root_app=self)
        else:
            self.current_content = PlaceholderFrame(self.content_host, titulo)

        self.current_content.grid(row=0, column=0, sticky="nsew")
        self.hide_progress()
        self.sidebar.set_active(section_id)

        if not self.noticias and section_id not in ("cargar", "busqueda", "grafo"):
            self.set_estado("Sin datos — carga noticias primero.", "warning",
                            total_noticias=0)
        else:
            self.set_estado(f"{titulo} lista.", "ok", total_noticias=self.total_noticias)

    # ── escritura de estado compartido ────────────────────────────────────────

    def set_resultado_analisis(self, resultado: ResultadoAnalisis) -> None:
        self.noticias           = resultado.noticias
        self.total_noticias     = len(resultado.noticias)
        self.corpus_procesado   = resultado.corpus
        self.estadisticas_fase2 = resultado.estadisticas
        self.rutas_exportacion  = resultado.rutas
        self.pipeline_estado    = resultado.pipeline_estado

    def set_noticias(self, noticias: list[dict]) -> None:
        self.noticias       = noticias
        self.total_noticias = len(noticias)

    def set_corpus(self, corpus: list[dict], estadisticas: dict) -> None:
        self.corpus_procesado   = corpus
        self.estadisticas_fase2 = estadisticas

    def set_estado(self, mensaje: str, nivel: str = "ok", total_noticias: int | None = None) -> None:
        if total_noticias is not None:
            self.total_noticias = total_noticias
        self.status_bar.set_estado(mensaje, nivel, total_noticias=self.total_noticias)

    def show_progress(self) -> None:
        self.header.show_progress()

    def hide_progress(self) -> None:
        self.header.hide_progress()


def main() -> None:
    app = SIMANWDesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
