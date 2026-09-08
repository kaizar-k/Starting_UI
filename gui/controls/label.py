import tkinter as tk
from gui.page_features.colour_scheme import *
from gui.page_features.font_definitions import get_header_font


class Label(tk.Label):
    def __init__(self, master, text):
        super().__init__(master)
        self.configure(text=text, fg=TEXT_COLOUR, bg=BACKGROUND, font=get_header_font(), justify="left")