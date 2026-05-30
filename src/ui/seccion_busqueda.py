from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, THEME


class SeccionBusquedaQA(ctk.CTkFrame):
    """Busqueda inteligente y Q&A sobre el corpus cargado."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.query_var = ctk.StringVar()
        self.question_var = ctk.StringVar()
        self.modelo_var = ctk.StringVar(value="Natural")
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
        left.grid_rowconfigure(4, weight=1)
        right = self._card(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_rowconfigure(3, weight=1)
        bottom = self._card(self)
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 12))

        ctk.CTkLabel(left, text="Smart Search", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        ctk.CTkEntry(left, textvariable=self.query_var, placeholder_text="Search the loaded corpus",
                     fg_color=THEME["bg_input"], border_color=THEME["border"], text_color=THEME["text_1"]).grid(
            row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8)
        )
        ctk.CTkOptionMenu(
            left,
            variable=self.modelo_var,
            values=["Natural", "Vectorial", "Booleano"],
            fg_color=THEME["bg_input"],
            button_color=THEME["border"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
        ).grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        ctk.CTkButton(left, text="Search", command=self._buscar, fg_color=THEME["accent"]).grid(
            row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8)
        )
        self.search_box = ctk.CTkTextbox(left, fg_color=THEME["bg_input"], text_color=THEME["text_1"], font=FONT_BODY)
        self.search_box.grid(row=4, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))

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
        self._build_alerts_card(bottom)
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
        modelo = self.modelo_var.get().lower()
        resultados = service.buscar(self.query_var.get(), modelo=modelo) if service else []
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

    def _build_alerts_card(self, card) -> None:
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(card, text="Saved query alerts (AC-10)", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4)
        )
        self.alerts_label = ctk.CTkLabel(
            card,
            text=self._alerts_text(),
            font=FONT_BODY,
            text_color=THEME["text_1"],
            justify="left",
            anchor="w",
        )
        self.alerts_label.grid(row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        ctk.CTkButton(
            card,
            text="Run alerts on loaded news",
            command=self._ejecutar_alertas,
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=CARD_PADDING, pady=CARD_PADDING)

    def _alerts_text(self, evidencia: dict | None = None) -> str:
        if evidencia is None:
            result = getattr(self.root_app, "resultado_actual", None)
            evidencia = result.evidencias_ac.get("AC-10", {}) if result else {}
        consultas = evidencia.get("consultas_guardadas", [])
        return (
            f"Estado: {evidencia.get('estado', 'pendiente')} | "
            f"Origen: {evidencia.get('origen_consultas', 'sin consultas')} | "
            f"Consultas: {evidencia.get('numero_consultas', len(consultas))} | "
            f"Alertas: {evidencia.get('alertas_generadas', 0)} | "
            f"Historial: {evidencia.get('historial_alertas', 0)} | "
            f"Duplicados evitados: {evidencia.get('alertas_duplicadas_evitadas', 0)}\n"
            f"Sin noticias nuevas: {evidencia.get('noticias_procesadas_sin_nuevas', 0)} docs | "
            f"Con noticias nuevas: {evidencia.get('noticias_procesadas_con_nuevas', 0)} docs | "
            f"Reproceso duplicado: {evidencia.get('alertas_segunda_ejecucion', 0)} alertas\n"
            f"{', '.join(consultas[:5]) or 'Sin consultas registradas'}"
        )

    def _ejecutar_alertas(self) -> None:
        service = getattr(self.root_app, "simanw_service", None)
        if service is None:
            mensaje = "No hay servicio activo. Carga y analiza noticias primero."
            self.alerts_label.configure(text=mensaje)
            self.root_app.set_estado(mensaje, "warning")
            messagebox.showwarning("Alertas AC-10", mensaje)
            return

        if not getattr(self.root_app, "corpus_procesado", []):
            mensaje = "No hay noticias cargadas para evaluar alertas."
            self.alerts_label.configure(text=mensaje)
            self.root_app.set_estado(mensaje, "warning")
            messagebox.showwarning("Alertas AC-10", mensaje)
            return

        try:
            evidencia = service.ejecutar_alertas_guardadas()
        except Exception as exc:
            mensaje = f"No se pudieron ejecutar las alertas: {exc}"
            self.alerts_label.configure(text=mensaje)
            self.root_app.set_estado(mensaje, "error")
            messagebox.showerror("Alertas AC-10", mensaje)
            return

        if not evidencia:
            mensaje = "No se genero evidencia de alertas. Revisa que el pipeline haya terminado."
            self.alerts_label.configure(text=mensaje)
            self.root_app.set_estado(mensaje, "warning")
            return

        if getattr(service, "estado_actual", None) is not None:
            self.root_app.resultado_actual = service.estado_actual

        self.alerts_label.configure(text=self._alerts_text(evidencia))
        generadas = evidencia.get("alertas_generadas", 0)
        duplicadas = evidencia.get("alertas_duplicadas_evitadas", 0)
        self.root_app.set_estado(
            f"AC-10: {generadas} alertas generadas, {duplicadas} duplicados evitados",
            "ok" if generadas else "warning",
        )

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
