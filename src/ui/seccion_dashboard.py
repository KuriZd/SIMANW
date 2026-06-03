from __future__ import annotations

from collections import Counter

import customtkinter as ctk

from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, FONT_STAT, FONT_STAT_LARGE, THEME

_DISTRIBUTION_CARD_MIN_WIDTH = 180
_DISTRIBUTION_MAX_COLUMNS = 4


class SeccionDashboard(ctk.CTkFrame):
    """Panel de resumen con estado real del pipeline SIMANW."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        if not self.root_app.noticias:
            self._build_empty_state()
        else:
            self._build_dashboard()

    def _card(self, master) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _build_empty_state(self) -> None:
        center = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        center.grid(row=0, column=0)
        ctk.CTkLabel(center, text="Sin datos", font=FONT_H1, text_color=THEME["text_2"]).grid(row=0, column=0, pady=(0, 8))
        ctk.CTkLabel(
            center,
            text="Carga y analiza noticias para ver el dashboard.",
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

    def _build_dashboard(self) -> None:
        noticias = self.root_app.noticias
        corpus = self.root_app.corpus_procesado
        stats = self.root_app.estadisticas_fase2
        pipeline = self.root_app.pipeline_estado
        resultado = getattr(self.root_app, "resultado_actual", None)
        grafo_info = getattr(resultado, "grafo_info", {}) if resultado else {}

        scroll = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew", padx=18, pady=12)
        for col in range(4):
            scroll.grid_columnconfigure(col, weight=1)

        stat_items = [
            ("Noticias", str(len(noticias))),
            ("Tokens totales", str(stats.get("total_tokens", "-"))),
            ("Sentimiento", _fmt_float(_sentimiento_promedio(noticias))),
            ("Triples RDF", str(grafo_info.get("total_triples", "-"))),
        ]
        for col, (label, value) in enumerate(stat_items):
            self._build_stat_card(scroll, label, value).grid(
                row=0,
                column=col,
                sticky="nsew",
                padx=(0, 10 if col < 3 else 0),
                pady=(0, 12),
            )

        self._build_terminos_card(scroll, corpus).grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 10), pady=(0, 12))
        self._build_pipeline_card(scroll, pipeline).grid(row=1, column=2, columnspan=2, sticky="nsew", pady=(0, 12))
        self._build_fuentes_card(scroll, noticias).grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, 12))
        self._build_categorias_card(scroll, noticias).grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 12))

        analisis = getattr(resultado, "analisis", {}) if resultado else {}
        self._build_sentimientos_card(scroll, noticias, analisis).grid(row=4, column=0, columnspan=4, sticky="ew")

    def _build_stat_card(self, master, label: str, value: str) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text=value, font=FONT_STAT_LARGE, text_color=THEME["accent"]).grid(
            row=0, column=0, padx=CARD_PADDING, pady=(CARD_PADDING, 2)
        )
        ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
            row=1, column=0, padx=CARD_PADDING, pady=(0, CARD_PADDING)
        )
        return card

    def _build_terminos_card(self, master, corpus: list[dict]) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Terminos mas frecuentes", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        top = _top_terms(corpus, n=12)
        if not top:
            ctk.CTkLabel(card, text="Sin datos NLP disponibles.", font=FONT_META, text_color=THEME["text_2"]).grid(
                row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING)
            )
            return card

        max_count = top[0][1] if top else 1
        for row, (term, count) in enumerate(top, start=1):
            line = ctk.CTkFrame(card, fg_color=THEME["bg_base"], corner_radius=0)
            line.grid(row=row, column=0, sticky="ew", padx=CARD_PADDING, pady=2)
            line.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(line, text=term, font=FONT_BODY, text_color=THEME["text_1"], width=120, anchor="w").grid(row=0, column=0)
            bar_frame = ctk.CTkFrame(line, fg_color=THEME["border"], corner_radius=3, height=10)
            bar_frame.grid(row=0, column=1, sticky="ew", padx=(8, 8))
            bar_frame.grid_propagate(False)
            ctk.CTkFrame(bar_frame, fg_color=THEME["accent"], corner_radius=3, height=10).place(
                relx=0, rely=0, relwidth=count / max_count, relheight=1
            )
            ctk.CTkLabel(line, text=str(count), font=FONT_META, text_color=THEME["text_2"], width=30).grid(row=0, column=2)
        return card

    def _build_pipeline_card(self, master, pipeline: dict) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Estado del pipeline", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        steps = [
            ("extraccion", "Extraccion de noticias"),
            ("nlp", "Procesamiento NLP"),
            ("analisis", "Analisis automatico"),
            ("busqueda", "Motor de busqueda"),
            ("qa", "Q&A contextual"),
            ("grafo", "Knowledge Graph"),
            ("reportes", "Reportes finales"),
        ]
        icons = {
            "completed": ("OK", THEME["success"]),
            "ok": ("OK", THEME["success"]),
            "partial": ("!", THEME["warning"]),
            "warning": ("!", THEME["warning"]),
            "error": ("X", THEME["error"]),
            "pending": ("-", THEME["text_2"]),
        }
        for row, (key, label) in enumerate(steps, start=1):
            icon, color = icons.get(pipeline.get(key, "pending"), ("-", THEME["text_2"]))
            ctk.CTkLabel(card, text=icon, font=FONT_BODY, text_color=color, width=28).grid(
                row=row, column=0, padx=(CARD_PADDING, 4), pady=3
            )
            ctk.CTkLabel(card, text=label, font=FONT_BODY, text_color=THEME["text_1"], anchor="w").grid(
                row=row, column=1, sticky="w", padx=(0, CARD_PADDING), pady=3
            )
        card.grid_columnconfigure(1, weight=1)
        return card

    def _build_fuentes_card(self, master, noticias: list[dict]) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Distribucion por fuente", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        self._build_distribution(card, Counter(n.get("fuente_nombre") or n.get("fuente") or "Demo local" for n in noticias), len(noticias))
        return card

    def _build_categorias_card(self, master, noticias: list[dict]) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Distribucion por categoria", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        counter = Counter(
            n.get("categoria_predicha") or n.get("categoria") or n.get("categoria_original") or "sin_categoria"
            for n in noticias
        )
        self._build_distribution(card, counter, len(noticias))
        return card

    def _build_sentimientos_card(self, master, noticias: list[dict], analisis: dict) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Análisis de sentimiento", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        dist = _sentimiento_distribucion(noticias, analisis)
        dominante = analisis.get("sentimiento_dominante") or (
            max(dist, key=dist.get) if dist else "neutral"
        )
        total = sum(dist.values())

        _SENT_COLORS = {
            "positivo": THEME["success"],
            "negativo": THEME["error"],
            "neutral":  THEME["text_2"],
            "mixed":    THEME["warning"],
        }
        dom_color = _SENT_COLORS.get(dominante, THEME["accent"])

        # Left: dominant sentiment badge
        badge = ctk.CTkFrame(card, fg_color=THEME["bg_base"], corner_radius=CARD_RADIUS)
        badge.grid(row=1, column=0, sticky="ns", padx=(CARD_PADDING, 8), pady=(0, CARD_PADDING))
        ctk.CTkLabel(badge, text=dominante.upper(), font=FONT_STAT_LARGE, text_color=dom_color).grid(
            row=0, column=0, padx=16, pady=(10, 2)
        )
        ctk.CTkLabel(badge, text="sentimiento dominante", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=1, column=0, padx=16, pady=(0, 10)
        )

        # Right: distribution bars
        bars = ctk.CTkFrame(card, fg_color=THEME["bg_base"], corner_radius=CARD_RADIUS)
        bars.grid(row=1, column=1, sticky="nsew", padx=(0, CARD_PADDING), pady=(0, CARD_PADDING))
        bars.grid_columnconfigure(1, weight=1)

        for row_idx, (etiqueta, count) in enumerate(
            sorted(dist.items(), key=lambda x: -x[1])
        ):
            pct = count / total if total else 0
            color = _SENT_COLORS.get(etiqueta, THEME["accent"])

            ctk.CTkLabel(
                bars, text=etiqueta, font=FONT_BODY, text_color=THEME["text_1"],
                width=80, anchor="w",
            ).grid(row=row_idx, column=0, padx=(CARD_PADDING, 6), pady=4, sticky="w")

            bar_track = ctk.CTkFrame(bars, fg_color=THEME["border"], corner_radius=4, height=14)
            bar_track.grid(row=row_idx, column=1, sticky="ew", padx=(0, 8), pady=4)
            bar_track.grid_propagate(False)
            ctk.CTkFrame(bar_track, fg_color=color, corner_radius=4, height=14).place(
                relx=0, rely=0, relwidth=pct, relheight=1
            )

            ctk.CTkLabel(
                bars, text=f"{count} ({pct:.0%})", font=FONT_META, text_color=THEME["text_2"],
                width=72, anchor="e",
            ).grid(row=row_idx, column=2, padx=(0, CARD_PADDING), pady=4)

        return card

    def _build_distribution(self, card, counter: Counter, total: int) -> None:
        card.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(card, fg_color=THEME["bg_surface"], corner_radius=0)
        container.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        items = counter.most_common()
        if not items:
            ctk.CTkLabel(
                container,
                text="Sin datos disponibles.",
                font=FONT_META,
                text_color=THEME["text_2"],
            ).grid(row=0, column=0, sticky="w")
            return

        state = {"columns": 0}

        def render(columns: int) -> None:
            columns = max(1, min(columns, len(items)))
            if state["columns"] == columns:
                return
            state["columns"] = columns
            for child in container.winfo_children():
                child.destroy()
            for col in range(_DISTRIBUTION_MAX_COLUMNS):
                container.grid_columnconfigure(col, weight=0, uniform="")
            for col in range(columns):
                container.grid_columnconfigure(col, weight=1, uniform="distribution")

            for index, (label, count) in enumerate(items):
                row = index // columns
                col = index % columns
                pct_text = f"{count / total * 100:.0f}%" if total else "0%"
                frame = ctk.CTkFrame(container, fg_color=THEME["bg_base"], corner_radius=CARD_RADIUS)
                frame.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
                frame.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(
                    frame,
                    text=pct_text,
                    font=FONT_STAT,
                    text_color=THEME["accent"],
                    anchor="center",
                ).grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 2))
                ctk.CTkLabel(
                    frame,
                    text=f"{label} ({count})",
                    font=FONT_META,
                    text_color=THEME["text_2"],
                    anchor="center",
                    wraplength=160,
                    justify="center",
                ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        def on_resize(event) -> None:
            available = max(event.width, _DISTRIBUTION_CARD_MIN_WIDTH)
            columns = min(_DISTRIBUTION_MAX_COLUMNS, max(1, available // _DISTRIBUTION_CARD_MIN_WIDTH))
            render(columns)

        render(min(_DISTRIBUTION_MAX_COLUMNS, len(items)))
        container.bind("<Configure>", on_resize)


def _top_terms(corpus: list[dict], n: int = 12) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for item in corpus:
        for term in item.get("terminos", []):
            counter[term] += 1
    return counter.most_common(n)


def _sentimiento_promedio(noticias: list[dict]) -> float | None:
    scores: list[float] = []
    for noticia in noticias:
        sentimiento = noticia.get("sentimiento")
        if not isinstance(sentimiento, dict):
            continue
        valor = sentimiento.get("compound", sentimiento.get("score"))
        try:
            scores.append(float(valor))
        except (TypeError, ValueError):
            continue
    return sum(scores) / len(scores) if scores else None


def _fmt_float(value) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "-"


def _sentimiento_distribucion(noticias: list[dict], analisis: dict) -> dict[str, int]:
    """Returns sentiment counter dict, preferring pre-computed analisis data."""
    precomputed = analisis.get("sentimientos")
    if isinstance(precomputed, dict) and precomputed:
        return {k: int(v) for k, v in precomputed.items()}
    counter: Counter[str] = Counter()
    for n in noticias:
        sent = n.get("sentimiento")
        if isinstance(sent, dict):
            etiqueta = sent.get("etiqueta", "neutral")
            counter[etiqueta] += 1
    return dict(counter) if counter else {"neutral": len(noticias)}
