"""AC-7: Enriquecimiento del Knowledge Graph con Wikidata."""
from __future__ import annotations

import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from src.enriquecedor_kg import enriquecer_categorias_demo
from src.knowledge_graph import KnowledgeGraphSIMANW
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME

_NOTICIAS_DEMO = [
    {"titulo": "Avances en inteligencia artificial",
     "cuerpo": "La IA y el aprendizaje automatico impulsan nuevas aplicaciones.",
     "categoria_predicha": "tecnologia", "fecha": "2026-05-09",
     "autor": "Autor 1", "fuente": "https://demo.test",
     "url": "https://demo.test/1", "sentimiento": {"etiqueta": "positivo", "compound": 0.4}},
    {"titulo": "Mercados financieros y economia global",
     "cuerpo": "La inflacion y las tasas presionan al mercado de valores.",
     "categoria_predicha": "economia", "fecha": "2026-05-08",
     "autor": "Autor 2", "fuente": "https://demo.test",
     "url": "https://demo.test/2", "sentimiento": {"etiqueta": "negativo", "compound": -0.3}},
    {"titulo": "Cambio climatico y ciencia ambiental",
     "cuerpo": "Investigadores publican datos sobre emisiones de carbono.",
     "categoria_predicha": "ciencia", "fecha": "2026-05-07",
     "autor": "Autor 3", "fuente": "https://demo.test",
     "url": "https://demo.test/3", "sentimiento": {"etiqueta": "negativo", "compound": -0.2}},
]


class Ac7EnriquecedorFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app

        self.stat_triples_antes_var = ctk.StringVar(value="—")
        self.stat_triples_despues_var = ctk.StringVar(value="—")
        self.stat_enlaces_var = ctk.StringVar(value="—")
        self.estado_var = ctk.StringVar(value="Sin enriquecer")
        self._build()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=250, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self._build_control_card(left).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_metricas_card(left).grid(row=1, column=0, sticky="ew")
        self._build_titulo_card(right).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_output_card(right).grid(row=1, column=0, sticky="nsew")

    def _build_control_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Enriquecimiento KG", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        ctk.CTkLabel(card, text="Enlaza entidades locales\ncon Wikidata (owl:sameAs)",
                     font=FONT_META, text_color=THEME["text_2"], justify="left").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10))
        self.btn_enriquecer = ctk.CTkButton(
            card, text="Enriquecer KG", command=self._enriquecer,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_enriquecer.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        self.btn_guardar = ctk.CTkButton(
            card, text="Guardar Turtle + JSON",
            command=self._guardar, state="disabled",
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"])
        self.btn_guardar.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        ctk.CTkLabel(card, text="Estado", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=4, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(card, textvariable=self.estado_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=5, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_metricas_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        metricas = [
            ("Triples antes", self.stat_triples_antes_var),
            ("Triples despues", self.stat_triples_despues_var),
            ("Enlaces externos", self.stat_enlaces_var),
        ]
        for i, (label, var) in enumerate(metricas):
            ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=i * 2, column=0, sticky="w", padx=CARD_PADDING,
                pady=(CARD_PADDING if i == 0 else 0, 0))
            ctk.CTkLabel(card, textvariable=var, font=FONT_BODY,
                         text_color=THEME["text_1"], anchor="w").grid(
                row=i * 2 + 1, column=0, sticky="w", padx=CARD_PADDING,
                pady=(0, 4 if i < len(metricas) - 1 else CARD_PADDING))
        return card

    def _build_titulo_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Resultado del enriquecimiento", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, CARD_PADDING))
        return card

    def _build_output_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(0, weight=1)
        self.output_box = ctk.CTkTextbox(
            card, fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1,
            text_color=THEME["text_1"], font=FONT_MONO, wrap="none", state="disabled")
        self.output_box.grid(row=0, column=0, sticky="nsew",
                              padx=CARD_PADDING, pady=CARD_PADDING)
        return card

    def _enriquecer(self) -> None:
        self.btn_enriquecer.configure(state="disabled")
        self.estado_var.set("Construyendo KG…")
        self.root_app.set_estado("AC-7: enriqueciendo KG…", "loading")
        self.root_app.show_progress()
        noticias = self.root_app.noticias or _NOTICIAS_DEMO
        threading.Thread(target=self._enriquecer_bg, args=(noticias,), daemon=True).start()

    def _enriquecer_bg(self, noticias: list[dict]) -> None:
        try:
            kg = KnowledgeGraphSIMANW()
            noticias_kg = []
            for i, n in enumerate(noticias[:10], start=1):
                sent = dict(n.get("sentimiento") or {})
                sent.setdefault("compound", 0.0)
                noticias_kg.append({**n, "sentimiento": sent,
                                     "fecha": n.get("fecha", f"2026-05-{i:02d}"),
                                     "autor": n.get("autor", f"Autor {i}"),
                                     "fuente": n.get("fuente", "https://demo.test"),
                                     "url": n.get("url", f"https://demo.test/{i}")})
            kg.construir_desde_noticias(noticias_kg)
            antes = kg.total_triples()
            enriquecedor = enriquecer_categorias_demo(kg)
            despues = kg.total_triples()
            enlaces = enriquecedor.enlaces_externos
            self._enriquecedor_cache = (kg, enriquecedor)
            self.after(0, lambda: self._on_ok(antes, despues, enlaces, enriquecedor))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_ok(self, antes: int, despues: int, enlaces: list, enriquecedor) -> None:
        self.stat_triples_antes_var.set(str(antes))
        self.stat_triples_despues_var.set(str(despues))
        self.stat_enlaces_var.set(str(len(enlaces)))

        lineas = [
            f"  Triples antes del enriquecimiento : {antes}",
            f"  Triples tras enriquecimiento      : {despues}",
            f"  Enlaces externos creados          : {len(enlaces)}",
            "",
            "  ENLACES locales -> Wikidata",
        ]
        for enlace in enlaces:
            local_id = enlace.get("local", "").rsplit("/", 1)[-1]
            wid = enlace.get("wikidata_id", enlace.get("wikidata", ""))
            etiqueta = enlace.get("etiqueta", "")
            lineas.append(f"    {local_id:<28} -> wd:{wid}  ({etiqueta})")

        lineas += ["", "  QUERY SPARQL SUGERIDA (tecnologia)"]
        lineas.append(enriquecedor.generar_query_wikidata("tecnologia"))

        for fila in enriquecedor.consulta_enriquecimiento():
            pass

        self._set_output("\n".join(lineas))
        self.estado_var.set("Enriquecimiento completado")
        self.btn_enriquecer.configure(state="normal")
        self.btn_guardar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(f"AC-7: {despues} triples, {len(enlaces)} enlaces", "ok")

    def _guardar(self) -> None:
        if not hasattr(self, "_enriquecedor_cache"):
            return
        try:
            _, enriquecedor = self._enriquecedor_cache
            ruta_ttl = Path("data/kg_enriquecido_ac7.ttl")
            ruta_json = Path("data/enlaces_wikidata_ac7.json")
            enriquecedor.guardar_grafo(ruta_ttl)
            enriquecedor.guardar_reporte_json(ruta_json)
            self.root_app.set_estado(f"AC-7: Turtle y JSON guardados", "ok")
        except Exception as exc:
            messagebox.showerror("AC-7", str(exc))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_enriquecer.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-7", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")
