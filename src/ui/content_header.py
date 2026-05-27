from __future__ import annotations

import customtkinter as ctk

from src.ui_theme import FONT_H1, FONT_META, HEADER_HEIGHT, THEME


class ContentHeaderFrame(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, height=HEADER_HEIGHT, fg_color=THEME["bg_base"], corner_radius=0)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(self, text="", font=FONT_H1, text_color=THEME["text_1"])
        self.title.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 0))

        self.description = ctk.CTkLabel(self, text="", font=FONT_META, text_color=THEME["text_2"])
        self.description.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 8))

        self.progress = ctk.CTkProgressBar(
            self,
            height=6,
            progress_color=THEME["accent"],
            fg_color=THEME["border"],
        )
        self.progress.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        self.progress.set(0)
        self.progress.grid_remove()

    def set_content(self, titulo: str, descripcion: str) -> None:
        self.title.configure(text=titulo)
        self.description.configure(text=descripcion)

    def show_progress(self) -> None:
        self.progress.grid()
        self.progress.configure(mode="indeterminate")
        self.progress.start()

    def hide_progress(self) -> None:
        self.progress.stop()
        self.progress.set(0)
        self.progress.grid_remove()
