"""Sección 'Cargar noticias' — fuente + pipeline de análisis automático."""
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.fuentes_service import FuentesService
from src.simanw_app_service import ResultadoAnalisis, SIMANWAppService
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, THEME


_STEPS = SIMANWAppService.PASOS
_ICON_PENDING = "○"
_ICON_RUNNING = "●"
_ICON_OK      = "✓"
_ICON_ERROR   = "✗"

_MODO_DEMO     = "Demo local"
_MODO_PREDEF   = "Predefined source"
_MODO_CUSTOM   = "Custom RSS/URL"


class SeccionCargar(ctk.CTkFrame):
    """Panel de carga y análisis: selecciona fuente y dispara el pipeline completo."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app        = root_app
        self.service         = SIMANWAppService()
        self.fuentes_service = FuentesService()

        self.modo_var        = ctk.StringVar(value=_MODO_DEMO)
        self.fuente_predef_var = ctk.StringVar()
        self.tipo_custom_var = ctk.StringVar(value="RSS")
        self.url_var         = ctk.StringVar()

        self._step_icon_labels: list[ctk.CTkLabel] = []
        self._step_text_labels: list[ctk.CTkLabel] = []
        self._step_index = 0

        self._build()

    # ═══════════════════════════════════════════════════════════════════════════
    # Layout
    # ═══════════════════════════════════════════════════════════════════════════

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=300, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self._build_fuente_card(left).grid(row=0, column=0, sticky="ew")
        self._build_pipeline_card(right).grid(row=0, column=0, sticky="nsew")

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build_fuente_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)

        ctk.CTkLabel(
            card, text="Fuente de noticias", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        self.selector_modo = ctk.CTkOptionMenu(
            card,
            values=[_MODO_DEMO, _MODO_PREDEF, _MODO_CUSTOM],
            variable=self.modo_var,
            command=lambda _: self._actualizar_modo_entrada(),
            fg_color=THEME["bg_input"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"],
            dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"],
        )
        self.selector_modo.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        # selector fuente predefinida (visible solo en modo PREDEF)
        nombres = self.fuentes_service.listar_nombres_fuentes()
        if nombres:
            self.fuente_predef_var.set(nombres[0])
        self.selector_predef = ctk.CTkOptionMenu(
            card,
            values=nombres or ["Sin fuentes activas"],
            variable=self.fuente_predef_var,
            fg_color=THEME["bg_input"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"],
            dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"],
        )
        self.selector_predef.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        # tipo para URL personalizada (visible solo en modo CUSTOM)
        self.selector_tipo_custom = ctk.CTkOptionMenu(
            card,
            values=["RSS", "Paginado"],
            variable=self.tipo_custom_var,
            fg_color=THEME["bg_input"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"],
            dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"],
        )
        self.selector_tipo_custom.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.url_entry = ctk.CTkEntry(
            card,
            textvariable=self.url_var,
            placeholder_text="URL RSS o página de inicio",
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            text_color=THEME["text_1"],
            placeholder_text_color=THEME["text_2"],
        )
        self.url_entry.grid(row=4, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 10))

        self.btn_analizar = ctk.CTkButton(
            card,
            text="Analyze News",
            command=self._analizar,
            fg_color=THEME["accent"],
            hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            height=36,
        )
        self.btn_analizar.grid(row=5, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        self._actualizar_modo_entrada()
        return card

    def _build_pipeline_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(7, weight=1)

        ctk.CTkLabel(
            card, text="Pipeline de análisis", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 12))

        for i, step_msg in enumerate(_STEPS, start=1):
            icon_lbl = ctk.CTkLabel(
                card, text=_ICON_PENDING, font=FONT_BODY, text_color=THEME["text_2"], width=20
            )
            icon_lbl.grid(row=i, column=0, sticky="w", padx=(CARD_PADDING, 4), pady=3)

            text_lbl = ctk.CTkLabel(
                card, text=step_msg, font=FONT_BODY, text_color=THEME["text_2"], anchor="w"
            )
            text_lbl.grid(row=i, column=1, sticky="w", padx=(0, CARD_PADDING), pady=3)

            self._step_icon_labels.append(icon_lbl)
            self._step_text_labels.append(text_lbl)

        card.grid_columnconfigure(1, weight=1)

        self._hint_label = ctk.CTkLabel(
            card,
            text="Selecciona una fuente y haz clic en «Analizar noticias».",
            font=FONT_META,
            text_color=THEME["text_2"],
            anchor="w",
        )
        self._hint_label.grid(
            row=7, column=0, columnspan=2, sticky="sw", padx=CARD_PADDING, pady=CARD_PADDING
        )
        return card

    # ═══════════════════════════════════════════════════════════════════════════
    # Acciones
    # ═══════════════════════════════════════════════════════════════════════════

    def _analizar(self) -> None:
        source, url = self._resolver_fuente()
        self._set_running(True)
        self._reset_pipeline()
        self.root_app.set_estado("Analizando noticias…", "loading")
        self.root_app.show_progress()
        threading.Thread(target=self._analizar_bg, args=(source, url), daemon=True).start()

    def _analizar_bg(self, source: str, url: str) -> None:
        try:
            resultado = self.service.analizar_noticias(
                source,
                url,
                on_progreso=lambda msg: self.after(0, lambda m=msg: self._on_progreso(m)),
            )
            self.after(0, lambda r=resultado: self._on_resultado(r))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_progreso(self, mensaje: str) -> None:
        if self._step_index > 0:
            prev = self._step_index - 1
            self._step_icon_labels[prev].configure(text=_ICON_OK, text_color=THEME["success"])
            self._step_text_labels[prev].configure(text_color=THEME["text_1"])

        if self._step_index < len(_STEPS):
            self._step_icon_labels[self._step_index].configure(
                text=_ICON_RUNNING, text_color=THEME["accent"]
            )
            self._step_text_labels[self._step_index].configure(text_color=THEME["text_1"])

        self._step_index += 1
        self.root_app.set_estado(mensaje, "loading")

    def _on_resultado(self, resultado: ResultadoAnalisis) -> None:
        if self._step_index > 0:
            last = min(self._step_index - 1, len(_STEPS) - 1)
            self._step_icon_labels[last].configure(text=_ICON_OK, text_color=THEME["success"])
            self._step_text_labels[last].configure(text_color=THEME["text_1"])

        self.root_app.set_resultado_analisis(resultado)
        nivel = "warning" if resultado.errores else "ok"
        msg = f"{len(resultado.noticias)} noticias · {len(resultado.corpus)} documentos NLP"
        self.root_app.set_estado(msg, nivel, total_noticias=len(resultado.noticias))
        self.root_app.hide_progress()

        if resultado.errores:
            messagebox.showwarning(
                "Análisis con advertencias", "\n".join(resultado.errores[:5])
            )

        self.root_app.show_section("dashboard")

    def _on_error(self, mensaje: str) -> None:
        if self._step_index > 0:
            idx = min(self._step_index - 1, len(_STEPS) - 1)
            self._step_icon_labels[idx].configure(text=_ICON_ERROR, text_color=THEME["error"])
            self._step_text_labels[idx].configure(text_color=THEME["error"])

        self._hint_label.configure(text=f"Error: {mensaje}", text_color=THEME["error"])
        self.root_app.hide_progress()
        self.root_app.set_estado(mensaje, "error")
        self._set_running(False)
        messagebox.showerror("Error en el análisis", mensaje)

    # ═══════════════════════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════════════════════

    def _resolver_fuente(self) -> tuple[str, str]:
        """Devuelve (source, url) según el modo activo."""
        modo = self.modo_var.get()
        if modo == _MODO_DEMO:
            return "demo", ""
        if modo == _MODO_PREDEF:
            nombre = self.fuente_predef_var.get()
            fuente = self.fuentes_service.obtener_por_nombre(nombre)
            return "predefinida", fuente["id"]
        # Custom
        tipo = self.tipo_custom_var.get()
        url  = self.url_var.get().strip()
        source = "rss" if tipo == "RSS" else "paginado"
        return source, url

    def _actualizar_modo_entrada(self) -> None:
        modo = self.modo_var.get()
        predef_state  = "normal" if modo == _MODO_PREDEF  else "disabled"
        custom_state  = "normal" if modo == _MODO_CUSTOM  else "disabled"
        url_state     = "normal" if modo == _MODO_CUSTOM  else "disabled"

        self.selector_predef.configure(state=predef_state)
        self.selector_tipo_custom.configure(state=custom_state)
        self.url_entry.configure(state=url_state)

    def _reset_pipeline(self) -> None:
        self._step_index = 0
        for icon_lbl, text_lbl in zip(self._step_icon_labels, self._step_text_labels):
            icon_lbl.configure(text=_ICON_PENDING, text_color=THEME["text_2"])
            text_lbl.configure(text_color=THEME["text_2"])
        self._hint_label.configure(text="Analizando…", text_color=THEME["text_2"])

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.btn_analizar.configure(state=state)
        self.selector_modo.configure(state=state)
        if running:
            self.selector_predef.configure(state="disabled")
            self.selector_tipo_custom.configure(state="disabled")
            self.url_entry.configure(state="disabled")
        else:
            self._actualizar_modo_entrada()
