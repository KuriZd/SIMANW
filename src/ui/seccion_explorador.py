"""Sección 'Explorador de noticias' — tabla + detalle del corpus crudo."""
from __future__ import annotations

from tkinter import messagebox, ttk

import customtkinter as ctk

from src.fase1_service import Fase1Service
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, THEME


class SeccionExplorador(ctk.CTkFrame):
    """Navega las noticias crudas extraídas y permite re-exportarlas."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.noticias: list[dict] = list(root_app.noticias)
        self._service = Fase1Service()
        self._config_treeview_style()
        self._build()

    # ═══════════════════════════════════════════════════════════════════════════
    # Layout
    # ═══════════════════════════════════════════════════════════════════════════

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if not self.noticias:
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
            center, text="Sin noticias", font=FONT_H1, text_color=THEME["text_2"]
        ).grid(row=0, column=0, pady=(0, 8))
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
            card, text="Exportar JSON", command=lambda: self._exportar("json"),
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"], text_color=THEME["text_1"],
        )
        self.btn_json.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.btn_csv = ctk.CTkButton(
            card, text="Exportar CSV", command=lambda: self._exportar("csv"),
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"], text_color=THEME["text_1"],
        )
        self.btn_csv.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.btn_todo = ctk.CTkButton(
            card, text="Exportar ambos", command=lambda: self._exportar("todo"),
            fg_color=THEME["success"], hover_color=THEME["success"], text_color=THEME["bg_base"],
        )
        self.btn_todo.grid(row=4, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_tabla_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Noticias extraídas", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        table_frame = ctk.CTkFrame(card, fg_color=THEME["bg_surface"], corner_radius=0)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = ("titulo", "fuente", "categoria", "fecha", "autor")
        self.tabla = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        for col, texto, ancho in [
            ("titulo", "Título", 360), ("fuente", "Fuente", 180), ("categoria", "Categoría", 120),
            ("fecha", "Fecha", 100), ("autor", "Autor", 160),
        ]:
            self.tabla.heading(col, text=texto)
            self.tabla.column(col, width=ancho, anchor="w")

        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<<TreeviewSelect>>", self._mostrar_detalle)

        ttk.Scrollbar(table_frame, orient="vertical", command=self.tabla.yview).grid(
            row=0, column=1, sticky="ns"
        )
        self.tabla.configure(yscrollcommand=lambda *a: None)
        return card

    def _build_detalle_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(3, weight=1)

        self._det_titulo = ctk.CTkLabel(
            card, text="Selecciona una noticia", font=FONT_H2,
            text_color=THEME["text_1"], anchor="w",
        )
        self._det_titulo.grid(row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 4))

        self._det_meta = ctk.CTkLabel(card, text="", font=FONT_META, text_color=THEME["text_2"], anchor="w")
        self._det_meta.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 4))

        self._det_url = ctk.CTkLabel(card, text="", font=FONT_META, text_color=THEME["accent"], anchor="w")
        self._det_url.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

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
        for n in self.tabla.get_children():
            self.tabla.delete(n)
        for idx, noticia in enumerate(self.noticias):
            self.tabla.insert(
                "", "end", iid=str(idx),
                values=(
                    noticia["titulo"],
                    noticia.get("fuente_nombre", "Demo local"),
                    noticia["categoria"],
                    noticia["fecha"],
                    noticia["autor"],
                ),
            )

    def _mostrar_detalle(self, _event=None) -> None:
        sel = self.tabla.selection()
        if not sel:
            return
        n = self.noticias[int(sel[0])]
        self._det_titulo.configure(text=n["titulo"])
        fuente = n.get("fuente_nombre", "Demo local")
        self._det_meta.configure(text=f"{fuente} · {n['categoria']} · {n['fecha']} · {n['autor']}")
        self._det_url.configure(text=n["url"])
        self._det_cuerpo.configure(state="normal")
        self._det_cuerpo.delete("1.0", "end")
        self._det_cuerpo.insert("1.0", n["cuerpo"])
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
            messagebox.showerror("Exportación", str(exc))
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
