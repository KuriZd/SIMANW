from __future__ import annotations

import threading
from tkinter import messagebox, ttk

import customtkinter as ctk

from src.fase1_service import Fase1Service, ResultadoFase1
from src.fuentes_service import FuentesService
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, THEME, TREEVIEW_ROW_HEIGHT


class Fase1Frame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.service = Fase1Service()
        self.fuentes_service = FuentesService()
        self.noticias: list[dict] = []

        self.modo_var = ctk.StringVar(value="Demo local")
        self.fuente_predef_var = ctk.StringVar(value="")
        self.tipo_custom_var = ctk.StringVar(value="RSS")
        self.url_var = ctk.StringVar()
        self.total_var = ctk.StringVar(value="0")
        self.fuente_actual_var = ctk.StringVar(value="Demo")
        self.ultima_accion_var = ctk.StringVar(value="Sin acciones")

        self._config_treeview_style()
        self._build()
        self._actualizar_botones_exportacion()

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=300, weight=0)
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

        self._build_fuente_card(left).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_export_card(left).grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self._build_estado_card(left).grid(row=2, column=0, sticky="ew")

        self._build_tabla_card(right).grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self._build_detalle_card(right).grid(row=1, column=0, sticky="nsew")

    def _card(self, master) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _build_fuente_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Fuente de noticias", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )

        self.selector_modo = ctk.CTkOptionMenu(
            card,
            values=["Demo local", "Predefined source", "Custom RSS/URL"],
            variable=self.modo_var,
            command=lambda _value: self._actualizar_modo_entrada(),
            fg_color=THEME["bg_input"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"],
            dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"],
        )
        self.selector_modo.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        nombres_fuentes = self.fuentes_service.listar_nombres_fuentes()
        self.fuente_predef_var.set(nombres_fuentes[0] if nombres_fuentes else "")
        self.selector_predef = ctk.CTkOptionMenu(
            card,
            values=nombres_fuentes or ["Sin fuentes activas"],
            variable=self.fuente_predef_var,
            fg_color=THEME["bg_input"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"],
            dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"],
        )
        self.selector_predef.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.selector_tipo_custom = ctk.CTkOptionMenu(
            card,
            values=["RSS", "Paginado"],
            variable=self.tipo_custom_var,
            fg_color=THEME["bg_input"],
            button_color=THEME["accent"],
            button_hover_color=THEME["accent"],
            text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"],
            dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"],
        )
        self.selector_tipo_custom.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.url_entry = ctk.CTkEntry(
            card,
            textvariable=self.url_var,
            placeholder_text="URL RSS o página inicial",
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            text_color=THEME["text_1"],
            placeholder_text_color=THEME["text_2"],
        )
        self.url_entry.grid(row=4, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 10))

        self.btn_ejecutar = ctk.CTkButton(
            card,
            text="Analyze News",
            command=self.ejecutar_fase1,
            fg_color=THEME["accent"],
            hover_color=THEME["accent"],
            text_color=THEME["text_1"],
        )
        self.btn_ejecutar.grid(row=5, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self._actualizar_modo_entrada()
        return card

    def _build_export_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Exportación", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )

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

    def _build_estado_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Estado", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        for row, (label, var) in enumerate(
            [
                ("Total de noticias", self.total_var),
                ("Fuente actual", self.fuente_actual_var),
                ("Última acción", self.ultima_accion_var),
            ],
            start=1,
        ):
            ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=row * 2 - 1, column=0, sticky="w", padx=CARD_PADDING
            )
            ctk.CTkLabel(card, textvariable=var, font=FONT_BODY, text_color=THEME["text_1"]).grid(
                row=row * 2, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 8)
            )
        return card

    def _build_tabla_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(card, text="Noticias extraídas", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )

        table_frame = ctk.CTkFrame(card, fg_color=THEME["bg_surface"], corner_radius=0)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columnas = ("titulo", "categoria", "fuente", "fecha", "autor")
        self.tabla = ttk.Treeview(table_frame, columns=columnas, show="headings", selectmode="browse")
        for columna, texto, ancho in [
            ("titulo", "Título", 430),
            ("categoria", "Categoría", 120),
            ("fuente", "Fuente", 180),
            ("fecha", "Fecha", 100),
            ("autor", "Autor", 160),
        ]:
            self.tabla.heading(columna, text=texto)
            self.tabla.column(columna, width=ancho, anchor="w")
        self.tabla.grid(row=0, column=0, sticky="nsew")
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabla.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.tabla.configure(yscrollcommand=scroll_y.set)
        return card

    def _build_detalle_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(6, weight=1)

        self.detalle_titulo = ctk.CTkLabel(
            card,
            text="Selecciona una noticia",
            font=FONT_H2,
            text_color=THEME["text_1"],
            anchor="w",
        )
        self.detalle_titulo.grid(row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 4))

        self.detalle_meta = ctk.CTkLabel(card, text="", font=FONT_META, text_color=THEME["text_2"], anchor="w")
        self.detalle_meta.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 4))

        self.detalle_url = ctk.CTkLabel(card, text="", font=FONT_META, text_color=THEME["accent"], anchor="w")
        self.detalle_url.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))

        self.detalle_cuerpo = ctk.CTkTextbox(
            card,
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            border_width=1,
            text_color=THEME["text_1"],
            font=FONT_BODY,
            wrap="word",
        )
        self.detalle_cuerpo.grid(row=6, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self.detalle_cuerpo.configure(state="disabled")
        return card

    def ejecutar_fase1(self) -> None:
        self._set_running(True)
        self.root_app.set_estado("Ejecutando Fase 1...", "loading", total_noticias=len(self.noticias))
        self.root_app.show_progress()
        self._limpiar_resultados()
        modo = self.modo_var.get()
        fuente_nombre = self.fuente_predef_var.get()
        tipo_custom = self.tipo_custom_var.get()
        url = self.url_var.get()

        threading.Thread(target=self._ejecutar_bg, args=(modo, fuente_nombre, tipo_custom, url), daemon=True).start()

    def _ejecutar_bg(self, modo: str, fuente_nombre: str, tipo_custom: str, url: str) -> None:
        try:
            if modo == "Demo local":
                resultado = self.service.ejecutar_demo()
            elif modo == "Predefined source":
                fuente = self.fuentes_service.obtener_por_nombre(fuente_nombre)
                noticias = self.service.ejecutar_fuente_predefinida(fuente["id"])
                resultado = ResultadoFase1(noticias=noticias, fuente="predefinida", errores=self.service.errores)
            elif tipo_custom == "RSS":
                resultado = self.service.ejecutar_rss(url)
            else:
                resultado = self.service.ejecutar_paginado(url)
            self.after(0, lambda: self._on_resultado(resultado))
        except Exception as exc:
            self.after(0, lambda: self._on_error(str(exc)))

    def _on_resultado(self, resultado: ResultadoFase1) -> None:
        self.noticias = resultado.noticias
        self.root_app.set_noticias(resultado.noticias)
        for idx, noticia in enumerate(self.noticias):
            self.tabla.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    noticia["titulo"],
                    noticia["categoria"],
                    noticia.get("fuente_nombre", ""),
                    noticia["fecha"],
                    noticia["autor"],
                ),
            )

        self.total_var.set(str(len(self.noticias)))
        self.fuente_actual_var.set(self._etiqueta_fuente_actual(resultado))
        self.ultima_accion_var.set("Extracción completada")
        nivel = "warning" if resultado.errores else "ok"
        mensaje = f"{len(self.noticias)} noticia(s) extraida(s)"
        if resultado.errores:
            mensaje = f"{mensaje}; {len(resultado.errores)} advertencia(s)"
        self.root_app.set_estado(mensaje, nivel, total_noticias=len(self.noticias))
        self.root_app.hide_progress()
        self._set_running(False)
        self._actualizar_botones_exportacion()

    def _on_error(self, mensaje: str) -> None:
        self.ultima_accion_var.set("Error de extracción")
        self.root_app.hide_progress()
        self.root_app.set_estado(mensaje, "error", total_noticias=len(self.noticias))
        self._set_running(False)
        self._actualizar_botones_exportacion()
        messagebox.showerror("Fase 1", mensaje)

    def mostrar_detalle(self, _event=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        noticia = self.noticias[int(seleccion[0])]
        self.detalle_titulo.configure(text=noticia["titulo"])
        fuente = noticia.get("fuente_nombre")
        fuente_txt = f" · {fuente}" if fuente else ""
        self.detalle_meta.configure(
            text=f"{noticia['categoria']} · {noticia['fecha']} · {noticia['autor']}{fuente_txt}"
        )
        self.detalle_url.configure(text=noticia["url"])
        self.detalle_cuerpo.configure(state="normal")
        self.detalle_cuerpo.delete("1.0", "end")
        self.detalle_cuerpo.insert("1.0", noticia["cuerpo"])
        self.detalle_cuerpo.configure(state="disabled")

    def exportar_json(self) -> None:
        self._exportar("json")

    def exportar_csv(self) -> None:
        self._exportar("csv")

    def exportar_todo(self) -> None:
        self._exportar("todo")

    def _exportar(self, formato: str) -> None:
        if not self.noticias:
            self.root_app.set_estado("No hay noticias para exportar.", "warning", total_noticias=0)
            return
        try:
            if formato == "json":
                ruta = self.service.exportar_json(self.noticias)
                mensaje = f"JSON exportado: {ruta}"
            elif formato == "csv":
                ruta = self.service.exportar_csv(self.noticias)
                mensaje = f"CSV exportado: {ruta}"
            else:
                ruta_json, ruta_csv = self.service.exportar_todo(self.noticias)
                mensaje = f"Exportados: {ruta_json} y {ruta_csv}"
            self.ultima_accion_var.set("Exportación completada")
            self.root_app.set_estado(mensaje, "ok", total_noticias=len(self.noticias))
        except Exception as exc:
            self.ultima_accion_var.set("Error de exportación")
            self.root_app.set_estado(str(exc), "error", total_noticias=len(self.noticias))
            messagebox.showerror("Exportación", str(exc))

    def _limpiar_resultados(self) -> None:
        self.noticias = []
        self.root_app.set_noticias([])
        self.root_app.set_corpus([], {})
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        self.total_var.set("0")
        self.ultima_accion_var.set("Ejecutando extracción")
        self.detalle_titulo.configure(text="Selecciona una noticia")
        self.detalle_meta.configure(text="")
        self.detalle_url.configure(text="")
        self.detalle_cuerpo.configure(state="normal")
        self.detalle_cuerpo.delete("1.0", "end")
        self.detalle_cuerpo.configure(state="disabled")
        self._actualizar_botones_exportacion()

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.btn_ejecutar.configure(state=state)
        self.selector_modo.configure(state=state)
        if running:
            self.selector_predef.configure(state=state)
            self.selector_tipo_custom.configure(state=state)
            self.url_entry.configure(state=state)
        else:
            self._actualizar_modo_entrada()

    def _actualizar_botones_exportacion(self) -> None:
        state = "normal" if self.noticias else "disabled"
        self.btn_json.configure(state=state)
        self.btn_csv.configure(state=state)
        self.btn_todo.configure(state=state)

    def _actualizar_modo_entrada(self) -> None:
        modo = self.modo_var.get()
        if modo == "Demo local":
            self.selector_predef.configure(state="disabled")
            self.selector_tipo_custom.configure(state="disabled")
            self.url_entry.configure(state="disabled")
        elif modo == "Predefined source":
            self.selector_predef.configure(state="normal")
            self.selector_tipo_custom.configure(state="disabled")
            self.url_entry.configure(state="disabled")
        else:
            self.selector_predef.configure(state="disabled")
            self.selector_tipo_custom.configure(state="normal")
            self.url_entry.configure(state="normal")

    def _etiqueta_fuente_actual(self, resultado: ResultadoFase1) -> str:
        if resultado.fuente == "predefinida" and self.noticias:
            return self.noticias[0].get("fuente_nombre", "Predefined source")
        return {
            "demo": "Demo local",
            "rss": "Custom RSS",
            "paginado": "Custom paginado",
            "predefinida": "Predefined source",
        }.get(resultado.fuente, str(resultado.fuente))

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
        style.map(
            "Treeview",
            background=[("selected", THEME["accent"])],
            foreground=[("selected", THEME["text_1"])],
        )
        style.map("Treeview.Heading", background=[("active", THEME["border"])])
