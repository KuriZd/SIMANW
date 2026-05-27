"""Vista de Fase 2 — Procesamiento NLP.

Sigue el mismo patrón de layout que Fase1Frame:
  columna izquierda (fija): tarjetas de control / estadísticas
  columna derecha (expandible): tabla de corpus + panel de detalle

Toda la lógica NLP vive en Fase2Service; esta clase sólo gestiona la UI
y el threading.
"""
from __future__ import annotations

import threading
from tkinter import messagebox, ttk

import customtkinter as ctk

from src.fase2_service import Fase2Service, ResultadoFase2
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, THEME


class Fase2Frame(ctk.CTkFrame):
    """Panel de Fase 2: procesa, muestra estadísticas y exporta el corpus NLP."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app      = root_app
        self.service_fase2 = Fase2Service()
        self.corpus_procesado: list[dict] = []

        # StringVars para la tarjeta de estadísticas
        self.stat_docs_var     = ctk.StringVar(value="—")
        self.stat_tokens_var   = ctk.StringVar(value="—")
        self.stat_terminos_var = ctk.StringVar(value="—")
        self.stat_vocab_var    = ctk.StringVar(value="—")
        self.stat_prom_var     = ctk.StringVar(value="—")
        self.ultima_accion_var = ctk.StringVar(value="Sin acciones")

        self._config_treeview_style()
        self._build()

        # Restaurar corpus previo si el root_app ya tiene uno
        if root_app.corpus_procesado:
            self.corpus_procesado = list(root_app.corpus_procesado)
            self._poblar_tabla(self.corpus_procesado)
            self._actualizar_stats_vars(root_app.estadisticas_fase2)
            self.ultima_accion_var.set("Corpus previo restaurado")

        self._actualizar_botones()

    # ═══════════════════════════════════════════════════════════════════════════
    # Construcción de la UI
    # ═══════════════════════════════════════════════════════════════════════════

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
        right.grid_rowconfigure(0, weight=3)
        right.grid_rowconfigure(1, weight=2)

        self._build_nlp_card(left).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_export_card(left).grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self._build_stats_card(left).grid(row=2, column=0, sticky="ew")

        self._build_tabla_card(right).grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self._build_detalle_card(right).grid(row=1, column=0, sticky="nsew")

    def _card(self, master) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    # ── tarjeta procesamiento NLP ──────────────────────────────────────────────

    def _build_nlp_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Procesamiento NLP", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))

        self.hint_label = ctk.CTkLabel(
            card,
            text="Extrae noticias con Fase 1 primero.",
            font=FONT_META,
            text_color=THEME["warning"],
            anchor="w",
        )
        self.hint_label.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))

        self.btn_procesar = ctk.CTkButton(
            card,
            text="▶  Procesar corpus NLP",
            command=self.procesar_nlp,
            fg_color=THEME["accent"],
            hover_color=THEME["accent"],
            text_color=THEME["text_1"],
        )
        self.btn_procesar.grid(
            row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING)
        )

        ctk.CTkLabel(
            card, text="Última acción", font=FONT_META, text_color=THEME["text_2"], anchor="w"
        ).grid(row=3, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(
            card,
            textvariable=self.ultima_accion_var,
            font=FONT_BODY,
            text_color=THEME["text_1"],
            anchor="w",
        ).grid(row=4, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    # ── tarjeta exportación ────────────────────────────────────────────────────

    def _build_export_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Exportar corpus", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        self.btn_json = ctk.CTkButton(
            card,
            text="Exportar JSON",
            command=self.exportar_json,
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        )
        self.btn_json.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.btn_csv = ctk.CTkButton(
            card,
            text="Exportar CSV",
            command=self.exportar_csv,
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        )
        self.btn_csv.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.btn_todo = ctk.CTkButton(
            card,
            text="Exportar ambos",
            command=self.exportar_todo,
            fg_color=THEME["success"],
            hover_color=THEME["success"],
            text_color=THEME["bg_base"],
        )
        self.btn_todo.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    # ── tarjeta estadísticas ───────────────────────────────────────────────────

    def _build_stats_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Estadísticas", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        for row_offset, (label, var) in enumerate(
            [
                ("Documentos",         self.stat_docs_var),
                ("Tokens totales",     self.stat_tokens_var),
                ("Términos filtrados", self.stat_terminos_var),
                ("Vocabulario",        self.stat_vocab_var),
                ("Tokens / doc",       self.stat_prom_var),
            ],
            start=1,
        ):
            ctk.CTkLabel(
                card, text=label, font=FONT_META, text_color=THEME["text_2"], anchor="w"
            ).grid(row=row_offset * 2 - 1, column=0, sticky="w", padx=CARD_PADDING)
            ctk.CTkLabel(
                card, textvariable=var, font=FONT_BODY, text_color=THEME["text_1"], anchor="w"
            ).grid(row=row_offset * 2, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 6))
        return card

    # ── tabla de corpus ────────────────────────────────────────────────────────

    def _build_tabla_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            card, text="Corpus procesado", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        table_frame = ctk.CTkFrame(card, fg_color=THEME["bg_surface"], corner_radius=0)
        table_frame.grid(
            row=1, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING)
        )
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columnas = ("titulo", "categoria", "terminos_relevantes", "num_terminos", "riqueza_lexica")
        self.tabla = ttk.Treeview(
            table_frame, columns=columnas, show="headings", selectmode="browse"
        )
        for col, texto, ancho in [
            ("titulo",              "Título",          380),
            ("categoria",           "Categoría",       110),
            ("terminos_relevantes", "Términos TF-IDF", 220),
            ("num_terminos",        "N° términos",      90),
            ("riqueza_lexica",      "Riqueza léxica",  100),
        ]:
            self.tabla.heading(col, text=texto)
            self.tabla.column(
                col, width=ancho, anchor="w" if col == "titulo" else "center"
            )
        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabla.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.tabla.configure(yscrollcommand=scroll_y.set)
        return card

    # ── panel de detalle NLP ───────────────────────────────────────────────────

    def _build_detalle_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(4, weight=1)

        self.detalle_titulo = ctk.CTkLabel(
            card,
            text="Selecciona un documento",
            font=FONT_H2,
            text_color=THEME["text_1"],
            anchor="w",
        )
        self.detalle_titulo.grid(
            row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 4)
        )

        self.detalle_meta = ctk.CTkLabel(
            card, text="", font=FONT_META, text_color=THEME["text_2"], anchor="w"
        )
        self.detalle_meta.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 4))

        self.detalle_terminos = ctk.CTkLabel(
            card,
            text="",
            font=FONT_META,
            text_color=THEME["accent"],
            anchor="w",
            wraplength=560,
        )
        self.detalle_terminos.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))

        self.detalle_cuerpo = ctk.CTkTextbox(
            card,
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_1"],
            font=FONT_BODY,
            wrap="word",
        )
        self.detalle_cuerpo.grid(
            row=4, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING)
        )
        self.detalle_cuerpo.configure(state="disabled")
        return card

    # ═══════════════════════════════════════════════════════════════════════════
    # Acciones de negocio
    # ═══════════════════════════════════════════════════════════════════════════

    def procesar_nlp(self) -> None:
        noticias = self.root_app.noticias
        if not noticias:
            messagebox.showwarning("Fase 2", "Extrae noticias con la Fase 1 primero.")
            return
        self._set_running(True)
        self.root_app.set_estado(
            "Procesando NLP…", "loading", total_noticias=len(noticias)
        )
        self.root_app.show_progress()
        self.ultima_accion_var.set("Procesando…")
        threading.Thread(
            target=self._procesar_bg, args=(noticias,), daemon=True
        ).start()

    def _procesar_bg(self, noticias: list[dict]) -> None:
        try:
            resultado = self.service_fase2.procesar_corpus(noticias)
            self.after(0, lambda: self._on_resultado(resultado))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_resultado(self, resultado: ResultadoFase2) -> None:
        self.corpus_procesado = resultado.corpus
        self.root_app.set_corpus(resultado.corpus, resultado.estadisticas)

        self._poblar_tabla(resultado.corpus)
        self._actualizar_stats_vars(resultado.estadisticas)
        self.ultima_accion_var.set("Procesamiento completado")

        nivel = "warning" if resultado.errores else "ok"
        msg = f"{len(resultado.corpus)} documento(s) procesado(s)"
        if resultado.errores:
            msg += f"; {len(resultado.errores)} advertencia(s)"
        self.root_app.set_estado(msg, nivel, total_noticias=len(self.root_app.noticias))
        self.root_app.hide_progress()
        self._set_running(False)
        self._actualizar_botones()

        if resultado.errores:
            messagebox.showwarning("Fase 2 — Advertencias", "\n".join(resultado.errores))

    def _on_error(self, mensaje: str) -> None:
        self.ultima_accion_var.set("Error de procesamiento")
        self.root_app.hide_progress()
        self.root_app.set_estado(
            mensaje, "error", total_noticias=len(self.root_app.noticias)
        )
        self._set_running(False)
        self._actualizar_botones()
        messagebox.showerror("Fase 2", mensaje)

    def mostrar_detalle(self, _event=None) -> None:
        sel = self.tabla.selection()
        if not sel:
            return
        item = self.corpus_procesado[int(sel[0])]

        self.detalle_titulo.configure(text=item["titulo"])
        self.detalle_meta.configure(
            text=f"{item['categoria']}  ·  {item['fecha']}  ·  {item['autor']}"
        )
        relev_str = ", ".join(item["terminos_relevantes"]) or "—"
        self.detalle_terminos.configure(text=f"TF-IDF: {relev_str}")

        terminos_str = ", ".join(item["terminos"][:30]) or "—"
        stems_str    = ", ".join(item["stems"][:20])    or "—"
        tokens_str   = " ".join(item["tokens"][:40])
        if len(item["tokens"]) > 40:
            tokens_str += " …"

        texto = (
            f"═══ TEXTO ORIGINAL ═══\n{item['texto_original']}\n\n"
            f"═══ TEXTO LIMPIO ═══\n{item['texto_limpio']}\n\n"
            f"═══ TOKENS  ({item['num_tokens']}) ═══\n{tokens_str}\n\n"
            f"═══ TÉRMINOS FILTRADOS  ({item['num_terminos']}) ═══\n{terminos_str}\n\n"
            f"═══ STEMS ═══\n{stems_str}\n\n"
            f"Oraciones: {item['num_oraciones']}  ·  "
            f"Vocabulario único: {item['vocabulario_unico']}  ·  "
            f"Riqueza léxica: {item['riqueza_lexica']:.4f}"
        )

        self.detalle_cuerpo.configure(state="normal")
        self.detalle_cuerpo.delete("1.0", "end")
        self.detalle_cuerpo.insert("1.0", texto)
        self.detalle_cuerpo.configure(state="disabled")

    # ── exportación ───────────────────────────────────────────────────────────

    def exportar_json(self) -> None:
        self._exportar("json")

    def exportar_csv(self) -> None:
        self._exportar("csv")

    def exportar_todo(self) -> None:
        self._exportar("todo")

    def _exportar(self, formato: str) -> None:
        if not self.corpus_procesado:
            self.root_app.set_estado("No hay corpus para exportar.", "warning")
            return
        try:
            if formato == "json":
                ruta = self.service_fase2.exportar_json(self.corpus_procesado)
                msg = f"JSON exportado: {ruta}"
            elif formato == "csv":
                ruta = self.service_fase2.exportar_csv(self.corpus_procesado)
                msg = f"CSV exportado: {ruta}"
            else:
                rutas = self.service_fase2.exportar_todo(self.corpus_procesado)
                msg = f"Exportados: {rutas['json']} y {rutas['csv']}"
            self.ultima_accion_var.set("Exportación completada")
            self.root_app.set_estado(
                msg, "ok", total_noticias=len(self.root_app.noticias)
            )
        except Exception as exc:
            self.ultima_accion_var.set("Error de exportación")
            self.root_app.set_estado(
                str(exc), "error", total_noticias=len(self.root_app.noticias)
            )
            messagebox.showerror("Exportación", str(exc))

    # ═══════════════════════════════════════════════════════════════════════════
    # Helpers internos
    # ═══════════════════════════════════════════════════════════════════════════

    def _poblar_tabla(self, corpus: list[dict]) -> None:
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for idx, item in enumerate(corpus):
            relev = ", ".join(item["terminos_relevantes"][:5]) or "—"
            self.tabla.insert(
                "", "end", iid=str(idx),
                values=(
                    item["titulo"],
                    item["categoria"],
                    relev,
                    item["num_terminos"],
                    f"{item['riqueza_lexica']:.4f}",
                ),
            )

    def _actualizar_stats_vars(self, estadisticas: dict) -> None:
        self.stat_docs_var.set(str(estadisticas.get("total_documentos", "—")))
        self.stat_tokens_var.set(str(estadisticas.get("total_tokens", "—")))
        vocab = estadisticas.get("vocabulario_total", "—")
        self.stat_terminos_var.set(str(estadisticas.get("stems_unicos", vocab)))
        self.stat_vocab_var.set(str(vocab))
        prom = estadisticas.get("promedio_tokens_doc")
        self.stat_prom_var.set(
            f"{prom:.1f}" if isinstance(prom, (int, float)) else "—"
        )

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.btn_procesar.configure(state=state)

    def _actualizar_botones(self) -> None:
        tiene_noticias = bool(self.root_app.noticias)
        tiene_corpus   = bool(self.corpus_procesado)

        self.btn_procesar.configure(state="normal" if tiene_noticias else "disabled")
        self.hint_label.configure(
            text="" if tiene_noticias else "Extrae noticias con Fase 1 primero.",
        )

        export_state = "normal" if tiene_corpus else "disabled"
        self.btn_json.configure(state=export_state)
        self.btn_csv.configure(state=export_state)
        self.btn_todo.configure(state=export_state)

    @staticmethod
    def _config_treeview_style() -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=THEME["bg_input"],
            fieldbackground=THEME["bg_input"],
            foreground=THEME["text_1"],
            rowheight=30,
            bordercolor=THEME["border"],
            lightcolor=THEME["border"],
            darkcolor=THEME["border"],
            font=FONT_BODY,
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["bg_surface"],
            foreground=THEME["text_1"],
            bordercolor=THEME["border"],
            relief="flat",
            font=FONT_H2,
        )
        style.map(
            "Treeview",
            background=[("selected", THEME["accent"])],
            foreground=[("selected", THEME["text_1"])],
        )
        style.map("Treeview.Heading", background=[("active", THEME["border"])])
