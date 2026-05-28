"""AC-6: Chatbot con memoria de contexto."""
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.chatbot_contextual import ChatbotContextual
from src.motor_busqueda import MotorBusqueda
from src.ui_theme import CARD_PADDING, CARD_RADIUS, FONT_BODY, FONT_H2, FONT_META, FONT_MONO, THEME

_NOTICIAS_DEMO = [
    {"titulo": "Avances en inteligencia artificial generativa",
     "cuerpo": "La inteligencia artificial y el aprendizaje automatico impulsan nuevas aplicaciones de software.",
     "categoria_predicha": "tecnologia", "sentimiento": {"etiqueta": "positivo"}},
    {"titulo": "Mercados financieros muestran volatilidad",
     "cuerpo": "La inflacion y las tasas de interes presionan al mercado de valores y a los inversionistas.",
     "categoria_predicha": "economia", "sentimiento": {"etiqueta": "negativo"}},
    {"titulo": "Descubrimiento cientifico sobre cambio climatico",
     "cuerpo": "Investigadores publican datos sobre emisiones de carbono y calentamiento global.",
     "categoria_predicha": "ciencia", "sentimiento": {"etiqueta": "negativo"}},
    {"titulo": "Python mejora herramientas de programacion",
     "cuerpo": "La nueva version de Python ayuda al desarrollo de software e inteligencia artificial.",
     "categoria_predicha": "tecnologia", "sentimiento": {"etiqueta": "positivo"}},
    {"titulo": "Gobierno publica datos abiertos",
     "cuerpo": "El gobierno libera datos abiertos para fortalecer transparencia y politicas publicas.",
     "categoria_predicha": "politica", "sentimiento": {"etiqueta": "positivo"}},
]


