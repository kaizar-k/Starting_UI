# import stuff needed from other files
import tkinter as tk
from gui.controls.z_Label import ZLabel
from gui.frames.container_frame import ContainerFrame
from gui.colour_scheme import TEXT_COLOUR
from gui.colour_scheme import BACKGROUND

# This class is simply to contain other frames and widgets for layout simplicity
class LabelFrame(ContainerFrame):
    def __init__(self, master, label_text: str):
        super().__init__(master)
        self.master = master
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.label = ZLabel(self, text=label_text)
        self.label.pack(side='top', fill='both', expand=True, anchor='w')

        self.content = ContainerFrame(self)
        self.content.configure(highlightbackground=TEXT_COLOUR, highlightthickness=1, padx=2, pady=2)
        self.content.pack(side="top", fill="both", expand=True)