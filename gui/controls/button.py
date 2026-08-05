import tkinter as tk
from gui.page_features.colour_scheme import *
from gui.page_features.font_definitions import *


class Button(tk.Button):
    def __init__(self, master, text):
        super().__init__(master)
        self.configure(
            text=text,
            fg=TEXT_COLOUR,
            bg=EMPHASIS,
            font=HEADER_FONT,
            highlightbackground=EMPHASIS,
            activebackground=HIGHLIGHT,
            activeforeground=TEXT_COLOUR,
            relief='flat',
            padx=6,
            pady=2,
            borderwidth=0,
        )