class Ac6ChatbotFrame(ctk.CTkFrame):
    def __init__(self, master, root_app) -> None:
        super().__init__(master, fg_color=THEME["bg_base"], corner_radius=0)
        self.root_app = root_app
        self.chatbot: ChatbotContextual | None = None

        self.stat_interacciones_var = ctk.StringVar(value="0")
        self.stat_contexto_var = ctk.StringVar(value="No")
        self.stat_temas_var = ctk.StringVar(value="—")
        self._build()
        self._inicializar_chatbot()

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=THEME["bg_surface"], corner_radius=CARD_RADIUS)
        f.grid_columnconfigure(0, weight=1)
        return f

    def _build(self) -> None:
        self.grid_columnconfigure(0, minsize=260, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 8), pady=12)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color=THEME["bg_base"], corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 18), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=0)

        self._build_stats_card(left).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._build_input_card(left).grid(row=1, column=0, sticky="ew")
        self._build_chat_card(right).grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self._build_entry_card(right).grid(row=1, column=0, sticky="ew")

    def _build_stats_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        ctk.CTkLabel(card, text="Sesion", font=FONT_H2, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        metricas = [
            ("Interacciones", self.stat_interacciones_var),
            ("Tiene contexto", self.stat_contexto_var),
            ("Temas de interes", self.stat_temas_var),
        ]
        for i, (label, var) in enumerate(metricas):
            ctk.CTkLabel(card, text=label, font=FONT_META, text_color=THEME["text_2"]).grid(
                row=i * 2 + 1, column=0, sticky="w", padx=CARD_PADDING)
            ctk.CTkLabel(card, textvariable=var, font=FONT_BODY,
                         text_color=THEME["text_1"], anchor="w").grid(
                row=i * 2 + 2, column=0, sticky="w", padx=CARD_PADDING,
                pady=(0, 4 if i < len(metricas) - 1 else CARD_PADDING))
        return card

    def _build_input_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        self.btn_guardar = ctk.CTkButton(
            card, text="Guardar sesion JSON",
            command=self._guardar_sesion,
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"])
        self.btn_guardar.grid(row=0, column=0, sticky="ew", padx=CARD_PADDING,
                               pady=(CARD_PADDING, 4))
        self.btn_limpiar = ctk.CTkButton(
            card, text="Nueva sesion",
            command=self._nueva_sesion,
            fg_color=THEME["bg_input"], hover_color=THEME["border"],
            border_width=1, border_color=THEME["border"],
            text_color=THEME["text_1"])
        self.btn_limpiar.grid(row=1, column=0, sticky="ew", padx=CARD_PADDING,
                               pady=(0, CARD_PADDING))
        return card

    def _build_chat_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(card, text="Conversacion", font=FONT_H2,
                     text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=CARD_PADDING, pady=(CARD_PADDING, 6))
        self.chat_box = ctk.CTkTextbox(
            card, fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1,
            text_color=THEME["text_1"], font=FONT_BODY, wrap="word", state="disabled")
        self.chat_box.grid(row=1, column=0, sticky="nsew",
                            padx=CARD_PADDING, pady=(0, CARD_PADDING))
        return card

    def _build_entry_card(self, master) -> ctk.CTkFrame:
        card = self._card(master)
        card.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(
            card, placeholder_text="Escribe tu pregunta aqui…",
            fg_color=THEME["bg_input"], border_color=THEME["border"], border_width=1,
            text_color=THEME["text_1"])
        self.entry.grid(row=0, column=0, sticky="ew", padx=(CARD_PADDING, 8),
                         pady=CARD_PADDING)
        self.entry.bind("<Return>", lambda _: self._enviar())
        self.btn_enviar = ctk.CTkButton(
            card, text="Enviar", command=self._enviar,
            fg_color=THEME["accent"], hover_color=THEME["accent"],
            text_color=THEME["text_1"], width=80)
        self.btn_enviar.grid(row=0, column=1, padx=(0, CARD_PADDING), pady=CARD_PADDING)
        return card

    def _inicializar_chatbot(self) -> None:
        threading.Thread(target=self._init_bg, daemon=True).start()

    def _init_bg(self) -> None:
        try:
            noticias = self.root_app.noticias or _NOTICIAS_DEMO
            motor = MotorBusqueda()
            motor.indexar(noticias)
            cb = ChatbotContextual(noticias, motor)
            self.after(0, lambda: self._on_init_ok(cb))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_init_ok(self, cb: ChatbotContextual) -> None:
        self.chatbot = cb
        self._append_chat("Sistema", "Chatbot listo. Puedes hacer preguntas sobre las noticias cargadas.")
        self.root_app.set_estado("AC-6: chatbot iniciado", "ok")

    def _enviar(self) -> None:
        if not self.chatbot:
            return
        pregunta = self.entry.get().strip()
        if not pregunta:
            return
        self.entry.delete(0, "end")
        self._append_chat("Tu", pregunta)
        self.btn_enviar.configure(state="disabled")
        threading.Thread(target=self._responder_bg, args=(pregunta,), daemon=True).start()

    def _responder_bg(self, pregunta: str) -> None:
        try:
            respuesta, tipo, confianza = self.chatbot.responder(pregunta)
            stats = self.chatbot.estadisticas_sesion()
            self.after(0, lambda: self._on_respuesta(respuesta, tipo, confianza, stats))
        except Exception as exc:
            self.after(0, lambda e=exc: self._on_error(str(e)))

    def _on_respuesta(self, respuesta: str, tipo: str, confianza: float, stats: dict) -> None:
        self._append_chat(f"Bot [{tipo}][{confianza:.2f}]", respuesta)
        self.stat_interacciones_var.set(str(stats["interacciones"]))
        self.stat_contexto_var.set("Si" if stats.get("tiene_contexto") else "No")
        self.stat_temas_var.set(", ".join(stats.get("temas_interes", [])) or "—")
        self.btn_enviar.configure(state="normal")

    def _guardar_sesion(self) -> None:
        if not self.chatbot:
            return
        try:
            ruta = self.chatbot.guardar_sesion("data/sesion_chatbot_ac6.json")
            self.root_app.set_estado(f"AC-6: sesion guardada en {ruta}", "ok")
        except Exception as exc:
            messagebox.showerror("AC-6", str(exc))

    def _nueva_sesion(self) -> None:
        self.chatbot = None
        self.stat_interacciones_var.set("0")
        self.stat_contexto_var.set("No")
        self.stat_temas_var.set("—")
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self._inicializar_chatbot()

    def _on_error(self, msg: str) -> None:
        self.root_app.set_estado(msg, "error")
        messagebox.showerror("AC-6", msg)

    def _append_chat(self, quien: str, texto: str) -> None:
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{quien}:\n  {texto}\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")
