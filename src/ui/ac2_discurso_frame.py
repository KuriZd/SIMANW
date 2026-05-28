"""AC-2: Análisis estadístico de discursos — panel de escritorio."""
from __future__ import annotations

import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from src.analisis_discurso import AnalisisDiscurso
from src.nltk_setup import descargar_recursos
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME

_TEXTO_DISCURSO = (
    "La educacion es la herramienta mas poderosa para transformar una sociedad. "
    "En Mexico, la inversion en educacion debe ser prioritaria para garantizar el desarrollo "
    "economico y social. Los jovenes mexicanos merecen oportunidades de calidad en todos los "
    "niveles educativos. Las universidades tecnologicas y los institutos de investigacion son "
    "pilares fundamentales para la innovacion. La ciencia y la tecnologia son motores del "
    "progreso nacional. El Instituto Tecnologico de Morelia ha formado generaciones de "
    "ingenieros que contribuyen al desarrollo del pais. La inteligencia artificial y la "
    "programacion son competencias esenciales para el futuro laboral. Mexico necesita mas "
    "profesionales en ciencias computacionales y recuperacion de informacion."
)

_TEXTO_CIENTIFICO = (
    "El procesamiento de lenguaje natural permite a las computadoras comprender y generar texto "
    "humano. Los modelos de aprendizaje profundo como BERT y GPT han revolucionado este campo. "
    "La representacion vectorial de documentos mediante TF-IDF sigue siendo fundamental para "
    "sistemas de recuperacion de informacion. Los algoritmos de clasificacion como Naive Bayes y "
    "SVM logran alta precision en categorizacion de texto. El analisis de sentimientos combina "
    "tecnicas lexicas con aprendizaje automatico para determinar la polaridad emocional de un texto."
)

_TEXTOS = {
    "Discurso Educativo": _TEXTO_DISCURSO,
    "Texto Científico NLP": _TEXTO_CIENTIFICO,
    "Personalizado": "",
}

_SALIDA_JSON = Path("data") / "analisis_ac2.json"


