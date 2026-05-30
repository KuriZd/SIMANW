"""Sección 'Resultados NLP' — corpus procesado con estadísticas y detalle."""
from __future__ import annotations

from pathlib import Path
from tkinter import messagebox, ttk

import customtkinter as ctk

from src.analisis_discurso import AnalisisDiscurso
from src.fase2_service import Fase2Service
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, THEME, TREEVIEW_ROW_HEIGHT


class SeccionResultados(ctk.CTkFrame):
    """Muestra el corpus NLP: tabla, panel de detalle y estadísticas."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.corpus: list[dict] = list(root_app.corpus_procesado)
        self._service = Fase2Service()
        self._analisis_discurso = self._cargar_analisis_discurso()
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

        left = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)

        self._build_stats_card(left, stats).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_auto_analysis_card(left).grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self._build_trends_card(left).grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self._build_thread_card(left).grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self._build_discourse_card(left).grid(row=4, column=0, sticky="ew", pady=(0, 10))
        self._build_similarity_card(left).grid(row=5, column=0, sticky="ew", pady=(0, 10))
        self._build_export_card(left).grid(row=6, column=0, sticky="ew")

        self._build_tabla_card(right).grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._build_detalle_card(right).grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self._build_ac2_visual_card(right).grid(row=2, column=0, sticky="ew")

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

    def _build_auto_analysis_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Automatic analysis", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        analisis = getattr(self.root_app, "analisis", {}) or {}
        clasificacion = analisis.get("clasificacion", {})
        evaluacion = analisis.get("evaluacion_busqueda", {})
        ac3 = clasificacion.get("ac3", {})
        items = [
            ("Categorias", _top_dict(analisis.get("categorias", {}))),
            ("Sentimiento", _top_dict(analisis.get("sentimientos", {}))),
            ("Modelo AC-3", ac3.get("mejor_modelo") or ac3.get("estado", "pendiente")),
            ("Accuracy", _fmt_float(ac3.get("accuracy"))),
            ("Search winner", evaluacion.get("ganador_f1") or "-"),
            ("MAP vectorial", _fmt_float(evaluacion.get("map_vectorial"))),
        ]
        for row, (lbl, val) in enumerate(items, start=1):
            ctk.CTkLabel(card, text=lbl, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=row * 2 - 1, column=0, sticky="w", padx=CARD_PADDING
            )
            ctk.CTkLabel(card, text=str(val or "-"), font=FONT_BODY, text_color=THEME["text_1"], wraplength=230).grid(
                row=row * 2, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 6)
            )
        return card

    def _build_trends_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card, text="Timeline & trends (AC-9)", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        analisis = getattr(self.root_app, "analisis", {}) or {}
        tendencias = analisis.get("tendencias", {})
        evidencia = {}
        result = getattr(self.root_app, "resultado_actual", None)
        if result:
            evidencia = result.evidencias_ac.get("AC-9", {})
        if not tendencias:
            texto = "AC-9 pendiente: no hay fechas/categorias suficientes para tendencias."
        else:
            pico = tendencias.get("pico", {}) or {}
            archivos = []
            if evidencia.get("archivo_csv"):
                archivos.append(evidencia["archivo_csv"])
            if evidencia.get("archivo_png"):
                archivos.append(evidencia["archivo_png"])
            texto = (
                f"Estado: {evidencia.get('estado', 'parcial')}\n"
                f"Granularidad: {tendencias.get('granularidad', 'mes')}\n"
                f"Temas: {', '.join(evidencia.get('temas_analizados', [])[:5]) or '-'}\n"
                f"Pico: {pico.get('categoria', '-')} / {pico.get('periodo', '-')} ({pico.get('count', 0)} noticias)\n"
                f"Archivos: {', '.join(archivos) or '-'}"
            )
        box = ctk.CTkFrame(card, fg_color=THEME["bg_input"], corner_radius=CARD_RADIUS)
        box.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            box,
            text=texto,
            font=FONT_BODY,
            text_color=THEME["text_1"],
            justify="left",
            anchor="w",
            wraplength=250,
        ).grid(
            row=0, column=0, sticky="ew", padx=10, pady=10
        )
        return card

    def _build_thread_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card, text="Thread discussion analysis (AC-4)", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="ew", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        evidencia = {}
        result = getattr(self.root_app, "resultado_actual", None)
        if result:
            evidencia = result.evidencias_ac.get("AC-4", {})

        if not evidencia:
            texto = "AC-4 pendiente: ejecuta el pipeline para analizar un hilo o corpus derivado."
        else:
            texto = (
                f"Estado: {evidencia.get('estado', 'pendiente')}\n"
                f"Origen: {evidencia.get('origen_datos', '-')}\n"
                f"Mensajes: {evidencia.get('total_mensajes', 0)} | Participantes: {evidencia.get('participantes', 0)}\n"
                f"Tono: {evidencia.get('tono', '-')} ({_fmt_signed(evidencia.get('sentimiento_promedio'))})\n"
                f"Subtemas: {evidencia.get('subtemas_detectados', 0)} | Evolucion: {evidencia.get('evolucion_puntos', 0)} puntos\n"
                f"Archivo: {evidencia.get('archivo_json', '-')}"
            )
            if evidencia.get("resumen_textual"):
                texto += f"\nResumen: {evidencia['resumen_textual']}"
            if evidencia.get("observacion"):
                texto += f"\nNota: {evidencia['observacion']}"

        box = ctk.CTkFrame(card, fg_color=THEME["bg_input"], corner_radius=CARD_RADIUS)
        box.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            box,
            text=texto,
            font=FONT_BODY,
            text_color=THEME["text_1"],
            justify="left",
            anchor="w",
            wraplength=250,
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        return card

    def _build_discourse_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Discourse statistics", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        textos = self._analisis_discurso.get("textos_analizados", [])
        if not textos:
            ctk.CTkLabel(
                card, text="No hay textos suficientes para AC-2.", font=FONT_META, text_color=THEME["text_2"]
            ).grid(row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
            return card

        primer = textos[0]
        items = [
            ("Textos analizados", str(len(textos))),
            ("Riqueza promedio", _fmt_float(self._riqueza_promedio(textos))),
            ("Top unigramas", _top_lista(primer.get("top_unigramas", []))),
            ("Top bigramas", _top_ngramas(primer.get("top_bigramas", []))),
            ("Top trigramas", _top_ngramas(primer.get("top_trigramas", []))),
        ]
        for row, (lbl, val) in enumerate(items, start=1):
            ctk.CTkLabel(card, text=lbl, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=row * 2 - 1, column=0, sticky="w", padx=CARD_PADDING
            )
            ctk.CTkLabel(card, text=val or "-", font=FONT_BODY, text_color=THEME["text_1"], wraplength=230).grid(
                row=row * 2, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 6)
            )
        return card

    def _build_similarity_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Similarity groups", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))
        grupos = self.root_app.estadisticas_fase2.get("grupos_similares", [])
        texto = "Sin grupos similares detectados."
        if grupos:
            texto = "\n".join(
                f"Group {idx + 1}: " + ", ".join(f"N{i + 1}" for i in grupo)
                for idx, grupo in enumerate(grupos[:5])
            )
        ctk.CTkLabel(card, text=texto, font=FONT_BODY, text_color=THEME["text_1"], justify="left").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING)
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
        card.configure(height=300)
        card.grid_propagate(False)
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
        card.configure(height=360)
        card.grid_propagate(False)
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

    def _build_ac2_visual_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.configure(height=310)
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            card,
            text="AC-2: nube de palabras y estadisticas de discurso",
            font=FONT_H2,
            text_color=THEME["text_1"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        textos = self._analisis_discurso.get("textos_analizados", [])
        comparativa = self._analisis_discurso.get("comparativa", [])
        primer = textos[0] if textos else {}
        evidencia = {}
        result = getattr(self.root_app, "resultado_actual", None)
        if result:
            evidencia = result.evidencias_ac.get("AC-2", {})

        nube_path = evidencia.get("archivo_nube") or getattr(self.root_app, "rutas_exportacion", {}).get("nube_ac2_png")
        imagen_mostrada = self._insertar_nube_ac2(card, nube_path)
        if not imagen_mostrada:
            ctk.CTkLabel(
                card,
                text="Nube pendiente: ejecuta Load / Analyze News o revisa que wordcloud este instalado.",
                font=FONT_META,
                text_color=THEME["text_2"],
                justify="left",
                wraplength=360,
            ).grid(row=1, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        resumen = (
            f"Textos: {len(textos)}\n"
            f"Bigramas: {_top_ngramas(primer.get('top_bigramas', [])) or '-'}\n"
            f"Trigramas: {_top_ngramas(primer.get('top_trigramas', [])) or '-'}\n"
            f"Riqueza por seccion: {_secciones_texto(primer.get('riqueza_por_seccion', []))}\n"
            f"Entidades: {_entidades_texto(primer.get('posibles_entidades', []))}\n"
            f"Comparativa: {_comparativa_texto(comparativa)}"
        )
        ctk.CTkLabel(
            card,
            text=resumen,
            font=FONT_BODY,
            text_color=THEME["text_1"],
            justify="left",
            anchor="nw",
            wraplength=430,
        ).grid(row=1, column=1, sticky="nsew", padx=(0, CARD_PADDING), pady=(0, CARD_PADDING))
        return card

    def _insertar_nube_ac2(self, card, ruta: str | Path | None) -> bool:
        if not ruta:
            return False
        path = Path(ruta)
        if not path.exists():
            return False
        try:
            from PIL import Image
        except ImportError:
            return False
        try:
            image = Image.open(path)
            self._ac2_wordcloud_image = ctk.CTkImage(light_image=image, dark_image=image, size=(360, 180))
            ctk.CTkLabel(card, text="", image=self._ac2_wordcloud_image).grid(
                row=1, column=0, sticky="nsew", padx=CARD_PADDING, pady=(0, CARD_PADDING)
            )
            return True
        except Exception:
            return False

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
        sentimiento = item.get("sentimiento", {}).get("etiqueta", "sin_sentimiento")
        categoria_pred = item.get("categoria_predicha", item.get("categoria", "sin_categoria"))
        self._det_meta.configure(
            text=f"{item['categoria']} -> {categoria_pred}  |  {sentimiento}  |  {item['fecha']}  |  {item['autor']}"
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
            f"Riqueza léxica: {item['riqueza_lexica']:.4f}\n\n"
            f"═══ NOTICIAS SIMILARES ═══\n{_similares_texto(item.get('recomendaciones') or item.get('noticias_similares', []))}"
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
            foreground=THEME["text_1"], rowheight=TREEVIEW_ROW_HEIGHT,
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

    def _cargar_analisis_discurso(self) -> dict:
        import json
        from pathlib import Path
        ruta = getattr(self.root_app, "rutas_exportacion", {}).get("analisis_ac2_json") or "data/analisis_ac2.json"
        try:
            path = Path(ruta)
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    @staticmethod
    def _riqueza_promedio(textos: list[dict]) -> float:
        if not textos:
            return 0.0
        return sum(float(t.get("riqueza_lexica_global", 0.0)) for t in textos) / len(textos)


def _fmt_float(value) -> str:
    return f"{value:.1f}" if isinstance(value, (int, float)) else "-"


def _fmt_signed(value) -> str:
    return f"{float(value):+.3f}" if isinstance(value, (int, float)) else "-"


def _top_lista(items: list) -> str:
    if not items:
        return ""
    return ", ".join(str(item[0]) for item in items[:5])


def _top_dict(items: dict) -> str:
    if not items:
        return ""
    ordenados = sorted(items.items(), key=lambda item: item[1], reverse=True)
    return ", ".join(f"{clave}: {valor}" for clave, valor in ordenados[:4])


def _top_ngramas(items: list) -> str:
    valores = []
    for item in items[:4]:
        ngrama = item[0]
        if isinstance(ngrama, (list, tuple)):
            valores.append(" ".join(str(p) for p in ngrama))
        else:
            valores.append(str(ngrama))
    return ", ".join(valores)


def _secciones_texto(valores: list) -> str:
    if not valores:
        return "-"
    return " | ".join(f"S{idx + 1}: {float(valor):.3f}" for idx, valor in enumerate(valores[:4]))


def _entidades_texto(items: list) -> str:
    if not items:
        return "-"
    partes = []
    for item in items[:5]:
        if len(item) >= 3:
            partes.append(f"{item[0]} ({item[1]}, {item[2]})")
        elif len(item) >= 2:
            partes.append(f"{item[0]} ({item[1]})")
        else:
            partes.append(str(item[0]))
    return ", ".join(partes)


def _comparativa_texto(items: list) -> str:
    if not items:
        return "-"
    partes = []
    for item in items[:3]:
        partes.append(
            f"{item.get('titulo', '-')}: riqueza {float(item.get('riqueza', 0.0)):.3f}"
        )
    return "; ".join(partes)


def _similares_texto(similares: list[dict]) -> str:
    if not similares:
        return "Sin documentos similares con similitud positiva."
    return "\n".join(
        f"- [{float(item.get('similitud', 0.0)):.4f}] {item.get('titulo', '')}"
        for item in similares[:5]
    )


def _serializar_basico(analisis: dict) -> dict:
    resultado = {k: v for k, v in analisis.items() if not k.startswith("_")}
    resultado["top_bigramas"] = [[list(b), c] for b, c in analisis.get("top_bigramas", [])]
    resultado["top_trigramas"] = [[list(t), c] for t, c in analisis.get("top_trigramas", [])]
    return resultado
