"""Sección 'Resultados NLP' — corpus procesado con estadísticas y detalle."""
from __future__ import annotations

from tkinter import messagebox, ttk

import customtkinter as ctk

from src.fase2_service import Fase2Service
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, THEME


class SeccionResultados(ctk.CTkFrame):
    """Muestra el corpus NLP: tabla, panel de detalle y estadísticas."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.corpus: list[dict] = list(root_app.corpus_procesado)
        self._service = Fase2Service()
        self._config_treeview_style()
        self._build()

    # ═══════════════════════════════════════════════════════════════════════════
    # Layout
    # ═══════════════════════════════════════════════════════════════════════════

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if not self.corpus:
            self._build_empty_state()
        else:
            self._build_content()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build_empty_state(self) -> None:
        center = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        center.grid(row=0, column=0)

        ctk.CTkLabel(
            center, text="Sin resultados NLP", font=FONT_H1, text_color=THEME["text_2"]
        ).grid(row=0, column=0, pady=(0, 8))
        ctk.CTkLabel(
            center,
            text="Carga y analiza noticias para ver los resultados.",
            font=FONT_BODY,
            text_color=THEME["text_2"],
        ).grid(row=1, column=0, pady=(0, 20))
        ctk.CTkButton(
            center,
            text="Cargar noticias",
            command=lambda: self.root_app.show_section("cargar"),
            fg_color=THEME["accent"],
            hover_color=THEME["accent"],
            text_color=THEME["text_1"],
        ).grid(row=2, column=0)

    def _build_content(self) -> None:
        stats = self.root_app.estadisticas_fase2

        self.grid_columnconfigure(0, minsize=260, weight=0)
        self.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=3)
        right.grid_rowconfigure(1, weight=2)

        self._build_stats_card(left, stats).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_export_card(left).grid(row=1, column=0, sticky="ew")

        self._build_tabla_card(right).grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self._build_detalle_card(right).grid(row=1, column=0, sticky="nsew")

        self._poblar_tabla()

    def _build_stats_card(self, master, stats: dict) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Estadísticas NLP", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        items = [
            ("Documentos",         str(stats.get("total_documentos", "—"))),
            ("Tokens totales",     str(stats.get("total_tokens", "—"))),
            ("Términos filtrados", str(stats.get("stems_unicos", "—"))),
            ("Vocabulario",        str(stats.get("vocabulario_total", "—"))),
            ("Tokens / doc",       _fmt_float(stats.get("promedio_tokens_doc"))),
        ]
        for row, (lbl, val) in enumerate(items, start=1):
            ctk.CTkLabel(card, text=lbl, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=row * 2 - 1, column=0, sticky="w", padx=CARD_PADDING
            )
            ctk.CTkLabel(card, text=val, font=FONT_BODY, text_color=THEME["text_1"]).grid(
                row=row * 2, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 6)
            )
        return card

    def _build_export_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Exportar corpus NLP", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        self.btn_json = ctk.CTkButton(
            card, text="Exportar JSON", command=lambda: self._exportar("json"),
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"], text_color=THEME["text_1"],
        )
        self.btn_json.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.btn_csv = ctk.CTkButton(
            card, text="Exportar CSV", command=lambda: self._exportar("csv"),
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"], text_color=THEME["text_1"],
        )
        self.btn_csv.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.btn_todo = ctk.CTkButton(
            card, text="Exportar ambos", command=lambda: self._exportar("todo"),
            fg_color=THEME["success"], hover_color=THEME["success"], text_color=THEME["bg_base"],
        )
        self.btn_todo.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_tabla_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            card, text="Corpus procesado", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        table_frame = ctk.CTkFrame(card, fg_color=THEME["bg_surface"], corner_radius=0)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = ("titulo", "categoria", "terminos_relevantes", "num_terminos", "riqueza_lexica")
        self.tabla = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        for col, texto, ancho in [
            ("titulo", "Título", 360), ("categoria", "Categoría", 110),
            ("terminos_relevantes", "Términos TF-IDF", 220),
            ("num_terminos", "N° términos", 90), ("riqueza_lexica", "Riqueza léxica", 100),
        ]:
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="w" if col == "titulo" else "center")

        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<<TreeviewSelect>>", self._mostrar_detalle)
        ttk.Scrollbar(table_frame, orient="vertical", command=self.tabla.yview).grid(
            row=0, column=1, sticky="ns"
        )
        return card

    def _build_detalle_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(3, weight=1)

        self._det_titulo = ctk.CTkLabel(
            card, text="Selecciona un documento", font=FONT_H2,
            text_color=THEME["text_1"], anchor="w",
        )
        self._det_titulo.grid(row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 4))

        self._det_meta = ctk.CTkLabel(card, text="", font=FONT_META, text_color=THEME["text_2"], anchor="w")
        self._det_meta.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 4))

        self._det_terminos = ctk.CTkLabel(
            card, text="", font=FONT_META, text_color=THEME["accent"], anchor="w", wraplength=560
        )
        self._det_terminos.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))

        self._det_cuerpo = ctk.CTkTextbox(
            card, fg_color=THEME["bg_input"], border_color=THEME["border"],
            border_width=1, text_color=THEME["text_1"], font=FONT_BODY, wrap="word",
        )
        self._det_cuerpo.grid(row=3, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self._det_cuerpo.configure(state="disabled")
        return card

    # ═══════════════════════════════════════════════════════════════════════════
    # Acciones
    # ═══════════════════════════════════════════════════════════════════════════

    def _poblar_tabla(self) -> None:
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for idx, item in enumerate(self.corpus):
            relev = ", ".join(item.get("terminos_relevantes", [])[:5]) or "—"
            self.tabla.insert(
                "", "end", iid=str(idx),
                values=(
                    item["titulo"], item["categoria"], relev,
                    item["num_terminos"], f"{item['riqueza_lexica']:.4f}",
                ),
            )

    def _mostrar_detalle(self, _event=None) -> None:
        sel = self.tabla.selection()
        if not sel:
            return
        item = self.corpus[int(sel[0])]

        self._det_titulo.configure(text=item["titulo"])
        self._det_meta.configure(
            text=f"{item['categoria']}  ·  {item['fecha']}  ·  {item['autor']}"
        )
        relev_str = ", ".join(item.get("terminos_relevantes", [])) or "—"
        self._det_terminos.configure(text=f"TF-IDF: {relev_str}")

        tokens_str  = " ".join(item["tokens"][:40]) + (" …" if len(item["tokens"]) > 40 else "")
        terminos_str = ", ".join(item["terminos"][:30]) or "—"
        stems_str    = ", ".join(item["stems"][:20])    or "—"

        texto = (
            f"═══ TEXTO ORIGINAL ═══\n{item['texto_original']}\n\n"
            f"═══ TEXTO LIMPIO ═══\n{item['texto_limpio']}\n\n"
            f"═══ TOKENS ({item['num_tokens']}) ═══\n{tokens_str}\n\n"
            f"═══ TÉRMINOS FILTRADOS ({item['num_terminos']}) ═══\n{terminos_str}\n\n"
            f"═══ STEMS ═══\n{stems_str}\n\n"
            f"Oraciones: {item['num_oraciones']}  ·  "
            f"Vocabulario único: {item['vocabulario_unico']}  ·  "
            f"Riqueza léxica: {item['riqueza_lexica']:.4f}"
        )
        self._det_cuerpo.configure(state="normal")
        self._det_cuerpo.delete("1.0", "end")
        self._det_cuerpo.insert("1.0", texto)
        self._det_cuerpo.configure(state="disabled")

    def _exportar(self, formato: str) -> None:
        try:
            if formato == "json":
                ruta = self._service.exportar_json(self.corpus)
                msg = f"JSON exportado: {ruta}"
            elif formato == "csv":
                ruta = self._service.exportar_csv(self.corpus)
                msg = f"CSV exportado: {ruta}"
            else:
                rutas = self._service.exportar_todo(self.corpus)
                msg = f"Exportados: {rutas['json']} y {rutas['csv']}"
            self.root_app.set_estado(msg, "ok", total_noticias=len(self.root_app.noticias))
        except Exception as exc:
            messagebox.showerror("Exportación", str(exc))
            self.root_app.set_estado(str(exc), "error")

    @staticmethod
    def _config_treeview_style() -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=THEME["bg_input"], fieldbackground=THEME["bg_input"],
            foreground=THEME["text_1"], rowheight=30,
            bordercolor=THEME["border"], lightcolor=THEME["border"],
            darkcolor=THEME["border"], font=FONT_BODY,
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["bg_surface"], foreground=THEME["text_1"],
            bordercolor=THEME["border"], relief="flat", font=FONT_H2,
        )
        style.map("Treeview",
                  background=[("selected", THEME["accent"])],
                  foreground=[("selected", THEME["text_1"])])
        style.map("Treeview.Heading", background=[("active", THEME["border"])])


def _fmt_float(value) -> str:
    return f"{value:.1f}" if isinstance(value, (int, float)) else "—"
