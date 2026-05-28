from __future__ import annotations

import customtkinter as ctk

from src.fase6_service import QUERY_ENLACES_WIKIDATA
from src.knowledge_graph import QUERY_CONTEO_CATEGORIA, QUERY_NOTICIAS_METADATA
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, THEME


class SeccionGrafo(ctk.CTkFrame):
    """Consulta y exportacion del Knowledge Graph."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.query_var = ctk.StringVar(value="Conteo por categoria")
        self.queries = {
            "Conteo por categoria": QUERY_CONTEO_CATEGORIA,
            "Noticias con metadata": QUERY_NOTICIAS_METADATA,
            "Enlaces Wikidata": QUERY_ENLACES_WIKIDATA,
        }
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=280, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        if not self.root_app.grafo_info:
            self._empty()
            return

        left = self._card(self)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        right = self._card(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_rowconfigure(4, weight=1)

        info = self.root_app.grafo_info
        items = [
            ("Triples RDF", str(info.get("total_triples", 0))),
            ("Wikidata links", str(info.get("entidades", {}).get("enlaces_wikidata", 0))),
            ("Formatos", ", ".join(info.get("formatos_exportados", [])) or "N/D"),
            ("Errores", str(len(info.get("errores", [])))),
        ]
        ctk.CTkLabel(left, text="Graph Summary", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        for row, (label, value) in enumerate(items, start=1):
            ctk.CTkLabel(left, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=row * 2 - 1, column=0, sticky="w", padx=CARD_PADDING
            )
            ctk.CTkLabel(left, text=value, font=FONT_BODY, text_color=THEME["text_1"]).grid(
                row=row * 2, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 8)
            )
        ctk.CTkButton(left, text="Export TTL", command=self._export_ttl, fg_color=THEME["bg_input"],
                      border_width=1, border_color=THEME["border"]).grid(row=8, column=0, sticky="ew", padx=CARD_PADDING, pady=(8, 4))
        ctk.CTkButton(left, text="Export JSON-LD", command=self._export_jsonld, fg_color=THEME["bg_input"],
                      border_width=1, border_color=THEME["border"]).grid(row=9, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        ctk.CTkLabel(right, text="SPARQL", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        ctk.CTkOptionMenu(right, values=list(self.queries), variable=self.query_var, fg_color=THEME["bg_input"]).grid(
            row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8)
        )
        ctk.CTkButton(right, text="Run Query", command=self._run_query, fg_color=THEME["accent"]).grid(
            row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8)
        )
        self.results = ctk.CTkTextbox(right, fg_color=THEME["bg_input"], text_color=THEME["text_1"], font=FONT_BODY)
        self.results.grid(row=4, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self._run_query()

    def _card(self, master) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _empty(self) -> None:
        center = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        center.grid(row=0, column=0, columnspan=2)
        ctk.CTkLabel(center, text="No graph loaded", font=FONT_H1, text_color=THEME["text_2"]).grid(row=0, column=0)

    def _run_query(self) -> None:
        service = getattr(self.root_app, "simanw_service", None)
        query = self.queries[self.query_var.get()]
        resultados = service.fase6_service.ejecutar_sparql(query) if service else []
        texto = "\n".join(str(item) for item in resultados) or "No results or query warning."
        self._set_text(texto)

    def _export_ttl(self) -> None:
        service = getattr(self.root_app, "simanw_service", None)
        if service:
            ruta = service.fase6_service.exportar_ttl()
            self.root_app.set_estado(f"TTL exported: {ruta}", "ok")

    def _export_jsonld(self) -> None:
        service = getattr(self.root_app, "simanw_service", None)
        if service:
            ruta = service.fase6_service.exportar_jsonld()
            self.root_app.set_estado(f"JSON-LD exported: {ruta}", "ok")

    def _set_text(self, text: str) -> None:
        self.results.configure(state="normal")
        self.results.delete("1.0", "end")
        self.results.insert("1.0", text)
        self.results.configure(state="disabled")