class Ac2DiscursoFrame(ctk.CTkFrame):
    """AC-2: Análisis estadístico de discursos y textos largos."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.analizador = AnalisisDiscurso()
        self.analisis_actual: dict | None = None
        self.todos_analisis: list[dict] = []

        self.texto_sel_var = ctk.StringVar(value="Discurso Educativo")
        self.stat_oraciones_var = ctk.StringVar(value="—")
        self.stat_palabras_var = ctk.StringVar(value="—")
        self.stat_vocab_var = ctk.StringVar(value="—")
        self.stat_riqueza_var = ctk.StringVar(value="—")
        self.stat_prom_var = ctk.StringVar(value="—")
        self.ultima_accion_var = ctk.StringVar(value="Sin acciones")

        descargar_recursos()
        self._build()

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=310, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self._build_texto_card(left).grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self._build_control_card(left).grid(row=1, column=0, sticky="ew")

        self._build_stats_card(right).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_resultados_card(right).grid(row=1, column=0, sticky="nsew")

    def _card(self, master) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _build_texto_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(card, text="Texto a analizar", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6)
        )

        self.selector_texto = ctk.CTkOptionMenu(
            card,
            values=list(_TEXTOS),
            variable=self.texto_sel_var,
            command=lambda _: self._cargar_predefinido(),
            fg_color=THEME["bg_input"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"],
            dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"],
        )
        self.selector_texto.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.textbox = ctk.CTkTextbox(
            card,
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_1"],
            font=FONT_BODY,
            wrap="word",
        )
        self.textbox.grid(row=2, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self._cargar_predefinido()
        return card

    def _build_control_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)

        self.btn_analizar = ctk.CTkButton(
            card,
            text="▶  Analizar texto",
            command=self._analizar,
            fg_color=THEME["accent"],
            hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            height=36,
        )
        self.btn_analizar.grid(row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        self.btn_guardar = ctk.CTkButton(
            card,
            text="Guardar JSON",
            command=self._guardar_json,
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
            state="disabled",
        )
        self.btn_guardar.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        ctk.CTkLabel(card, text="Última acción", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=2, column=0, sticky="w", padx=CARD_PADDING
        )
        ctk.CTkLabel(
            card,
            textvariable=self.ultima_accion_var,
            font=FONT_BODY,
            text_color=THEME["text_1"],
            anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_stats_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="Estadísticas", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )

        metricas = [
            ("Oraciones",          self.stat_oraciones_var),
            ("Palabras totales",   self.stat_palabras_var),
            ("Vocabulario único",  self.stat_vocab_var),
            ("Riqueza léxica",     self.stat_riqueza_var),
            ("Prom. pal./oración", self.stat_prom_var),
        ]
        for idx, (label, var) in enumerate(metricas):
            col = idx % 2
            row_base = (idx // 2) * 2 + 1
            px = CARD_PADDING if col == 0 else 6
            ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=row_base, column=col, sticky="w", padx=(px, 4)
            )
            ctk.CTkLabel(card, textvariable=var, font=FONT_BODY, text_color=THEME["text_1"]).grid(
                row=row_base + 1, column=col, sticky="w", padx=(px, 4), pady=(0, 6)
            )
        return card

    def _build_resultados_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(card, text="N-gramas y entidades", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6)
        )

        self.resultados_box = ctk.CTkTextbox(
            card,
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_1"],
            font=FONT_MONO,
            wrap="none",
            state="disabled",
        )
        self.resultados_box.grid(row=1, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _analizar(self) -> None:
        texto = self.textbox.get("1.0", "end").strip()
        if not texto:
            messagebox.showwarning("AC-2", "Ingresa o selecciona un texto para analizar.")
            return

        titulo = self.texto_sel_var.get()
        self.btn_analizar.configure(state="disabled")
        self.ultima_accion_var.set("Analizando…")
        self.root_app.set_estado("Analizando texto…", "loading")
        self.root_app.show_progress()
        threading.Thread(target=self._analizar_bg, args=(texto, titulo), daemon=True).start()

    def _analizar_bg(self, texto: str, titulo: str) -> None:
        try:
            resultado = self.analizador.analizar(texto, titulo)
            self.after(0, lambda: self._on_resultado(resultado))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_resultado(self, resultado: dict) -> None:
        self.analisis_actual = resultado
        if not any(a["titulo"] == resultado["titulo"] for a in self.todos_analisis):
            self.todos_analisis.append(resultado)

        self.stat_oraciones_var.set(str(resultado["oraciones"]))
        self.stat_palabras_var.set(str(resultado["palabras_totales"]))
        self.stat_vocab_var.set(str(resultado["vocabulario_unico"]))
        self.stat_riqueza_var.set(f"{resultado['riqueza_lexica_global']:.3f}")
        self.stat_prom_var.set(f"{resultado['promedio_palabras_oracion']:.1f}")

        self._renderizar_resultados(resultado)
        self.ultima_accion_var.set(f"'{resultado['titulo']}' analizado")
        self.btn_analizar.configure(state="normal")
        self.btn_guardar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(
            f"AC-2: '{resultado['titulo']}' — "
            f"{resultado['palabras_totales']} palabras, "
            f"riqueza {resultado['riqueza_lexica_global']:.3f}",
            "ok",
        )

    def _on_error(self, mensaje: str) -> None:
        self.ultima_accion_var.set("Error de análisis")
        self.btn_analizar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(mensaje, "error")
        messagebox.showerror("AC-2 — Error", mensaje)

    def _renderizar_resultados(self, resultado: dict) -> None:
        lineas: list[str] = []

        sec = " | ".join(f"{v:.3f}" for v in resultado["riqueza_por_seccion"])
        lineas += ["  RIQUEZA POR SECCIÓN", f"  {sec}", ""]

        lineas.append("  TOP BIGRAMAS")
        for (w1, w2), cnt in resultado["top_bigramas"][:7]:
            lineas.append(f"    {w1} {w2:<26}  {cnt}")
        lineas.append("")

        lineas.append("  TOP TRIGRAMAS")
        for (w1, w2, w3), cnt in resultado["top_trigramas"][:5]:
            lineas.append(f"    {w1} {w2} {w3:<22}  {cnt}")
        lineas.append("")

        lineas.append("  ENTIDADES DETECTADAS")
        for entidad, cnt in resultado["posibles_entidades"]:
            lineas.append(f"    {entidad:<28}  {cnt}")

        if len(self.todos_analisis) >= 2:
            lineas += ["", "  COMPARATIVA"]
            comparativa = self.analizador.comparar_textos(self.todos_analisis)
            encabezado = f"    {'Texto':<22} {'Pal':>6} {'Vocab':>6} {'Riqueza':>8}  {'Top bigrama'}"
            lineas += [encabezado, "    " + "─" * (len(encabezado) - 4)]
            for fila in comparativa:
                lineas.append(
                    f"    {fila['titulo']:<22} {fila['palabras']:>6} {fila['vocabulario']:>6} "
                    f"{fila['riqueza']:>8.3f}  {fila['top_bigrama']}"
                )

        self.resultados_box.configure(state="normal")
        self.resultados_box.delete("1.0", "end")
        self.resultados_box.insert("1.0", "\n".join(lineas))
        self.resultados_box.configure(state="disabled")

    def _guardar_json(self) -> None:
        if not self.todos_analisis:
            return
        try:
            comparativa = self.analizador.comparar_textos(self.todos_analisis)
            AnalisisDiscurso.guardar_json(_SALIDA_JSON, self.todos_analisis, comparativa)
            self.ultima_accion_var.set(f"JSON guardado: {_SALIDA_JSON.name}")
            self.root_app.set_estado(f"JSON exportado: {_SALIDA_JSON}", "ok")
        except Exception as exc:
            messagebox.showerror("Exportar", str(exc))

    def _cargar_predefinido(self) -> None:
        texto = _TEXTOS.get(self.texto_sel_var.get(), "")
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        if texto:
            self.textbox.insert("1.0", texto)
