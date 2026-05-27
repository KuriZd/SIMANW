"""Sección 'Dashboard' — resumen estadístico del último análisis."""
from __future__ import annotations

from collections import Counter

import customtkinter as ctk

from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, THEME


class SeccionDashboard(ctk.CTkFrame):
    """Panel de resumen: estadísticas, términos más frecuentes y estado del pipeline."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self._build()

    # ═══════════════════════════════════════════════════════════════════════════
    # Layout
    # ═══════════════════════════════════════════════════════════════════════════

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if not self.root_app.noticias:
            self._build_empty_state()
        else:
            self._build_dashboard()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    # ── estado vacío ──────────────────────────────────────────────────────────

    def _build_empty_state(self) -> None:
        center = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        center.grid(row=0, column=0)

        ctk.CTkLabel(
            center, text="Sin datos", font=FONT_H1, text_color=THEME["text_2"]
        ).grid(row=0, column=0, pady=(0, 8))
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

    # ── dashboard con datos ───────────────────────────────────────────────────

    def _build_dashboard(self) -> None:
        noticias   = self.root_app.noticias
        corpus     = self.root_app.corpus_procesado
        stats      = self.root_app.estadisticas_fase2
        pipeline   = self.root_app.pipeline_estado

        scroll = ctk.CTkScrollableFrame(
            self, fg_color=THEME["bg_base"], corner_radius=0
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=18, pady=12)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)
        scroll.grid_columnconfigure(2, weight=1)
        scroll.grid_columnconfigure(3, weight=1)

        # ── fila 1: tarjetas de stats ──────────────────────────────────────
        stat_items = [
            ("Noticias",       str(len(noticias))),
            ("Tokens totales", str(stats.get("total_tokens", "—"))),
            ("Vocabulario",    str(stats.get("vocabulario_total", "—"))),
            ("Tokens / doc",   _fmt_float(stats.get("promedio_tokens_doc"))),
        ]
        for col, (label, value) in enumerate(stat_items):
            self._build_stat_card(scroll, label, value).grid(
                row=0, column=col, sticky="nsew", padx=(0 if col else 0, 10 if col < 3 else 0), pady=(0, 12)
            )

        # ── fila 2: términos frecuentes + pipeline ─────────────────────────
        terminos_card = self._build_terminos_card(scroll, corpus)
        terminos_card.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 10), pady=(0, 12))

        pipeline_card = self._build_pipeline_card(scroll, pipeline)
        pipeline_card.grid(row=1, column=2, columnspan=2, sticky="nsew", pady=(0, 12))

        # ── fila 3: fuentes + categorías ────────────────────────────────────
        fuentes_card = self._build_fuentes_card(scroll, noticias)
        fuentes_card.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, 12))

        categorias_card = self._build_categorias_card(scroll, noticias)
        categorias_card.grid(row=3, column=0, columnspan=4, sticky="ew")

    def _build_stat_card(self, master, label: str, value: str) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text=value, font=("Segoe UI", 22, "bold"), text_color=THEME["accent"]
        ).grid(row=0, column=0, padx=CARD_PADDING, pady=(CARD_PADDING, 2))
        ctk.CTkLabel(
            card, text=label, font=FONT_META, text_color=THEME["text_2"]
        ).grid(row=1, column=0, padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_terminos_card(self, master, corpus: list[dict]) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Términos más frecuentes", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        top = _top_terms(corpus, n=12)
        if not top:
            ctk.CTkLabel(
                card, text="Sin datos NLP disponibles.", font=FONT_META, text_color=THEME["text_2"]
            ).grid(row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
            return card

        max_count = top[0][1] if top else 1
        for row, (term, count) in enumerate(top, start=1):
            bar_pct = int((count / max_count) * 100)
            line = ctk.CTkFrame(card, fg_color=THEME["bg_base"], corner_radius=0)
            line.grid(row=row, column=0, sticky="ew", padx=CARD_PADDING, pady=2)
            line.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                line, text=term, font=FONT_BODY, text_color=THEME["text_1"], width=120, anchor="w"
            ).grid(row=0, column=0)

            bar_frame = ctk.CTkFrame(line, fg_color=THEME["border"], corner_radius=3, height=10)
            bar_frame.grid(row=0, column=1, sticky="ew", padx=(8, 8))
            bar_frame.grid_propagate(False)
            bar_fill = ctk.CTkFrame(
                bar_frame,
                fg_color=THEME["accent"],
                corner_radius=3,
                height=10,
            )
            bar_fill.place(relx=0, rely=0, relwidth=bar_pct / 100, relheight=1)

            ctk.CTkLabel(
                line, text=str(count), font=FONT_META, text_color=THEME["text_2"], width=30
            ).grid(row=0, column=2)

        return card

    def _build_pipeline_card(self, master, pipeline: dict) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Estado del pipeline", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        _steps_info = [
            ("extraccion",           "Extracción de noticias"),
            ("exportacion_cruda",    "Exportación cruda"),
            ("nlp",                  "Procesamiento NLP"),
            ("exportacion_procesada","Exportación NLP"),
        ]
        _icons = {"ok": ("✓", THEME["success"]), "warning": ("⚠", THEME["warning"]),
                  "error": ("✗", THEME["error"])}

        for row, (key, label) in enumerate(_steps_info, start=1):
            estado = pipeline.get(key)
            if estado:
                icon, color = _icons.get(estado, ("?", THEME["text_2"]))
            else:
                icon, color = "○", THEME["text_2"]

            ctk.CTkLabel(card, text=icon, font=FONT_BODY, text_color=color, width=22).grid(
                row=row, column=0, padx=(CARD_PADDING, 4), pady=3
            )
            ctk.CTkLabel(card, text=label, font=FONT_BODY, text_color=THEME["text_1"], anchor="w").grid(
                row=row, column=1, sticky="w", padx=(0, CARD_PADDING), pady=3
            )

        card.grid_columnconfigure(1, weight=1)
        return card

    def _build_fuentes_card(self, master, noticias: list[dict]) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Distribución por fuente", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, columnspan=99, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        counter = Counter(n.get("fuente_nombre", "Demo local") for n in noticias)
        total = len(noticias)

        for col, (fuente, cnt) in enumerate(counter.most_common()):
            pct_text = f"{cnt / total * 100:.0f}%" if total else "0%"
            frame = ctk.CTkFrame(card, fg_color=THEME["bg_base"], corner_radius=CARD_RADIUS)
            frame.grid(row=1, column=col, padx=(CARD_PADDING if col == 0 else 4, 4), pady=(0, CARD_PADDING))

            ctk.CTkLabel(
                frame, text=pct_text, font=("Segoe UI", 14, "bold"), text_color=THEME["accent"]
            ).grid(row=0, column=0, padx=8, pady=(6, 0))
            ctk.CTkLabel(
                frame, text=f"{fuente} ({cnt})", font=FONT_META, text_color=THEME["text_2"]
            ).grid(row=1, column=0, padx=8, pady=(0, 6))

        return card

    def _build_categorias_card(self, master, noticias: list[dict]) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(
            card, text="Distribución por categoría", font=FONT_H2, text_color=THEME["text_1"]
        ).grid(row=0, column=0, columnspan=99, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        counter = Counter(n.get("categoria", "sin_categoria") for n in noticias)
        total   = len(noticias)

        for col, (cat, cnt) in enumerate(counter.most_common()):
            pct_text = f"{cnt / total * 100:.0f}%" if total else "0%"
            frame = ctk.CTkFrame(card, fg_color=THEME["bg_base"], corner_radius=CARD_RADIUS)
            frame.grid(row=1, column=col, padx=(CARD_PADDING if col == 0 else 4, 4), pady=(0, CARD_PADDING))

            ctk.CTkLabel(
                frame, text=pct_text, font=("Segoe UI", 14, "bold"), text_color=THEME["accent"]
            ).grid(row=0, column=0, padx=8, pady=(6, 0))
            ctk.CTkLabel(
                frame, text=f"{cat} ({cnt})", font=FONT_META, text_color=THEME["text_2"]
            ).grid(row=1, column=0, padx=8, pady=(0, 6))

        return card


# ── helpers ──────────────────────────────────────────────────────────────────

def _top_terms(corpus: list[dict], n: int = 12) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for item in corpus:
        for term in item.get("terminos", []):
            counter[term] += 1
    return counter.most_common(n)


def _fmt_float(value) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.1f}"
    return "—"
