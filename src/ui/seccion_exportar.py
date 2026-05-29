"""Seccion 'Exportar': artefactos generados, estado de archivos y reexportacion."""
from __future__ import annotations

import os
from pathlib import Path

import customtkinter as ctk

from src.fase1_service import Fase1Service
from src.fase2_service import Fase2Service
from src.ui_theme import (
    CARD_PADDING,
    CARD_RADIUS,
    FONT_BODY,
    FONT_H1,
    FONT_H2,
    FONT_META,
    FONT_MONO,
    THEME,
)


class SeccionExportar(ctk.CTkFrame):
    """Muestra los archivos del ultimo analisis y permite abrirlos."""

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self._svc_f1 = Fase1Service()
        self._svc_f2 = Fase2Service()
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        if not self.root_app.noticias:
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
        ctk.CTkLabel(center, text="Sin archivos generados", font=FONT_H1, text_color=THEME["text_2"]).grid(
            row=0, column=0, pady=(0, 8)
        )
        ctk.CTkLabel(
            center,
            text="Analiza noticias primero para generar archivos.",
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
        rutas = self.root_app.rutas_exportacion
        noticias = self.root_app.noticias
        corpus = self.root_app.corpus_procesado

        scroll = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew", padx=18, pady=12)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        self._build_raw_card(scroll, rutas, noticias).grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        self._build_nlp_card(scroll, rutas, corpus).grid(row=0, column=1, sticky="nsew", pady=(0, 12))
        self._build_artifacts_card(scroll, rutas).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self._build_generated_files_card(scroll).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self._build_actions_card(scroll).grid(row=3, column=0, columnspan=2, sticky="ew")

    def _build_raw_card(self, master, rutas: dict, noticias: list[dict]) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Corpus crudo (Fase 1)", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4)
        )
        ctk.CTkLabel(card, text=f"{len(noticias)} noticias", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10)
        )
        self._path_label(card, "JSON", rutas.get("noticias_json"), 2)
        self._path_label(card, "CSV", rutas.get("noticias_csv"), 4)
        ctk.CTkButton(
            card,
            text="Re-exportar JSON",
            command=lambda: self._reexportar_raw("json"),
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        ).grid(row=6, column=0, sticky="ew", padx=CARD_PADDING, pady=(8, 4))
        ctk.CTkButton(
            card,
            text="Re-exportar CSV",
            command=lambda: self._reexportar_raw("csv"),
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        ).grid(row=7, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_nlp_card(self, master, rutas: dict, corpus: list[dict]) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Corpus NLP (Fase 2)", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4)
        )
        ctk.CTkLabel(card, text=f"{len(corpus)} documentos procesados", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10)
        )
        self._path_label(card, "JSON", rutas.get("corpus_json"), 2)
        self._path_label(card, "CSV", rutas.get("corpus_csv"), 4)
        ctk.CTkButton(
            card,
            text="Re-exportar JSON",
            command=lambda: self._reexportar_nlp("json"),
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        ).grid(row=6, column=0, sticky="ew", padx=CARD_PADDING, pady=(8, 4))
        ctk.CTkButton(
            card,
            text="Re-exportar CSV",
            command=lambda: self._reexportar_nlp("csv"),
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        ).grid(row=7, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_artifacts_card(self, master, rutas: dict) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Artefactos por fase y AC", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4)
        )
        for row, (key, label) in enumerate(ARTIFACT_KEYS, start=1):
            info = artifact_info(label, rutas.get(key))
            color = THEME["accent"] if info["exists"] else THEME["warning"]
            ctk.CTkLabel(card, text=f"{label}:", font=FONT_META, text_color=THEME["text_2"]).grid(
                row=row * 2 - 1, column=0, sticky="w", padx=CARD_PADDING
            )
            ctk.CTkLabel(card, text=info["display"], font=FONT_MONO, text_color=color, anchor="w").grid(
                row=row * 2, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 6)
            )
        return card

    def _build_generated_files_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Todos los archivos registrados", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        result = getattr(self.root_app, "resultado_actual", None)
        archivos = list(getattr(result, "archivos_generados", []) or []) or list(self.root_app.rutas_exportacion.values())
        for row, ruta in enumerate(archivos, start=1):
            info = artifact_info("archivo", ruta)
            color = THEME["accent"] if info["exists"] else THEME["warning"]
            ctk.CTkLabel(card, text=info["display"], font=FONT_MONO, text_color=color, anchor="w").grid(
                row=row, column=0, sticky="w", padx=CARD_PADDING, pady=2
            )
        return card

    def _build_actions_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Acciones de archivos", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        ctk.CTkButton(
            card,
            text="Abrir carpeta de exportaciones",
            command=self._abrir_carpeta_exportaciones,
            fg_color=THEME["bg_input"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_1"],
        ).grid(row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        ctk.CTkButton(
            card,
            text="Abrir reporte final",
            command=lambda: self._abrir_archivo(self.root_app.rutas_exportacion.get("reporte_final", "")),
            fg_color=THEME["accent"],
            hover_color=THEME["accent"],
            text_color=THEME["text_1"],
        ).grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _path_label(self, card, label: str, ruta: str | None, row: int) -> None:
        info = artifact_info(label, ruta)
        ctk.CTkLabel(card, text=f"{label}:", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=row, column=0, sticky="w", padx=CARD_PADDING
        )
        ctk.CTkLabel(
            card,
            text=info["display"],
            font=FONT_MONO,
            text_color=THEME["accent"] if info["exists"] else THEME["warning"],
            anchor="w",
        ).grid(row=row + 1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 6))

    def _reexportar_raw(self, fmt: str) -> None:
        try:
            noticias = self.root_app.noticias
            ruta = self._svc_f1.exportar_json(noticias) if fmt == "json" else self._svc_f1.exportar_csv(noticias)
            self.root_app.set_estado(f"Exportado: {ruta}", "ok")
        except Exception as exc:
            self.root_app.set_estado(str(exc), "error")

    def _reexportar_nlp(self, fmt: str) -> None:
        try:
            corpus = self.root_app.corpus_procesado
            ruta = self._svc_f2.exportar_json(corpus) if fmt == "json" else self._svc_f2.exportar_csv(corpus)
            self.root_app.set_estado(f"Exportado: {ruta}", "ok")
        except Exception as exc:
            self.root_app.set_estado(str(exc), "error")

    def _abrir_archivo(self, ruta: str) -> None:
        path = Path(ruta)
        if not ruta or not path.exists():
            self.root_app.set_estado(f"Archivo no encontrado: {ruta or 'sin ruta'}", "warning")
            return
        try:
            os.startfile(path)  # type: ignore[attr-defined]
            self.root_app.set_estado(f"Abierto: {path}", "ok")
        except Exception as exc:
            self.root_app.set_estado(f"No se pudo abrir {path}: {exc}", "error")

    def _abrir_carpeta_exportaciones(self) -> None:
        carpeta = Path("outputs") if Path("outputs").exists() else Path(".")
        try:
            os.startfile(carpeta.resolve())  # type: ignore[attr-defined]
            self.root_app.set_estado(f"Carpeta abierta: {carpeta}", "ok")
        except Exception as exc:
            self.root_app.set_estado(f"No se pudo abrir carpeta: {exc}", "error")


