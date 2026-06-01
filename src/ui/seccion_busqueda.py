from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, THEME


ASSISTANT_BUBBLE = "#171a24"
USER_BUBBLE = "#2563eb"


class SeccionBusquedaQA(ctk.CTkFrame):
    """Busqueda inteligente y Q&A sobre el corpus cargado."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.query_var = ctk.StringVar()
        self.question_var = ctk.StringVar()
        self.modelo_var = ctk.StringVar(value="Natural")
        self.active_mode = "qa"
        self.mode_buttons: dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if not self.root_app.corpus_procesado:
            self._empty()
            return

        main = self._card(self)
        main.grid(row=0, column=0, sticky="nsew", padx=18, pady=12)
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        bottom = self._card(self)
        bottom.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Search & Q&A", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w"
        )
        toggle = ctk.CTkFrame(header, fg_color=THEME["bg_input"], corner_radius=8)
        toggle.grid(row=0, column=1, sticky="e")
        self.mode_buttons = {
            "qa": ctk.CTkButton(toggle, text="Q&A", width=110, command=lambda: self._set_mode("qa")),
            "search": ctk.CTkButton(toggle, text="Smart Search", width=130, command=lambda: self._set_mode("search")),
        }
        self.mode_buttons["qa"].grid(row=0, column=0, padx=4, pady=4)
        self.mode_buttons["search"].grid(row=0, column=1, padx=(0, 4), pady=4)

        self.mode_host = ctk.CTkFrame(main, fg_color="transparent")
        self.mode_host.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self.mode_host.grid_columnconfigure(0, weight=1)
        self.mode_host.grid_rowconfigure(3, weight=1)
        self._render_mode()
        self._build_alerts_card(bottom)

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

    def _set_mode(self, mode: str) -> None:
        self.active_mode = mode
        self._render_mode()

    def _render_mode(self) -> None:
        for child in self.mode_host.winfo_children():
            child.destroy()
        self.mode_host.grid_rowconfigure(3, weight=1)
        for mode, button in self.mode_buttons.items():
            active = mode == self.active_mode
            button.configure(
                fg_color=THEME["accent"] if active else THEME["bg_input"],
                hover_color=THEME["accent"] if active else THEME["border"],
                text_color=THEME["text_1"],
                border_width=0 if active else 1,
                border_color=THEME["border"],
            )

        if self.active_mode == "search":
            self._render_search_mode()
            return
        self._render_qa_mode()

    def _render_search_mode(self) -> None:
        self.mode_host.grid_rowconfigure(1, weight=0)
        self.mode_host.grid_rowconfigure(2, weight=0)
        self.mode_host.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(self.mode_host, text="Smart Search", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        ctk.CTkEntry(
            self.mode_host,
            textvariable=self.query_var,
            placeholder_text="Search the loaded corpus",
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        ).grid(row=1, column=0, sticky="ew", pady=(0, 8))
        controls = ctk.CTkFrame(self.mode_host, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        controls.grid_columnconfigure(0, weight=1)
        ctk.CTkOptionMenu(
            controls,
            variable=self.modelo_var,
            values=["Natural", "Vectorial", "Booleano"],
            fg_color=THEME["bg_input"],
            button_color=THEME["border"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(controls, text="Search", command=self._buscar, fg_color=THEME["accent"]).grid(
            row=0, column=1, sticky="e"
        )
        self.search_box = ctk.CTkTextbox(
            self.mode_host,
            fg_color=THEME["bg_input"],
            text_color=THEME["text_1"],
            font=FONT_BODY,
        )
        self.search_box.grid(row=3, column=0, sticky="nsew")
        self._set_text(self.search_box, "Search results will appear here.")

    def _render_qa_mode(self) -> None:
        self.mode_host.grid_rowconfigure(1, weight=1)
        self.mode_host.grid_rowconfigure(2, weight=0)
        self.mode_host.grid_rowconfigure(3, weight=0)
        ctk.CTkLabel(self.mode_host, text="Q&A", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.chat_area = ctk.CTkScrollableFrame(
            self.mode_host,
            fg_color=THEME["bg_input"],
            corner_radius=10,
        )
        self.chat_area.grid(row=1, column=0, rowspan=2, sticky="nsew", pady=(0, 10))
        self.chat_area.grid_columnconfigure(0, weight=1)

        composer = ctk.CTkFrame(
            self.mode_host,
            fg_color=THEME["bg_input"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border"],
        )
        composer.grid(row=3, column=0, sticky="ew")
        composer.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(
            composer,
            textvariable=self.question_var,
            placeholder_text="Ask about the loaded news",
            fg_color="transparent",
            border_width=0,
            text_color=THEME["text_1"],
        ).grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=10)
        ctk.CTkButton(
            composer,
            text="Ask",
            width=82,
            command=self._preguntar,
            fg_color=THEME["accent"],
        ).grid(row=0, column=1, sticky="e", padx=(0, 10), pady=10)
        self._render_history()

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
        if hasattr(self, "search_box"):
            self._set_text(self.search_box, "\n".join(texto) or "No results.")

    def _preguntar(self) -> None:
        service = getattr(self.root_app, "simanw_service", None)
        respuesta = service.preguntar(self.question_var.get()) if service else "No service available."
        self.question_var.set("")
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
        if not hasattr(self, "chat_area"):
            return
        for child in self.chat_area.winfo_children():
            child.destroy()
        if not historial and extra:
            self._add_message_bubble("assistant", extra, 0)
            return
        if not historial:
            self._render_empty_chat()
            return
        row = 0
        for item in historial:
            self._add_message_bubble("user", item.get("pregunta", ""), row)
            row += 1
            self._add_message_bubble("assistant", item.get("respuesta", ""), row)
            row += 1
        self.after(50, self._scroll_chat_bottom)

    def _scroll_chat_bottom(self) -> None:
        canvas = getattr(getattr(self, "chat_area", None), "_parent_canvas", None)
        if canvas is not None:
            canvas.yview_moveto(1.0)

    def _render_empty_chat(self) -> None:
        empty = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        empty.grid(row=0, column=0, sticky="nsew", padx=18, pady=24)
        empty.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            empty,
            text="Ask a question about your loaded news",
            font=FONT_H2,
            text_color=THEME["text_1"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ctk.CTkLabel(
            empty,
            text="Try: Cuantas noticias hay de tecnologia? or Dame otra noticia similar a la anterior.",
            font=FONT_BODY,
            text_color=THEME["text_2"],
            wraplength=720,
            justify="left",
        ).grid(row=1, column=0, sticky="w")

    def _add_message_bubble(self, role: str, text: str, row: int) -> None:
        is_user = role == "user"
        outer = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        outer.grid(row=row, column=0, sticky="ew", padx=12, pady=(4, 8))
        outer.grid_columnconfigure(0, weight=1)
        bubble = ctk.CTkFrame(
            outer,
            fg_color=USER_BUBBLE if is_user else ASSISTANT_BUBBLE,
            corner_radius=14,
            border_width=0 if is_user else 1,
            border_color=THEME["border"],
        )
        bubble.grid(row=0, column=0, sticky="e" if is_user else "w", padx=(120, 0) if is_user else (0, 120))
        ctk.CTkLabel(
            bubble,
            text="You" if is_user else "SIMANW",
            font=FONT_META,
            text_color="#dbeafe" if is_user else THEME["text_2"],
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            bubble,
            text=str(text or ""),
            font=FONT_BODY,
            text_color=THEME["text_1"],
            justify="left",
            wraplength=620,
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 10))

    @staticmethod
    def _set_text(widget: ctk.CTkTextbox, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")
