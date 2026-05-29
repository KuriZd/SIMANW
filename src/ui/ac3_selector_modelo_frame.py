"""AC-3: Seleccion automatica de modelo de clasificacion."""
# LEGACY UI: este frame no forma parte del sidebar principal de app_desktop.py.
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.selector_modelo import ETIQUETAS_AC3, TEXTOS_AC3, SelectorModelo
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME


class Ac3SelectorModeloFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.selector: SelectorModelo | None = None

        self.estado_var = ctk.StringVar(value="Sin evaluar")
        self.mejor_modelo_var = ctk.StringVar(value="—")
        self.texto_pred_var = ctk.StringVar()

        self._build()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=280, weight=0)
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
        self._build_pred_card(left).grid(row=1, column=0, sticky="ew")

        self._build_stats_card(right).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_output_card(right).grid(row=1, column=0, sticky="nsew")

    def _build_control_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Evaluacion de modelos", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        ctk.CTkLabel(card, text="Corpus de entrenamiento: 20 textos / 4 categorias\nValidacion cruzada: 3 pliegues",
                     font=FONT_META, text_color=THEME["text_2"], justify="left").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10))
        self.btn_evaluar = ctk.CTkButton(card, text="Evaluar 4 modelos",
                                         command=self._evaluar,
                                         fg_color=THEME["accent"],
                                         hover_color=THEME["accent"],
                                         text_color=THEME["text_1"], height=36)
        self.btn_evaluar.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        ctk.CTkLabel(card, text="Ultimo estado", font=FONT_META,
                     text_color=THEME["text_2"]).grid(
            row=3, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(card, textvariable=self.estado_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=4, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_pred_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(card, text="Prediccion libre", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        self.txt_pred = ctk.CTkTextbox(card, height=80, fg_color=THEME["bg_input"],
                                        border_color=THEME["border"], border_width=1,
                                        text_color=THEME["text_1"], font=FONT_BODY, wrap="word")
        self.txt_pred.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        self.txt_pred.insert("1.0", "nueva aplicacion de machine learning para detectar fraudes")
        self.btn_predecir = ctk.CTkButton(card, text="Predecir categoria",
                                           command=self._predecir,
                                           fg_color=THEME["bg_input"],
                                           hover_color=THEME["border"],
                                           border_width=1, border_color=THEME["border"],
                                           text_color=THEME["text_1"], state="disabled")
        self.btn_predecir.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING,
                                pady=(0, CARD_PADDING))
        return card

    def _build_stats_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text="Mejor modelo", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        ctk.CTkLabel(card, textvariable=self.mejor_modelo_var, font=FONT_BODY,
                     text_color=THEME["success"], anchor="w").grid(
            row=0, column=1, sticky="w", padx=(0, CARD_PADDING), pady=(CARD_PADDING, 6))
        return card

    def _build_output_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(card, text="Resultados", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        self.output_box = ctk.CTkTextbox(card, fg_color=THEME["bg_input"],
                                          border_color=THEME["border"], border_width=1,
                                          text_color=THEME["text_1"], font=FONT_MONO,
                                          wrap="none", state="disabled")
        self.output_box.grid(row=1, column=0, sticky="nsew",
                              padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _evaluar(self) -> None:
        self.btn_evaluar.configure(state="disabled")
        self.estado_var.set("Evaluando…")
        self.root_app.set_estado("AC-3: evaluando modelos…", "loading")
        self.root_app.show_progress()
        threading.Thread(target=self._evaluar_bg, daemon=True).start()

    def _evaluar_bg(self) -> None:
        try:
            self.selector = SelectorModelo()
            self.selector.evaluar_todos(TEXTOS_AC3, ETIQUETAS_AC3, cv_folds=3)
            self.after(0, self._on_evaluacion_ok)
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_evaluacion_ok(self) -> None:
        reporte = self.selector.reporte()
        nombre_mejor = self.selector.mejor_modelo[0] if self.selector.mejor_modelo else "N/A"
        self.mejor_modelo_var.set(nombre_mejor)
        self.estado_var.set("Evaluacion completada")
        self._set_output(reporte)
        self.btn_evaluar.configure(state="normal")
        self.btn_predecir.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(f"AC-3: mejor modelo = {nombre_mejor}", "ok")

    def _predecir(self) -> None:
        if not self.selector or not self.selector.mejor_modelo:
            messagebox.showwarning("AC-3", "Evalua los modelos primero.")
            return
        texto = self.txt_pred.get("1.0", "end").strip()
        if not texto:
            messagebox.showwarning("AC-3", "Escribe un texto para predecir.")
            return
        try:
            resultado = self.selector.predecir([texto])[0]
            self._append_output(f"\n  Prediccion: [{resultado}]  {texto[:60]}")
            self.root_app.set_estado(f"AC-3: prediccion = {resultado}", "ok")
        except Exception as exc:
            self._on_error(str(exc))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_evaluar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-3", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")

    def _append_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.insert("end", texto)
        self.output_box.configure(state="disabled")
        self.output_box.see("end")
