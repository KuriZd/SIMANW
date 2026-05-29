"""AC-12: Trazabilidad y reproducibilidad del pipeline."""
# LEGACY UI: este frame no forma parte del sidebar principal de app_desktop.py.
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.trazabilidad import trazabilidad_demo
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME

_ARCHIVOS_SALIDA = {
    "rastreo_paginado": "data/ac1_noticias_paginadas.json",
    "calidad": "data/ac8_informe_calidad.json",
    "tendencias": "data/ac9_tendencias.csv",
    "consultas_guardadas": "data/ac10_consultas_guardadas.json",
    "historial_alertas": "data/ac10_historial_alertas.json",
    "usabilidad": "data/ac11_resultados_usabilidad.csv",
}


class Ac12TrazabilidadFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.traza = None

        self.stat_etapas_var = ctk.StringVar(value="—")
        self.stat_version_var = ctk.StringVar(value="—")
        self.alumno_var = ctk.StringVar(value="Alumno SIMANW")
        self.estado_var = ctk.StringVar(value="Sin ejecutar")
        self._build()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=250, weight=0)
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
        ctk.CTkLabel(card, text="Trazabilidad del pipeline", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        ctk.CTkLabel(card, text="Nombre del alumno", font=FONT_META,
                     text_color=THEME["text_2"]).grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 2))
        ctk.CTkEntry(card, textvariable=self.alumno_var,
                     fg_color=THEME["bg_input"], border_color=THEME["border"],
                     border_width=1, text_color=THEME["text_1"]).grid(
            row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 10))
        self.btn_ejecutar = ctk.CTkButton(
            card, text="Generar trazabilidad", command=self._ejecutar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_ejecutar.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        self.btn_exportar = ctk.CTkButton(
            card, text="Exportar todos los artefactos", command=self._exportar,
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"], state="disabled")
        self.btn_exportar.grid(row=4, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        ctk.CTkLabel(card, text="Estado", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=5, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(card, textvariable=self.estado_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=6, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_metricas_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        for i, (label, var) in enumerate([
            ("Etapas registradas", self.stat_etapas_var),
            ("Version", self.stat_version_var),
        ]):
            ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=i * 2, column=0, sticky="w", padx=CARD_PADDING,
                pady=(CARD_PADDING if i == 0 else 0, 0))
            ctk.CTkLabel(card, textvariable=var, font=FONT_BODY,
                         text_color=THEME["text_1"], anchor="w").grid(
                row=i * 2 + 1, column=0, sticky="w", padx=CARD_PADDING,
                pady=(0, 4 if i == 0 else CARD_PADDING))
        return card

    def _build_titulo_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Manifiesto y checklist", font=FONT_H2,
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

    def _ejecutar(self) -> None:
        self.btn_ejecutar.configure(state="disabled")
        self.estado_var.set("Generando…")
        self.root_app.show_progress()
        alumno = self.alumno_var.get().strip() or "Alumno SIMANW"
        threading.Thread(target=self._ejecutar_bg, args=(alumno,), daemon=True).start()

    def _ejecutar_bg(self, alumno: str) -> None:
        try:
            traza = trazabilidad_demo()
            manifiesto = traza.manifiesto(_ARCHIVOS_SALIDA)
            checklist = traza.checklist_firmado(alumno)
            limitaciones = traza.anexo_limitaciones()
            procedimiento = traza.procedimiento_reproducible()
            self.traza = traza
            self.after(0, lambda: self._on_ok(traza, manifiesto, checklist,
                                               limitaciones, procedimiento))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_ok(self, traza, manifiesto, checklist: str, limitaciones: str, procedimiento: str) -> None:
        self.stat_etapas_var.set(str(len(traza.eventos)))
        self.stat_version_var.set(traza.version_proyecto[:12])

        lineas = [
            f"  Version del proyecto : {traza.version_proyecto}",
            f"  Fuente de noticias   : {traza.fuente_noticias}",
            f"  Etapas registradas   : {len(traza.eventos)}",
            "",
            "  ETAPAS DEL PIPELINE",
            f"  {'Etapa':<12} {'Entrada':>8} {'Salida':>8}  Artefacto",
            "  " + "-" * 65,
        ]
        for e in traza.eventos:
            lineas.append(
                f"  {e.etapa:<12} {e.documentos_entrada:>8} {e.documentos_salida:>8}  {e.artefacto}")

        lineas += ["", "  CHECKLIST DE REPRODUCIBILIDAD", ""]
        lineas += ["  " + l for l in checklist.splitlines()]

        lineas += ["", "  PROCEDIMIENTO REPRODUCIBLE", ""]
        lineas += ["  " + l for l in procedimiento.splitlines()]

        lineas += ["", "  LIMITACIONES", ""]
        lineas += ["  " + l for l in limitaciones.splitlines()]

        self._set_output("\n".join(lineas))
        self.estado_var.set("Trazabilidad generada")
        self.btn_ejecutar.configure(state="normal")
        self.btn_exportar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(
            f"AC-12: {len(traza.eventos)} etapas, version {traza.version_proyecto[:8]}", "ok")

    def _exportar(self) -> None:
        if not self.traza:
            return
        alumno = self.alumno_var.get().strip() or "Alumno SIMANW"
        try:
            self.traza.guardar_manifiesto("data/ac12_manifiesto.json", _ARCHIVOS_SALIDA)
            self.traza.guardar_log_jsonl("logs/ac12_log.jsonl")
            self.traza.guardar_checklist("reports/checklist_ac12.md", alumno)
            self.traza.guardar_limitaciones("reports/limitaciones_ac12.md")
            self.root_app.set_estado("AC-12: artefactos exportados", "ok")
        except Exception as exc:
            messagebox.showerror("AC-12", str(exc))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_ejecutar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-12", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")
