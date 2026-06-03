"""AC-5: Comparacion de modelos booleano vs. vectorial."""
# LEGACY UI: este frame no forma parte del sidebar principal de app_desktop.py.
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.comparador_busqueda import CONSULTAS_EVAL_AC5, ComparadorModelos
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME

_NOTICIAS_DEMO = [
    {"titulo": "Avances en inteligencia artificial generativa",
     "cuerpo": "La inteligencia artificial y el aprendizaje automatico impulsan nuevas aplicaciones."},
    {"titulo": "Mercados financieros muestran volatilidad",
     "cuerpo": "La inflacion y las tasas de interes presionan al mercado de valores."},
    {"titulo": "Descubrimiento cientifico sobre cambio climatico",
     "cuerpo": "Investigadores publican datos sobre emisiones de carbono y calentamiento global."},
    {"titulo": "Python mejora herramientas de programacion",
     "cuerpo": "La nueva version de Python ayuda al desarrollo de software e inteligencia artificial."},
    {"titulo": "Gobierno publica datos abiertos",
     "cuerpo": "El gobierno libera datos abiertos para fortalecer transparencia y politicas publicas."},
]


class Ac5ComparadorFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.comparador: ComparadorModelos | None = None

        self.ganador_var = ctk.StringVar(value="—")
        self.estado_var = ctk.StringVar(value="Sin evaluar")
        self._build()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=270, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self._build_eval_card(left).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_busqueda_card(left).grid(row=1, column=0, sticky="ew")
        self._build_metrics_card(right).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_output_card(right).grid(row=1, column=0, sticky="nsew")

    def _build_eval_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Evaluacion comparativa", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        ctk.CTkLabel(card,
                     text="4 consultas de referencia\n5 documentos demo",
                     font=FONT_META, text_color=THEME["text_2"], justify="left").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10))
        self.btn_evaluar = ctk.CTkButton(
            card, text="Evaluar ambos modelos", command=self._evaluar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_evaluar.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        ctk.CTkLabel(card, text="Estado", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=3, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(card, textvariable=self.estado_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=4, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_busqueda_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(card, text="Busqueda manual", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        self.entry_consulta = ctk.CTkEntry(
            card, placeholder_text="Escribe una consulta…",
            fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1,
            text_color=THEME["text_1"])
        self.entry_consulta.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        self.btn_buscar = ctk.CTkButton(
            card, text="Buscar en ambos modelos", command=self._buscar,
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"], state="disabled")
        self.btn_buscar.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING,
                              pady=(0, CARD_PADDING))
        return card

    def _build_metrics_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text="Ganador F1", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, CARD_PADDING))
        ctk.CTkLabel(card, textvariable=self.ganador_var, font=FONT_BODY,
                     text_color=THEME["success"], anchor="w").grid(
            row=0, column=1, sticky="w", padx=(0, CARD_PADDING), pady=(CARD_PADDING, CARD_PADDING))
        return card

    def _build_output_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(card, text="Reporte de evaluacion", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        self.output_box = ctk.CTkTextbox(
            card, fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1,
            text_color=THEME["text_1"], font=FONT_MONO, wrap="none", state="disabled")
        self.output_box.grid(row=1, column=0, sticky="nsew",
                              padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _evaluar(self) -> None:
        self.btn_evaluar.configure(state="disabled")
        self.estado_var.set("Evaluando…")
        self.root_app.set_estado("AC-5: comparando modelos…", "loading")
        self.root_app.show_progress()
        docs = self.root_app.noticias or _NOTICIAS_DEMO
        threading.Thread(target=self._evaluar_bg, args=(docs,), daemon=True).start()

    def _evaluar_bg(self, docs: list[dict]) -> None:
        try:
            self.comparador = ComparadorModelos(docs)
            reporte = self.comparador.reporte(CONSULTAS_EVAL_AC5)
            evaluacion = self.comparador.evaluar_consultas(CONSULTAS_EVAL_AC5)
            conclusion = self.comparador.generar_conclusion(evaluacion)
            ganador = evaluacion["ganador_f1"]
            self.after(0, lambda: self._on_ok(reporte, conclusion, ganador))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_ok(self, reporte: str, conclusion: str, ganador: str) -> None:
        self.ganador_var.set(ganador)
        self.estado_var.set("Evaluacion completada")
        self._set_output(reporte + f"\n\nConclusión: {conclusion}")
        self.btn_evaluar.configure(state="normal")
        self.btn_buscar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(f"AC-5: ganador F1 = {ganador}", "ok")

    def _buscar(self) -> None:
        if not self.comparador:
            messagebox.showwarning("AC-5", "Evalua los modelos primero.")
            return
        consulta = self.entry_consulta.get().strip()
        if not consulta:
            return
        bool_res = self.comparador.busqueda_booleana(consulta)
        vec_res = self.comparador.busqueda_vectorial(consulta, top_k=5)
        lineas = [f"\n  -- BUSQUEDA: '{consulta}' --",
                  f"  Booleano ({len(bool_res)} docs): {bool_res}",
                  "  Vectorial top-5:"]
        for idx, score in vec_res:
            doc = self.comparador.documentos[idx]
            lineas.append(f"    [{score:.3f}] {doc['titulo'][:55]}")
        self._append_output("\n".join(lineas))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_evaluar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-5", msg)

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
