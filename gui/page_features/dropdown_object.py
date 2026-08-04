import tkinter as tk
from tkinter import ttk

from gui.controls.z_Label import ZLabel


class DropdownObject(ttk.Frame):
    """Reusable labelled dropdown widget used throughout the configuration form."""

    def __init__(self, parent, label_text, options, default_value=None, width=20, command=None):
        super().__init__(parent)

        self.label = ZLabel(self, text=label_text)
        self.label.pack(anchor="w", pady=(0, 5))

        selected_value = default_value if default_value is not None else options[0]
        self.var = tk.StringVar(value=selected_value)
        self.dropdown = ttk.Combobox(
            self,
            textvariable=self.var,
            values=options,
            state="readonly",
            width=width,
        )
        self.dropdown.pack(anchor="w")

        if command is not None:
            self.dropdown.bind("<<ComboboxSelected>>", command)

    def get(self):
        """Return the currently selected value."""
        return self.var.get()

    def set(self, value):
        """Set the selected value programmatically."""
        self.var.set(value)