ARTIFACT_KEYS = [
    ("ac8_informe_json", "AC-8 informe de calidad"),
    ("ac8_corpus_depurado", "AC-8 corpus depurado"),
    ("ac8_rechazados", "AC-8 rechazados"),
    ("analisis_ac2_json", "AC-2 analisis de discurso"),
    ("resultados_ac3_json", "AC-3 clasificacion"),
    ("resultados_ac5_json", "AC-5 evaluacion IRS"),
    ("tendencias_csv", "AC-9 tendencias CSV"),
    ("tendencias_png", "AC-9 tendencias PNG"),
    ("ac10_consultas", "AC-10 consultas"),
    ("ac10_historial", "AC-10 historial"),
    ("ac11_csv", "AC-11 usabilidad CSV"),
    ("ac12_manifest", "AC-12 manifiesto"),
    ("ac12_log", "AC-12 log"),
    ("ac12_checklist", "AC-12 checklist"),
    ("ac12_limitaciones", "AC-12 limitaciones"),
    ("kg_enriquecido_ac7_ttl", "AC-7 KG enriquecido"),
    ("enlaces_wikidata_ac7_json", "AC-7 enlaces Wikidata"),
    ("ac13_turtle", "AC-13 Turtle"),
    ("ac13_jsonld", "AC-13 JSON-LD"),
    ("ac13_validacion", "AC-13 SHACL"),
    ("ac13_glosario", "AC-13 glosario"),
    ("reporte_final", "Reporte final Markdown"),
    ("reporte_final_json", "Reporte final JSON"),
    ("academic_evidence", "Academic Evidence"),
]


def artifact_info(label: str, ruta: str | Path | None) -> dict:
    raw = str(ruta or "").strip()
    if not raw or raw in {"-", "—", "N/D"}:
        return {"label": label, "path": raw, "exists": False, "size": 0, "display": "faltante"}
    path = Path(raw)
    exists = path.exists()
    size = path.stat().st_size if exists and path.is_file() else 0
    status = "OK" if exists else "faltante"
    size_text = f" ({format_size(size)})" if exists and path.is_file() else ""
    return {
        "label": label,
        "path": raw,
        "exists": exists,
        "size": size,
        "display": f"[{status}] {raw}{size_text}",
    }


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
