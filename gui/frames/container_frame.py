import tkinter as tk
from tkinter import ttk

# This will be the parent class for all the pages

class ContainerFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.configure(highlightbackground="black", highlightthickness=1) # adds a 1px black border around the frame for ease fo layout
