"""AC-8: Control de calidad del corpus."""
from __future__ import annotations

import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from src.control_calidad import ControlCalidadCorpus
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME

_NOTICIAS_DEMO = [
    {"titulo": "Avances en inteligencia artificial generativa",
     "cuerpo": "La inteligencia artificial generativa transforma procesos de software, educacion y analisis de datos.",
     "fecha": "2026-05-10", "autor": "Maria Garcia", "categoria_original": "tecnologia",
     "url": "https://demo.test/noticias/ia", "fuente": "https://demo.test"},
    {"titulo": "Mercados reaccionan a nuevas tasas",
     "cuerpo": "La Reserva Federal ajusta tasas de interes ante presiones inflacionarias y expectativas del mercado.",
     "fecha": "2026-05-11", "autor": "Juan Lopez", "categoria_original": "economia",
     "url": "https://demo.test/noticias/economia", "fuente": "https://demo.test"},
    {"titulo": "", "cuerpo": "Sin titulo, debe rechazarse.",
     "fecha": "2026-05-12", "autor": "Autor", "categoria_original": "general",
     "url": "https://demo.test/noticias/sin-titulo", "fuente": "https://demo.test"},
    {"titulo": "Cuerpo muy corto", "cuerpo": "corto",
     "fecha": "2026-05-12", "autor": "Autor", "categoria_original": "general",
     "url": "https://demo.test/noticias/corto", "fuente": "https://demo.test"},
    {"titulo": "Fecha invalida", "cuerpo": "Fecha en formato incorrecto que viola la regla ISO YYYY-MM-DD del corpus.",
     "fecha": "25/05/2026", "autor": "Autor", "categoria_original": "general",
     "url": "https://demo.test/noticias/fecha", "fuente": "https://demo.test"},
    {"titulo": "Duplicado exacto por URL",
     "cuerpo": "Esta noticia comparte la misma URL que la primera y sera detectada como duplicado.",
     "fecha": "2026-05-13", "autor": "Copia", "categoria_original": "tecnologia",
     "url": "https://demo.test/noticias/ia", "fuente": "https://demo.test"},
    {"titulo": "Avances en inteligencia artificial generativa",
     "cuerpo": "Titulo identico al primer registro, detectado como duplicado casi identico.",
     "fecha": "2026-05-14", "autor": "Otro Autor", "categoria_original": "tecnologia",
     "url": "https://demo.test/noticias/ia-copia", "fuente": "https://demo.test"},
]


class Ac8CalidadFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.control: ControlCalidadCorpus | None = None

        self.stat_total_var = ctk.StringVar(value="—")
        self.stat_validos_var = ctk.StringVar(value="—")
        self.stat_rechazados_var = ctk.StringVar(value="—")
        self.stat_dup_url_var = ctk.StringVar(value="—")
        self.stat_dup_tit_var = ctk.StringVar(value="—")
        self.estado_var = ctk.StringVar(value="Sin validar")
        self._build()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=240, weight=0)
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
        ctk.CTkLabel(card, text="Control de calidad", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        ctk.CTkLabel(card,
                     text="Valida titulo, cuerpo, fecha,\nURL, autor, categoria y fuente.\nDetecta duplicados exactos\ny casi identicos.",
                     font=FONT_META, text_color=THEME["text_2"], justify="left").grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 10))
        self.btn_validar = ctk.CTkButton(
            card, text="Validar corpus", command=self._validar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_validar.grid(row=2, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))
        self.btn_exportar = ctk.CTkButton(
            card, text="Exportar informes", command=self._exportar,
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
        metricas = [
            ("Total", self.stat_total_var),
            ("Validos", self.stat_validos_var),
            ("Rechazados", self.stat_rechazados_var),
            ("Dup. URL", self.stat_dup_url_var),
            ("Dup. titulo", self.stat_dup_tit_var),
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
        ctk.CTkLabel(card, text="Informe de calidad", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, CARD_PADDING))
        return card

    def _build_output_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(0, weight=1)
        self.output_box = ctk.CTkTextbox(
            card, fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1,
            text_color=THEME["text_1"], font=FONT_MONO, wrap="word", state="disabled")
        self.output_box.grid(row=0, column=0, sticky="nsew",
                              padx=CARD_PADDING, pady=CARD_PADDING)
        return card

    def _validar(self) -> None:
        self.btn_validar.configure(state="disabled")
        self.estado_var.set("Validando…")
        self.root_app.set_estado("AC-8: validando corpus…", "loading")
        self.root_app.show_progress()
        noticias = self.root_app.noticias or _NOTICIAS_DEMO
        threading.Thread(target=self._validar_bg, args=(noticias,), daemon=True).start()

    def _validar_bg(self, noticias: list[dict]) -> None:
        try:
            ctrl = ControlCalidadCorpus()
            ctrl.validar(noticias)
            informe = ctrl.generar_informe()
            resumen = ctrl.parrafo_resumen()
            self.control = ctrl
            self.after(0, lambda: self._on_ok(informe, resumen))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_ok(self, informe: dict, resumen: str) -> None:
        self.stat_total_var.set(str(informe["total_registros"]))
        self.stat_validos_var.set(str(informe["registros_validos"]))
        self.stat_rechazados_var.set(str(informe["registros_rechazados"]))
        self.stat_dup_url_var.set(str(informe["duplicados_exactos_url"]))
        self.stat_dup_tit_var.set(str(informe["duplicados_casi_identicos_titulo"]))

        lineas = [
            f"  Total registros    : {informe['total_registros']}",
            f"  Validos            : {informe['registros_validos']}",
            f"  Rechazados         : {informe['registros_rechazados']}",
            f"  Invalidos/incompl. : {informe['invalidos_o_incompletos']}",
            f"  Duplicados URL     : {informe['duplicados_exactos_url']}",
            f"  Duplicados titulo  : {informe['duplicados_casi_identicos_titulo']}",
            "",
            "  RESUMEN",
            "",
        ]
        lineas += ["  " + linea for linea in resumen.splitlines()]

        if informe["detalle_rechazados"]:
            lineas += ["", "  DETALLE DE RECHAZADOS"]
            for r in informe["detalle_rechazados"]:
                titulo = (r["titulo"] or "(sin titulo)")[:45]
                lineas.append(f"  - {titulo}")
                for m in r["motivos"]:
                    lineas.append(f"      {m}")

        self._set_output("\n".join(lineas))
        self.estado_var.set("Validacion completada")
        self.btn_validar.configure(state="normal")
        self.btn_exportar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(
            f"AC-8: {informe['registros_validos']} validos, "
            f"{informe['registros_rechazados']} rechazados", "ok")

    def _exportar(self) -> None:
        if not self.control:
            return
        try:
            self.control.guardar_informe("data/ac8_informe_calidad.json")
            self.control.guardar_corpus_depurado("data/corpus_depurado_ac8.json")
            self.control.guardar_rechazados("data/registros_rechazados_ac8.json")
            self.control.guardar_resumen_markdown("reports/resumen_calidad_ac8.md")
            self.root_app.set_estado("AC-8: informes exportados", "ok")
        except Exception as exc:
            messagebox.showerror("AC-8", str(exc))

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_validar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-8", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")
