"""AC-9: Linea de tiempo y tendencias por tema."""
# LEGACY UI: este frame no forma parte del sidebar principal de app_desktop.py.
from __future__ import annotations

import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from src.tendencias_temporales import NOTICIAS_AC9_DEMO, TendenciasTemporales
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME


class Ac9TendenciasFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.analizador: TendenciasTemporales | None = None

        self.granularidad_var = ctk.StringVar(value="mes")
        self.stat_noticias_var = ctk.StringVar(value="—")
        self.stat_categorias_var = ctk.StringVar(value="—")
        self.stat_periodos_var = ctk.StringVar(value="—")
        self.estado_var = ctk.StringVar(value="Sin analizar")
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
        ctk.CTkLabel(card, text="Tendencias temporales", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        ctk.CTkLabel(card, text="Granularidad", font=FONT_META,
                     text_color=THEME["text_2"]).grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 4))
        ctk.CTkOptionMenu(
            card, values=["mes", "semana"],
            variable=self.granularidad_var,
            fg_color=THEME["bg_input"], button_color=THEME["accent"],
            button_hover_color=THEME["accent"], text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"], dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"]).grid(
            row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 10))
        self.btn_analizar = ctk.CTkButton(
            card, text="Analizar tendencias", command=self._analizar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_analizar.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        self.btn_exportar = ctk.CTkButton(
            card, text="Exportar CSV + Markdown", command=self._exportar,
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
        metricas = [
            ("Noticias cargadas", self.stat_noticias_var),
            ("Categorias", self.stat_categorias_var),
            ("Periodos", self.stat_periodos_var),
        ]
        for i, (label, var) in enumerate(metricas):
            ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=i * 2, column=0, sticky="w", padx=CARD_PADDING,
                pady=(CARD_PADDING if i == 0 else 0, 0))
            ctk.CTkLabel(card, textvariable=var, font=FONT_BODY,
                         text_color=THEME["text_1"], anchor="w").grid(
                row=i * 2 + 1, column=0, sticky="w", padx=CARD_PADDING,
                pady=(0, 4 if i < len(metricas) - 1 else CARD_PADDING))
        return card

    def _build_titulo_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Analisis de tendencias", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, CARD_PADDING))
        return card

    def _build_output_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(0, weight=1)
        self.output_box = ctk.CTkTextbox(
            card, fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1,
            text_color=THEME["text_1"], font=FONT_MONO, wrap="none", state="disabled")
        self.output_box.grid(row=0, column=0, sticky="nsew",
                              padx=CARD_PADDING, pady=CARD_PADDING)
        return card

    def _analizar(self) -> None:
        self.btn_analizar.configure(state="disabled")
        self.estado_var.set("Analizando…")
        self.root_app.set_estado("AC-9: analizando tendencias…", "loading")
        self.root_app.show_progress()
        noticias = self.root_app.noticias or NOTICIAS_AC9_DEMO
        gran = self.granularidad_var.get()
        threading.Thread(target=self._analizar_bg, args=(noticias, gran), daemon=True).start()

    def _analizar_bg(self, noticias: list[dict], gran: str) -> None:
        try:
            a = TendenciasTemporales(granularidad=gran)
            a.cargar_noticias(noticias)
            tabla = a.tabla_resumen()
            pico = a.pico_notable()
            conclusion = a.conclusion()
            viz = a.visualizacion_texto()
            self.analizador = a
            conteos = a.conteo_por_periodo()
            self.after(0, lambda: self._on_ok(tabla, pico, conclusion, viz, conteos))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_ok(self, tabla: list, pico: dict, conclusion: str, viz: str, conteos: dict) -> None:
        total = sum(f["noticias"] for f in tabla)
        categorias = len(conteos)
        periodos = len({f["periodo"] for f in tabla})
        self.stat_noticias_var.set(str(total))
        self.stat_categorias_var.set(str(categorias))
        self.stat_periodos_var.set(str(periodos))

        lineas = [viz, "", "  TABLA RESUMEN",
                  f"  {'Categoria':<15} {'Periodo':<12} {'Noticias':>8}",
                  "  " + "-" * 38]
        for fila in tabla:
            lineas.append(f"  {fila['categoria']:<15} {fila['periodo']:<12} {fila['noticias']:>8}")

        if pico["categoria"]:
            lineas += [
                "",
                "  PICO NOTABLE",
                f"  Categoria: {pico['categoria']} | Periodo: {pico['periodo']} | Noticias: {pico['count']}",
            ]
            for titulo in pico["titulos"][:3]:
                lineas.append(f"    - {titulo[:65]}")

        lineas += ["", "  CONCLUSION", ""]
        lineas += ["  " + l for l in conclusion.splitlines()]

        self._set_output("\n".join(lineas))
        self.estado_var.set("Analisis completado")
        self.btn_analizar.configure(state="normal")
        self.btn_exportar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(
            f"AC-9: {categorias} categorias, {periodos} periodos", "ok")

    def _exportar(self) -> None:
        if not self.analizador:
            return
        try:
            self.analizador.exportar_csv("data/ac9_tendencias.csv")
            self.analizador.guardar_reporte_json("reports/tendencias_ac9.json")
            self.analizador.guardar_conclusion_markdown("reports/conclusion_tendencias_ac9.md")
            self.root_app.set_estado("AC-9: CSV y Markdown exportados", "ok")
        except Exception as exc:
            messagebox.showerror("AC-9", str(exc))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_analizar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-9", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")
