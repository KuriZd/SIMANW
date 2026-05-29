"""Seccion 'Explorador de noticias': tabla y detalle del corpus analizado."""
from __future__ import annotations

from tkinter import messagebox, ttk

import customtkinter as ctk

from src.fase1_service import Fase1Service
from src.ui_theme import (
    CARD_PADDING,
    CARD_RADIUS,
    FONT_BODY,
    FONT_H1,
    FONT_H2,
    FONT_META,
    THEME,
    TREEVIEW_ROW_HEIGHT,
)


class SeccionExplorador(ctk.CTkFrame):
    """Navega las noticias extraidas y sus resultados de analisis."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.noticias: list[dict] = list(root_app.noticias)
        self._corpus_por_url = {
            item.get("url"): item
            for item in getattr(root_app, "corpus_procesado", [])
            if item.get("url")
        }
        self._service = Fase1Service()
        self._config_treeview_style()
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        if not self.noticias:
            self._build_empty_state()
        else:
            self._build_content()

    def _card(self, master) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _build_empty_state(self) -> None:
        center = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        center.grid(row=0, column=0)
        ctk.CTkLabel(center, text="Sin noticias", font=FONT_H1, text_color=THEME["text_2"]).grid(
            row=0, column=0, pady=(0, 8)
        )
        ctk.CTkLabel(
            center,
            text="Carga y analiza noticias primero.",
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
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=3)
        right.grid_rowconfigure(1, weight=2)

        self._build_export_card(left).grid(row=0, column=0, sticky="ew")
        self._build_tabla_card(right).grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self._build_detalle_card(right).grid(row=1, column=0, sticky="nsew")
        self._poblar_tabla()
        self._actualizar_export_state()

    def _build_export_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Exportar corpus crudo", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))
        ctk.CTkLabel(
            card,
            text=f"{len(self.noticias)} noticias cargadas",
            font=FONT_META,
            text_color=THEME["text_2"],
        ).grid(row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10))
        self.btn_json = ctk.CTkButton(
            card,
            text="Exportar JSON",
            command=lambda: self._exportar("json"),
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        )
        self.btn_json.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        self.btn_csv = ctk.CTkButton(
            card,
            text="Exportar CSV",
            command=lambda: self._exportar("csv"),
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        )
        self.btn_csv.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        self.btn_todo = ctk.CTkButton(
            card,
            text="Exportar ambos",
            command=lambda: self._exportar("todo"),
            fg_color=THEME["success"],
            hover_color=THEME["success"],
            text_color=THEME["bg_base"],
        )
        self.btn_todo.grid(row=4, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_tabla_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            card, text="Noticias extraidas", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        table_frame = ctk.CTkFrame(card, fg_color=THEME["bg_surface"], corner_radius=0)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = ("titulo", "fuente", "categoria_original", "categoria_predicha", "sentimiento", "fecha", "autor")
        self.tabla = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        for col, texto, ancho in [
            ("titulo", "Titulo", 320),
            ("fuente", "Fuente", 160),
            ("categoria_original", "Categoria original", 130),
            ("categoria_predicha", "Categoria predicha", 130),
            ("sentimiento", "Sentimiento", 100),
            ("fecha", "Fecha", 100),
            ("autor", "Autor", 150),
        ]:
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="w")

        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<<TreeviewSelect>>", self._mostrar_detalle)
        ttk.Scrollbar(table_frame, orient="vertical", command=self.tabla.yview).grid(row=0, column=1, sticky="ns")
        self.tabla.configure(yscrollcommand=lambda *a: None)
        return card

    def _build_detalle_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(3, weight=1)
        self._det_titulo = ctk.CTkLabel(
            card, text="Selecciona una noticia", font=FONT_H2, text_color=THEME["text_1"], anchor="w"
        )
        self._det_titulo.grid(row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        self._det_meta = ctk.CTkLabel(card, text="", font=FONT_META, text_color=THEME["text_2"], anchor="w")
        self._det_meta.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 4))
        self._det_url = ctk.CTkLabel(card, text="", font=FONT_META, text_color=THEME["accent"], anchor="w")
        self._det_url.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        self._det_cuerpo = ctk.CTkTextbox(
            card,
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_1"],
            font=FONT_BODY,
            wrap="word",
        )
        self._det_cuerpo.grid(row=3, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self._det_cuerpo.configure(state="disabled")
        return card

    def _poblar_tabla(self) -> None:
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for idx, noticia in enumerate(self.noticias):
            corpus_item = self._corpus_por_url.get(noticia.get("url"), {})
            self.tabla.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    noticia.get("titulo", ""),
                    noticia.get("fuente_nombre") or noticia.get("fuente", "Demo local"),
                    noticia.get("categoria_original") or noticia.get("categoria", "sin_categoria"),
                    noticia.get("categoria_predicha") or corpus_item.get("categoria_predicha") or noticia.get("categoria", "sin_categoria"),
                    _sentimiento_label(noticia, corpus_item),
                    noticia.get("fecha", ""),
                    noticia.get("autor", ""),
                ),
            )

    def _mostrar_detalle(self, _event=None) -> None:
        sel = self.tabla.selection()
        if not sel:
            return
        indice = int(sel[0])
        noticia = self.noticias[indice]
        corpus_item = self._corpus_por_url.get(noticia.get("url"), {})
        fuente = noticia.get("fuente_nombre") or noticia.get("fuente", "Demo local")
        categoria_original = noticia.get("categoria_original") or noticia.get("categoria", "sin_categoria")
        categoria_predicha = noticia.get("categoria_predicha") or corpus_item.get("categoria_predicha") or categoria_original
        sentimiento = noticia.get("sentimiento") or corpus_item.get("sentimiento") or {}
        etiqueta = sentimiento.get("etiqueta", "sin_sentimiento") if isinstance(sentimiento, dict) else "sin_sentimiento"
        score = sentimiento.get("compound", sentimiento.get("score", "")) if isinstance(sentimiento, dict) else ""
        kg_estado = "presente en KG" if _esta_en_kg(self.root_app, noticia) else "sin enlace KG verificado"

        self._det_titulo.configure(text=noticia.get("titulo", ""))
        self._det_meta.configure(
            text=(
                f"{fuente} | original: {categoria_original} | predicha: {categoria_predicha} | "
                f"{etiqueta} {_fmt_score(score)} | {noticia.get('fecha', '')} | {noticia.get('autor', '')} | {kg_estado}"
            )
        )
        self._det_url.configure(text=noticia.get("url", ""))
        terminos = ", ".join(corpus_item.get("terminos_relevantes", [])[:8]) or "sin terminos TF-IDF registrados"
        similares = _similares_texto(corpus_item.get("recomendaciones") or corpus_item.get("noticias_similares") or [])
        rdf_uri = _rdf_uri(self.root_app, indice + 1)
        texto = (
            f"{noticia.get('cuerpo', '')}\n\n"
            "--- Analisis integrado ---\n"
            f"Terminos relevantes: {terminos}\n"
            f"Noticias similares:\n{similares}\n\n"
            f"URI RDF sugerida: {rdf_uri}"
        )
        self._det_cuerpo.configure(state="normal")
        self._det_cuerpo.delete("1.0", "end")
        self._det_cuerpo.insert("1.0", texto)
        self._det_cuerpo.configure(state="disabled")

    def _exportar(self, formato: str) -> None:
        try:
            if formato == "json":
                ruta = self._service.exportar_json(self.noticias)
                msg = f"JSON exportado: {ruta}"
            elif formato == "csv":
                ruta = self._service.exportar_csv(self.noticias)
                msg = f"CSV exportado: {ruta}"
            else:
                rj, rc = self._service.exportar_todo(self.noticias)
                msg = f"Exportados: {rj} y {rc}"
            self.root_app.set_estado(msg, "ok", total_noticias=len(self.noticias))
        except Exception as exc:
            messagebox.showerror("Exportacion", str(exc))
            self.root_app.set_estado(str(exc), "error")

    def _actualizar_export_state(self) -> None:
        state = "normal" if self.noticias else "disabled"
        for btn in (self.btn_json, self.btn_csv, self.btn_todo):
            btn.configure(state=state)

    @staticmethod
    def _config_treeview_style() -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=THEME["bg_input"],
            fieldbackground=THEME["bg_input"],
            foreground=THEME["text_1"],
            rowheight=TREEVIEW_ROW_HEIGHT,
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
        style.map("Treeview", background=[("selected", THEME["accent"])], foreground=[("selected", THEME["text_1"])])
        style.map("Treeview.Heading", background=[("active", THEME["border"])])


def _sentimiento_label(noticia: dict, corpus_item: dict | None = None) -> str:
    sentimiento = noticia.get("sentimiento") or (corpus_item or {}).get("sentimiento")
    if isinstance(sentimiento, dict):
        return str(sentimiento.get("etiqueta") or "neutral")
    return "sin_sentimiento"


def _fmt_score(score: object) -> str:
    try:
        return f"({float(score):+.3f})"
    except (TypeError, ValueError):
        return ""


def _similares_texto(similares: list[dict]) -> str:
    if not similares:
        return "- Sin similares registrados."
    return "\n".join(
        f"- [{float(item.get('similitud', 0.0)):.4f}] {item.get('titulo', '')}"
        for item in similares[:5]
    )


def _rdf_uri(root_app, indice: int) -> str:
    if not getattr(root_app, "grafo_info", None):
        return "Knowledge Graph no construido"
    return f"http://simanw.org/data/noticia_{indice}"


def _esta_en_kg(root_app, noticia: dict) -> bool:
    grafo_info = getattr(root_app, "grafo_info", {}) or {}
    total_triples = int(grafo_info.get("total_triples", 0) or 0)
    return total_triples > 0 and bool(noticia.get("url"))
