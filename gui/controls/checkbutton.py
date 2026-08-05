import tkinter as tk
from tkinter import ttk


class Checkbutton(ttk.Checkbutton):
    def __init__(self, master, text, variable=None, command=None):
        self._variable = variable if variable is not None else tk.BooleanVar(value=False)
        super().__init__(master, text=text, variable=self._variable, command=command)
        self.configure(style='TCheckbutton')
