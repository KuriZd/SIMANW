"""AC-13: Publicacion semantica y validacion RDF del Knowledge Graph."""
from __future__ import annotations

import json
import threading
from tkinter import messagebox

import customtkinter as ctk

from src.knowledge_graph import (
    QUERY_AC13_AUTORES_PRODUCTIVOS,
    QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
    QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
    KnowledgeGraphSIMANW,
)
from src.tendencias_temporales import NOTICIAS_AC9_DEMO
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME

_QUERIES = {
    "Autores productivos": QUERY_AC13_AUTORES_PRODUCTIVOS,
    "Sentimiento por categoria": QUERY_AC13_SENTIMIENTO_POR_CATEGORIA,
    "Noticias negativas recientes": QUERY_AC13_NOTICIAS_RECIENTES_NEGATIVAS,
}


class Ac13PublicacionFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.kg: KnowledgeGraphSIMANW | None = None

        self.stat_triples_var = ctk.StringVar(value="—")
        self.stat_conforme_var = ctk.StringVar(value="—")
        self.stat_enlaces_var = ctk.StringVar(value="—")
        self.query_sel_var = ctk.StringVar(value=list(_QUERIES)[0])
        self.estado_var = ctk.StringVar(value="Sin publicar")
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
        self._build_metricas_card(left).grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self._build_query_card(left).grid(row=2, column=0, sticky="ew")
        self._build_titulo_card(right).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_output_card(right).grid(row=1, column=0, sticky="nsew")

    def _build_control_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Publicacion semantica RDF", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        ctk.CTkLabel(card,
                     text="Construye KG, exporta Turtle\ny JSON-LD, valida con SHACL\ny enlaza con Wikidata.",
                     font=FONT_META, text_color=THEME["text_2"], justify="left").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10))
        self.btn_publicar = ctk.CTkButton(
            card, text="Publicar KG semantico", command=self._publicar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_publicar.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        self.btn_exportar = ctk.CTkButton(
            card, text="Guardar Turtle + JSON-LD", command=self._exportar,
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"], state="disabled")
        self.btn_exportar.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        ctk.CTkLabel(card, text="Estado", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=4, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(card, textvariable=self.estado_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=5, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_metricas_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        for i, (label, var) in enumerate([
            ("Triples RDF", self.stat_triples_var),
            ("SHACL conforme", self.stat_conforme_var),
            ("Enlaces externos", self.stat_enlaces_var),
        ]):
            ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=i * 2, column=0, sticky="w", padx=CARD_PADDING,
                pady=(CARD_PADDING if i == 0 else 0, 0))
            ctk.CTkLabel(card, textvariable=var, font=FONT_BODY,
                         text_color=THEME["text_1"], anchor="w").grid(
                row=i * 2 + 1, column=0, sticky="w", padx=CARD_PADDING,
                pady=(0, 4 if i < 2 else CARD_PADDING))
        return card

    def _build_query_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Consulta SPARQL", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        ctk.CTkOptionMenu(
            card, values=list(_QUERIES),
            variable=self.query_sel_var,
            fg_color=THEME["bg_input"], button_color=THEME["accent"],
            button_hover_color=THEME["accent"], text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"], dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"]).grid(
            row=1, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 8))
        self.btn_consultar = ctk.CTkButton(
            card, text="Ejecutar consulta SPARQL", command=self._consultar,
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"], state="disabled")
        self.btn_consultar.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING,
                                 pady=(0, CARD_PADDING))
        return card

    def _build_titulo_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Grafo RDF y SPARQL", font=FONT_H2,
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

    def _publicar(self) -> None:
        self.btn_publicar.configure(state="disabled")
        self.estado_var.set("Construyendo KG…")
        self.root_app.set_estado("AC-13: construyendo KG semantico…", "loading")
        self.root_app.show_progress()
        noticias = self.root_app.noticias or NOTICIAS_AC9_DEMO
        threading.Thread(target=self._publicar_bg, args=(noticias,), daemon=True).start()

    def _publicar_bg(self, noticias: list[dict]) -> None:
        try:
            kg = KnowledgeGraphSIMANW()
            noticias_kg = []
            for i, n in enumerate(noticias[:10], start=1):
                sent = dict(n.get("sentimiento") or {})
                sent.setdefault("compound", 0.0)
                noticias_kg.append({
                    **n,
                    "autor": n.get("autor", f"Autor {i % 3}"),
                    "fuente": n.get("fuente", "https://demo.test"),
                    "url": n.get("url", f"https://demo.test/kg/{i}"),
                    "sentimiento": sent,
                    "fecha": n.get("fecha", f"2026-05-{i:02d}"),
                })
            kg.construir_desde_noticias(noticias_kg)
            enlaces = kg.agregar_enlaces_externos_basicos()
            validacion = kg.validar_formas()
            self.kg = kg
            self.after(0, lambda: self._on_ok(kg, enlaces, validacion))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_ok(self, kg: KnowledgeGraphSIMANW, enlaces: list, validacion: dict) -> None:
        self.stat_triples_var.set(str(kg.total_triples()))
        self.stat_conforme_var.set("Si" if validacion["conforme"] else "No")
        self.stat_enlaces_var.set(str(len(enlaces)))

        lineas = [
            f"  Triples RDF         : {kg.total_triples()}",
            f"  SHACL conforme      : {'Si' if validacion['conforme'] else 'No'}",
            f"  Violaciones SHACL   : {len(validacion['violaciones'])}",
            f"  Enlaces externos    : {len(enlaces)}",
            "",
            "  CONSULTAS SPARQL",
        ]
        for nombre, query in _QUERIES.items():
            filas = kg.consultar(query)
            lineas.append(f"  [{nombre}]  {len(filas)} fila(s)")

        lineas += ["", "  FRAGMENTO JSON-LD (noticia 1)", ""]
        try:
            fragmento = kg.fragmento_jsonld_noticia(1)
            fragmento_texto = json.dumps(fragmento, ensure_ascii=False, indent=2)
            lineas += [f"  {l}" for l in fragmento_texto.splitlines()]
        except Exception:
            lineas.append("  (fragmento no disponible)")

        lineas += ["", "  NOTA DE REUTILIZACION", ""]
        lineas += ["  " + l for l in kg.nota_reutilizacion_datos().splitlines()]

        self._set_output("\n".join(lineas))
        self.estado_var.set("KG publicado")
        self.btn_publicar.configure(state="normal")
        self.btn_exportar.configure(state="normal")
        self.btn_consultar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(
            f"AC-13: {kg.total_triples()} triples, "
            f"SHACL {'conforme' if validacion['conforme'] else 'no conforme'}", "ok")

    def _consultar(self) -> None:
        if not self.kg:
            return
        nombre = self.query_sel_var.get()
        query = _QUERIES[nombre]
        try:
            filas = self.kg.consultar(query)
            lineas = [f"\n  -- SPARQL: {nombre} --",
                      f"  {len(filas)} fila(s) recuperadas"]
            for fila in filas[:10]:
                lineas.append(f"    {dict(fila)}")
            self._append_output("\n".join(lineas))
        except Exception as exc:
            self._on_error(str(exc))

    def _exportar(self) -> None:
        if not self.kg:
            return
        try:
            rutas = self.kg.exportar_rdf("data/ac13_simanw")
            self.root_app.set_estado(
                f"AC-13: {rutas['turtle']} y {rutas['json-ld']} guardados", "ok")
        except Exception as exc:
            messagebox.showerror("AC-13", str(exc))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_publicar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-13", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")

    def _append_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.insert("end", texto)
        self.output_box.configure(state="disabled")
        self.output_box.see("end")
