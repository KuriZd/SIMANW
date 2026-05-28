"""AC-11: Estudio de usabilidad."""
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.usabilidad import estudio_demo
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME


class Ac11UsabilidadFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.estudio = None

        self.stat_partic_var = ctk.StringVar(value="—")
        self.estado_var = ctk.StringVar(value="Sin generar")
        self._build()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=240, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self._build_control_card(left).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_metricas_card(left).grid(row=1, column=0, sticky="ew")
        self._build_titulo_card(right).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_output_card(right).grid(row=1, column=0, sticky="nsew")

    def _build_control_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Estudio de usabilidad", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        ctk.CTkLabel(card,
                     text="3 participantes anonimos\n8 items en escala Likert 1-5\n5 tareas de usabilidad",
                     font=FONT_META, text_color=THEME["text_2"], justify="left").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10))
        self.btn_generar = ctk.CTkButton(
            card, text="Generar estudio demo", command=self._generar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_generar.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        self.btn_exportar = ctk.CTkButton(
            card, text="Exportar CSV + Markdown", command=self._exportar,
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"], state="disabled")
        self.btn_exportar.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        ctk.CTkLabel(card, text="Estado", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=4, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(card, textvariable=self.estado_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=5, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_metricas_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Participantes", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 0))
        ctk.CTkLabel(card, textvariable=self.stat_partic_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_titulo_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Resultados del estudio", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, CARD_PADDING))
        return card

    def _build_output_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(0, weight=1)
        self.output_box = ctk.CTkTextbox(
            card, fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1,
            text_color=THEME["text_1"], font=FONT_MONO, wrap="word", state="disabled")
        self.output_box.grid(row=0, column=0, sticky="nsew",
                              padx=CARD_PADDING, pady=CARD_PADDING)
        return card

    def _generar(self) -> None:
        self.btn_generar.configure(state="disabled")
        self.estado_var.set("Generando…")
        self.root_app.show_progress()
        threading.Thread(target=self._generar_bg, daemon=True).start()

    def _generar_bg(self) -> None:
        try:
            e = estudio_demo()
            promedios = e.promedios()
            problemas = e.problemas_y_mejoras()
            reflexion = e.reflexion_consentimiento()
            self.estudio = e
            self.after(0, lambda: self._on_ok(e, promedios, problemas, reflexion))
        except Exception as exc:
            self.after(0, lambda err=exc: self._on_error(str(err)))

    def _on_ok(self, e, promedios: dict, problemas: list, reflexion: str) -> None:
        self.stat_partic_var.set(str(len(e.participantes)))

        lineas = ["  TAREAS DEL GUION"]
        for i, tarea in enumerate(e.tareas, 1):
            lineas.append(f"  {i}. {tarea}")

        lineas += ["", "  PROMEDIOS DEL CUESTIONARIO (1-5)"]
        for item, val in promedios.items():
            barra = "█" * round(val * 2)
            lineas.append(f"  {item:<35} {val:.2f}  {barra}")

        lineas += ["", "  PROBLEMAS Y MEJORAS"]
        for i, pm in enumerate(problemas, 1):
            lineas.append(f"  {i}. {pm['problema']}")
            lineas.append(f"     Mejora: {pm['mejora']}")
            lineas.append("")

        lineas += ["  REFLEXION ETICA Y CONSENTIMIENTO", ""]
        lineas += ["  " + l for l in reflexion.splitlines()]

        self._set_output("\n".join(lineas))
        self.estado_var.set("Estudio generado")
        self.btn_generar.configure(state="normal")
        self.btn_exportar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(
            f"AC-11: {len(e.participantes)} participantes, promedio general "
            f"{sum(promedios.values()) / len(promedios):.2f}", "ok")

    def _exportar(self) -> None:
        if not self.estudio:
            return
        try:
            self.estudio.exportar_csv("data/ac11_resultados_usabilidad.csv")
            self.estudio.guardar_reporte_markdown("reports/usabilidad_ac11.md")
            self.estudio.guardar_reflexion_etica("reports/reflexion_etica_ac11.md")
            self.root_app.set_estado("AC-11: CSV y Markdown exportados", "ok")
        except Exception as exc:
            messagebox.showerror("AC-11", str(exc))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_generar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-11", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")
