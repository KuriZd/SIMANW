from __future__ import annotations

import json
from pathlib import Path

import customtkinter as ctk

from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H1, FONT_H2, FONT_META, FONT_MONO, THEME


class SeccionEvidencia(ctk.CTkFrame):
    """Evidencia academica: estado interno, advertencias, errores y artefactos."""

    LABELS = [
        ("extraction", "Extraction"),
        ("nlp", "NLP"),
        ("analysis", "Analysis"),
        ("search", "Search"),
        ("qa", "Q&A"),
        ("graph", "Knowledge Graph"),
        ("reports", "Reports"),
    ]

    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        if not self.root_app.resultado_actual:
            center = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
            center.grid(row=0, column=0)
            ctk.CTkLabel(center, text="No evidence yet", font=FONT_H1, text_color=THEME["text_2"]).grid(row=0, column=0)
            return

        scroll = ctk.CTkScrollableFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew", padx=18, pady=12)
        scroll.grid_columnconfigure(0, weight=1)
        self._status_card(scroll).grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._academic_card(scroll).grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self._messages_card(scroll).grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self._artifacts_card(scroll).grid(row=3, column=0, sticky="ew")

    def _card(self, master) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        frame.grid_columnconfigure(0, weight=1)
        return frame

    def _status_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        status = self.root_app.resultado_actual.estado_pipeline
        ctk.CTkLabel(card, text="Pipeline Status", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        for row, (attr, label) in enumerate(self.LABELS, start=1):
            value = getattr(status, attr)
            color = THEME["success"] if value == "completed" else THEME["warning"] if value == "partial" else THEME["error"] if value == "error" else THEME["text_2"]
            ctk.CTkLabel(card, text=f"{label}: {value}", font=FONT_BODY, text_color=color).grid(
                row=row, column=0, sticky="w", padx=CARD_PADDING, pady=2
            )
        return card

    def _academic_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Academic Criteria Evidence", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        evidencias = self._cargar_evidencias()
        if not evidencias:
            ctk.CTkLabel(
                card,
                text="No academic evidence recorded yet. Run the related feature from its product module.",
                font=FONT_BODY,
                text_color=THEME["text_2"],
                anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
            return card

        row = 1
        for ac, data in sorted(evidencias.items()):
            estado = data.get("estado", "pendiente")
            color = THEME["success"] if estado == "completo" else THEME["warning"] if estado == "parcial" else THEME["text_2"]
            metricas = _metricas_texto(data)
            archivos = data.get("archivo_json") or ", ".join(data.get("archivos", []))
            texto = (
                f"{ac}: {estado} | {data.get('ejecutado_desde', 'modulo interno')}\n"
                f"{metricas}\n"
                f"Archivo: {archivos or 'sin archivo registrado'}"
            )
            ctk.CTkLabel(card, text=texto, font=FONT_BODY, text_color=color, justify="left", anchor="w").grid(
                row=row, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 8)
            )
            row += 1
        return card

    def _messages_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        result = self.root_app.resultado_actual
        ctk.CTkLabel(card, text="Warnings and Errors", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        messages = [f"WARNING: {m}" for m in result.advertencias] + [f"ERROR: {m}" for m in result.errores]
        text = "\n".join(messages) or "No warnings or errors."
        ctk.CTkLabel(card, text=text, font=FONT_BODY, text_color=THEME["text_2"], justify="left", anchor="w").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING)
        )
        return card

    def _cargar_evidencias(self) -> dict:
        result = self.root_app.resultado_actual
        if result and getattr(result, "evidencias_ac", None):
            return result.evidencias_ac
        ruta = Path("outputs/evidence/academic_evidence.json")
        if ruta.exists():
            try:
                data = json.loads(ruta.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    def _artifacts_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Generated Artifacts", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8)
        )
        for row, ruta in enumerate(self.root_app.resultado_actual.archivos_generados, start=1):
            ctk.CTkLabel(card, text=ruta, font=FONT_MONO, text_color=THEME["accent"], anchor="w").grid(
                row=row, column=0, sticky="w", padx=CARD_PADDING, pady=2
            )
        return card


def _metricas_texto(data: dict) -> str:
    claves = [
        "noticias_extraidas",
        "paginas_visitadas",
        "robots_permitido",
        "delay_segundos",
        "duplicados_omitidos",
        "textos_analizados",
        "unigramas",
        "bigramas",
        "trigramas",
        "riqueza_promedio",
        "total_textos",
        "total_clases",
        "mejor_modelo",
        "accuracy",
        "accuracy_std",
        "total_documentos",
        "total_consultas",
        "ganador_f1",
        "ganador_map",
        "map_booleano",
        "map_vectorial",
        "origen_consultas",
        "criterio_relevancia",
        "endpoint",
        "wikidata_online",
        "modo",
        "entidades_evaluadas",
        "total_enlaces_externos",
        "triples_antes",
        "triples_despues",
        "total_registros",
        "registros_validos",
        "registros_rechazados",
        "duplicados_exactos",
        "duplicados_casi_identicos",
        "granularidad",
        "total_temas",
        "numero_consultas",
        "origen_consultas",
        "consultas_reales",
        "historial_alertas",
        "alertas_generadas",
        "alertas_duplicadas_evitadas",
        "participantes",
        "datos",
        "version_proyecto",
        "fuente_noticias",
        "violaciones_encontradas",
        "enlaces_externos_creados",
    ]
    partes = [f"{clave}: {data[clave]}" for clave in claves if clave in data]
    return " | ".join(partes) if partes else "Metricas: sin metricas registradas"
