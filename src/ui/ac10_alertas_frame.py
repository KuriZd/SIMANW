"""AC-10: Sistema de alertas por consulta guardada."""
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.alertas_consulta import (
    SistemaAlertasConsulta,
    consultas_demo,
    noticias_nuevas_demo,
)
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME


class Ac10AlertasFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.sistema = SistemaAlertasConsulta(consultas_demo())

        self.stat_consultas_var = ctk.StringVar(value=str(len(self.sistema.consultas)))
        self.stat_alertas_var = ctk.StringVar(value="0")
        self.nombre_var = ctk.StringVar()
        self.expresion_var = ctk.StringVar()
        self.estado_var = ctk.StringVar(value="Listo")
        self._build()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=260, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self._build_nueva_consulta_card(left).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_acciones_card(left).grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self._build_metricas_card(left).grid(row=2, column=0, sticky="ew")
        self._build_titulo_card(right).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_output_card(right).grid(row=1, column=0, sticky="nsew")

    def _build_nueva_consulta_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Nueva consulta guardada", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        ctk.CTkLabel(card, text="Nombre", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkEntry(card, textvariable=self.nombre_var,
                     placeholder_text="p.ej. IA generativa",
                     fg_color=THEME["bg_input"], border_color=THEME["border"],
                     border_width=1, text_color=THEME["text_1"]).grid(
            row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        ctk.CTkLabel(card, text="Expresion de busqueda", font=FONT_META,
                     text_color=THEME["text_2"]).grid(
            row=3, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkEntry(card, textvariable=self.expresion_var,
                     placeholder_text='p.ej. "inteligencia artificial"',
                     fg_color=THEME["bg_input"], border_color=THEME["border"],
                     border_width=1, text_color=THEME["text_1"]).grid(
            row=4, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        ctk.CTkButton(card, text="Agregar consulta", command=self._agregar,
                       fg_color=THEME["accent"], hover_color=THEME["accent"],
                       text_color=THEME["text_1"]).grid(
            row=5, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_acciones_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Procesar noticias nuevas", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        self.btn_procesar = ctk.CTkButton(
            card, text="Ejecutar 5 noticias demo", command=self._procesar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_procesar.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        self.btn_exportar = ctk.CTkButton(
            card, text="Guardar historial + Markdown", command=self._exportar,
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"])
        self.btn_exportar.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        ctk.CTkLabel(card, text="Estado", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=3, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(card, textvariable=self.estado_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=4, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_metricas_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        for i, (label, var) in enumerate([
            ("Consultas activas", self.stat_consultas_var),
            ("Alertas generadas", self.stat_alertas_var),
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
        ctk.CTkLabel(card, text="Historial de alertas", font=FONT_H2,
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

    def _agregar(self) -> None:
        nombre = self.nombre_var.get().strip()
        expresion = self.expresion_var.get().strip()
        if not nombre or not expresion:
            messagebox.showwarning("AC-10", "Completa nombre y expresion.")
            return
        self.sistema.agregar_consulta(nombre, expresion)
        self.stat_consultas_var.set(str(len(self.sistema.consultas)))
        self.nombre_var.set("")
        self.expresion_var.set("")
        self._refresh_output()
        self.root_app.set_estado(f"AC-10: consulta '{nombre}' agregada", "ok")

    def _procesar(self) -> None:
        self.btn_procesar.configure(state="disabled")
        self.estado_var.set("Procesando…")
        threading.Thread(target=self._procesar_bg, daemon=True).start()

    def _procesar_bg(self) -> None:
        try:
            alertas = self.sistema.procesar_noticias_nuevas(noticias_nuevas_demo())
            self.after(0, lambda: self._on_procesar_ok(alertas))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_procesar_ok(self, alertas: list) -> None:
        self.stat_alertas_var.set(str(len(self.sistema.historial_alertas)))
        self.estado_var.set(f"{len(alertas)} alertas nuevas")
        self._refresh_output()
        self.btn_procesar.configure(state="normal")
        self.root_app.set_estado(
            f"AC-10: {len(alertas)} alertas nuevas, "
            f"{len(self.sistema.historial_alertas)} total", "ok")

    def _exportar(self) -> None:
        try:
            self.sistema.guardar_consultas("data/ac10_consultas_guardadas.json")
            self.sistema.guardar_historial("data/ac10_historial_alertas.json")
            self.sistema.guardar_reporte_markdown("reports/alertas_ac10.md")
            self.root_app.set_estado("AC-10: historial y Markdown exportados", "ok")
        except Exception as exc:
            messagebox.showerror("AC-10", str(exc))

    def _refresh_output(self) -> None:
        lineas = [f"  Consultas activas: {len(self.sistema.consultas)}",
                  f"  Alertas en historial: {len(self.sistema.historial_alertas)}", ""]
        lineas.append("  CONSULTAS GUARDADAS")
        for c in self.sistema.consultas:
            lineas.append(f"    [{c.nombre}]  {c.expresion}")
        if self.sistema.historial_alertas:
            lineas += ["", "  HISTORIAL DE ALERTAS"]
            for a in self.sistema.historial_alertas[-20:]:
                lineas.append(f"    {a['consulta']:<22} {a['titulo'][:45]}")
        else:
            lineas += ["", "  (Sin alertas generadas aun)"]
        self._set_output("\n".join(lineas))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_procesar.configure(state="normal")
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-10", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")
