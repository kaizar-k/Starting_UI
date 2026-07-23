import tkinter as tk
from gui.colour_scheme import *
from gui.font_definitions import *

class ZButton(tk.Button):
    def __init__(self, master, text):
        super().__init__(master)
        self.configure(text=text, fg=TEXT_COLOUR, bg=EMPHASIS, font=HEADER_FONT, highlightbackground=EMPHASIS, activebackground=BACKGROUND)