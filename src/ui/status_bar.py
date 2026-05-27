from __future__ import annotations

import customtkinter as ctk

from src.ui_theme import FONT_META, STATUS_HEIGHT, THEME


class StatusBarFrame(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, height=STATUS_HEIGHT, fg_color=THEME["bg_surface"], corner_radius=0)
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        self.indicator = ctk.CTkLabel(self, text="●", font=FONT_META, text_color=THEME["success"])
        self.indicator.grid(row=0, column=0, padx=(14, 8), sticky="w")

        self.message = ctk.CTkLabel(self, text="Listo.", font=FONT_META, text_color=THEME["text_1"])
        self.message.grid(row=0, column=1, sticky="w")

        self.total = ctk.CTkLabel(self, text="Noticias: 0", font=FONT_META, text_color=THEME["text_2"])
        self.total.grid(row=0, column=2, padx=14, sticky="e")

    def set_estado(self, mensaje: str, nivel: str = "ok", total_noticias: int | None = None) -> None:
        color = {
            "ok": THEME["success"],
            "loading": THEME["accent"],
            "error": THEME["error"],
            "warning": THEME["warning"],
        }.get(nivel, THEME["success"])
        self.indicator.configure(text_color=color)
        self.message.configure(text=mensaje)
        if total_noticias is not None:
            self.total.configure(text=f"Noticias: {total_noticias}")
