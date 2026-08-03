import tkinter as tk
from gui.colour_scheme import BACKGROUND, TEXT_COLOUR


# This will be the parent class for all custom frame objects
class ContainerFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.configure(bg=BACKGROUND) # adds a 1px black border around the frame for ease fo layout
#, highlightbackground=TEXT_COLOUR, highlightthickness=1