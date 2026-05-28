"""AC-4: Analisis de hilo de discusion."""
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.analizador_hilo import HILO_IA_DEMO, AnalizadorHiloDiscusion
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME


class Ac4HiloDiscusionFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app

        self.stat_msgs_var = ctk.StringVar(value="—")
        self.stat_partic_var = ctk.StringVar(value="—")
        self.stat_tono_var = ctk.StringVar(value="—")
        self.stat_clusters_var = ctk.StringVar(value="3")
        self.estado_var = ctk.StringVar(value="Sin analizar")

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
        self._build_stats_card(left).grid(row=1, column=0, sticky="ew")

        self._build_header_right(right).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_output_card(right).grid(row=1, column=0, sticky="nsew")

    def _build_control_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Hilo de discusion", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))
        ctk.CTkLabel(card, text=f"Demo: {len(HILO_IA_DEMO)} mensajes sobre IA",
                     font=FONT_META, text_color=THEME["text_2"]).grid(
            row=1, column=0, sticky="w", padx=CARD_PADDING, pady=(0, 8))

        ctk.CTkLabel(card, text="Numero de subtemas (clusters)", font=FONT_META,
                     text_color=THEME["text_2"]).grid(
            row=2, column=0, sticky="w", padx=CARD_PADDING)
        self.spin_clusters = ctk.CTkOptionMenu(
            card, values=["2", "3", "4", "5"],
            variable=self.stat_clusters_var,
            fg_color=THEME["bg_input"], button_color=THEME["accent"],
            button_hover_color=THEME["accent"], text_color=THEME["text_1"],
            dropdown_fg_color=THEME["bg_surface"], dropdown_text_color=THEME["text_1"],
            dropdown_hover_color=THEME["border"])
        self.spin_clusters.grid(row=3, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 10))

        self.btn_analizar = ctk.CTkButton(
            card, text="Analizar hilo", command=self._analizar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], height=36)
        self.btn_analizar.grid(row=4, column=0, sticky="ew", padx=CARD_PADDING, pady=(0, 6))

        ctk.CTkLabel(card, text="Estado", font=FONT_META, text_color=THEME["text_2"]).grid(
            row=5, column=0, sticky="w", padx=CARD_PADDING)
        ctk.CTkLabel(card, textvariable=self.estado_var, font=FONT_BODY,
                     text_color=THEME["text_1"], anchor="w").grid(
            row=6, column=0, sticky="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_stats_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        metricas = [
            ("Mensajes", self.stat_msgs_var),
            ("Participantes", self.stat_partic_var),
            ("Tono general", self.stat_tono_var),
        ]
        for i, (label, var) in enumerate(metricas):
            ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=i * 2, column=0, sticky="w", padx=CARD_PADDING,
                pady=(CARD_PADDING if i == 0 else 0, 0))
            ctk.CTkLabel(card, textvariable=var, font=FONT_BODY,
                         text_color=THEME["text_1"], anchor="w").grid(
                row=i * 2 + 1, column=0, sticky="w", padx=CARD_PADDING,
                pady=(0, 6 if i < len(metricas) - 1 else CARD_PADDING))
        return card

    def _build_header_right(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text="Analisis del hilo", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, CARD_PADDING))
        return card

    def _build_output_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(0, weight=1)
        self.output_box = ctk.CTkTextbox(
            card, fg_color=THEME["bg_input"], border_color=THEME["border"],
            border_width=1, text_color=THEME["text_1"], font=FONT_MONO,
            wrap="none", state="disabled")
        self.output_box.grid(row=0, column=0, sticky="nsew",
                              padx=CARD_PADDING, pady=CARD_PADDING)
        return card

    def _analizar(self) -> None:
        self.btn_analizar.configure(state="disabled")
        self.estado_var.set("Analizando…")
        self.root_app.set_estado("AC-4: analizando hilo…", "loading")
        self.root_app.show_progress()
        n_clusters = int(self.stat_clusters_var.get())
        threading.Thread(target=self._analizar_bg, args=(n_clusters,), daemon=True).start()

    def _analizar_bg(self, n_clusters: int) -> None:
        try:
            analizador = AnalizadorHiloDiscusion()
            analizador.cargar_hilo(HILO_IA_DEMO)
            resumen = analizador.resumen_hilo()
            evolucion = analizador.evolucion_sentimiento(ventana=3)
            subtemas = analizador.detectar_subtemas(n_clusters=n_clusters)
            self.after(0, lambda: self._on_ok(resumen, evolucion, subtemas))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_ok(self, resumen: dict, evolucion: list, subtemas: dict) -> None:
        self.stat_msgs_var.set(str(resumen["total_mensajes"]))
        self.stat_partic_var.set(str(resumen["participantes"]))
        self.stat_tono_var.set(f"{resumen['tono']} ({resumen['sentimiento_promedio']:+.3f})")

        lineas = [
            "  RESUMEN DEL HILO",
            f"  Mensajes          : {resumen['total_mensajes']}",
            f"  Participantes     : {resumen['participantes']}",
            f"  Tono              : {resumen['tono']} ({resumen['sentimiento_promedio']:+.3f})",
            f"  Positivos         : {resumen['positivos_pct']:.0f}%  |  "
            f"Negativos: {resumen['negativos_pct']:.0f}%",
            f"  Hashtags top      : {resumen['hashtags_top']}",
            f"  Mas activos       : {resumen['usuarios_activos']}",
            "",
            "  EVOLUCION DEL SENTIMIENTO (ventana=3)",
        ]
        for item in evolucion:
            barra = "+" * int(max(0, item["tendencia"] * 10))
            barra += "-" * int(max(0, -item["tendencia"] * 10))
            lineas.append(
                f"  Msg {item['posicion']:>2}: [{item['sentimiento_puntual']:+.2f}] "
                f"tend: {item['tendencia']:+.3f} |{barra}")

        lineas += ["", "  SUBTEMAS DETECTADOS"]
        for cid, info in subtemas.items():
            lineas.append(f"  Subtema {cid + 1} ({info['n_mensajes']} msgs): {info['keywords']}")

        self._set_output("\n".join(lineas))
        self.estado_var.set("Analisis completado")
        self.btn_analizar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(f"AC-4: {resumen['total_mensajes']} mensajes, "
                                  f"tono {resumen['tono']}", "ok")

    def _on_error(self, msg: str) -> None:
        self.estado_var.set("Error")
        self.btn_analizar.configure(state="normal")
        self.root_app.hide_progress()
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-4", msg)

    def _set_output(self, texto: str) -> None:
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", texto)
        self.output_box.configure(state="disabled")
