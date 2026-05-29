from __future__ import annotations

import customtkinter as ctk

from src.ui_theme import FONT_BODY, FONT_H1, FONT_META, SECTIONS, SIDEBAR_WIDTH, THEME


class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, on_select) -> None:
        super().__init__(master, width=SIDEBAR_WIDTH, fg_color=THEME["bg_sidebar"], corner_radius=0)
        self.on_select = on_select
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="SIMANW", font=FONT_H1, text_color=THEME["text_1"]).grid(
            row=0, column=0, sticky="w", padx=14, pady=(20, 2)
        )
        ctk.CTkLabel(
            self,
            text="Monitor de Noticias Web",
            font=FONT_META,
            text_color=THEME["text_2"],
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 22))

        for idx, (section_id, label, enabled) in enumerate(SECTIONS, start=2):
            button = ctk.CTkButton(
                self,
                text=label,
                font=FONT_BODY,
                anchor="w",
                fg_color=THEME["bg_input"] if enabled else THEME["bg_sidebar"],
                hover_color=THEME["border"] if enabled else THEME["bg_sidebar"],
                text_color=THEME["text_1"] if enabled else THEME["text_2"],
                border_width=1,
                border_color=THEME["border"] if enabled else THEME["bg_sidebar"],
                state="normal" if enabled else "disabled",
                command=lambda sid=section_id: self.on_select(sid),
            )
            button.grid(row=idx, column=0, sticky="ew", padx=10, pady=4)
            if enabled:
                self._buttons[section_id] = button

    def set_active(self, section_id: str) -> None:
        for sid, btn in self._buttons.items():
            if sid == section_id:
                btn.configure(fg_color=THEME["accent"], hover_color=THEME["accent"])
            else:
                btn.configure(fg_color=THEME["bg_input"], hover_color=THEME["border"])
