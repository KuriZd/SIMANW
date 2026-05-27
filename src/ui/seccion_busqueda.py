from __future__ import annotations

import customtkinter as ctk

from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, THEME


class SeccionBusquedaQA(ctk.CTkFrame):
    """Busqueda inteligente y Q&A sobre el corpus cargado."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.query_var = ctk.StringVar()
        self.question_var = ctk.StringVar()
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if not self.root_app.corpus_procesado:
            self._empty()
            return

        left = self._card(self)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_rowconfigure(3, weight=1)
        right = self._card(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(left, text="Smart Search", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        ctk.CTkEntry(left, textvariable=self.query_var, placeholder_text="Search the loaded corpus",
                     fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_1"]).grid(
            row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8)
        )
        ctk.CTkButton(left, text="Search", command=self._buscar, fg_color=THEME["accent"]).grid(
            row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8)
        )
        self.search_box = ctk.CTkTextbox(left, fg_color=THEME["bg_input"], text_color=THEME["text_1"], font=FONT_BODY)
        self.search_box.grid(row=3, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        ctk.CTkLabel(right, text="Q&A", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        ctk.CTkEntry(right, textvariable=self.question_var, placeholder_text="Ask about the loaded news",
                     fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_1"]).grid(
            row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8)
        )
        ctk.CTkButton(right, text="Ask", command=self._preguntar, fg_color=THEME["accent"]).grid(
            row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8)
        )
        self.qa_box = ctk.CTkTextbox(right, fg_color=THEME["bg_input"], text_color=THEME["text_1"], font=FONT_BODY)
        self.qa_box.grid(row=3, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self._render_history()

    def _card(self, master) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _empty(self) -> None:
        center = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        center.grid(row=0, column=0, columnspan=2)
        ctk.CTkLabel(center, text="No corpus loaded", font=FONT_H1, text_color=THEME["text_2"]).grid(row=0, column=0)
        ctk.CTkButton(center, text="Load / Analyze News", command=lambda: self.root_app.show_section("cargar"),
                      fg_color=THEME["accent"]).grid(row=1, column=0, pady=12)

    def _buscar(self) -> None:
        service = getattr(self.root_app, "simanw_service", None)
        resultados = service.buscar(self.query_var.get()) if service else []
        texto = []
        for idx, item in enumerate(resultados, start=1):
            texto.append(
                f"{idx}. [{item.get('score', 0):.3f}] {item.get('titulo', '')}\n"
                f"   {item.get('categoria', '?')} | {item.get('sentimiento', '?')} | {item.get('fecha', '')}\n"
                f"   {item.get('snippet', '')}\n   {item.get('url', '')}\n"
            )
        self._set_text(self.search_box, "\n".join(texto) or "No results.")

    def _preguntar(self) -> None:
        service = getattr(self.root_app, "simanw_service", None)
        respuesta = service.preguntar(self.question_var.get()) if service else "No service available."
        self._render_history(extra=respuesta)

    def _render_history(self, extra: str | None = None) -> None:
        service = getattr(self.root_app, "simanw_service", None)
        historial = service.fase5_service.obtener_historial() if service else []
        lineas = []
        for item in historial:
            lineas.append(f"Q: {item.get('pregunta', '')}\nA: {item.get('respuesta', '')}\n")
        if extra and not historial:
            lineas.append(extra)
        self._set_text(self.qa_box, "\n".join(lineas) or "Ask a question to start.")

    @staticmethod
    def _set_text(widget: ctk.CTkTextbox, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")
