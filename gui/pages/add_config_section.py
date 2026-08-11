import tkinter as tk
from tkinter import ttk

from gui.controls.dropdown_object import DropdownObject


class AddConfigSection(ttk.LabelFrame):
    """Section for selecting the values used in the Add configuration form."""

    def __init__(self, parent, category_options):
        super().__init__(parent, text="Add", padding=12)
        self.category_options = category_options
        self.dropdown_widgets = {}

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Create a new configuration preset here.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w", pady=(8, 0))

        for category_name in self.category_options.keys():
            options = self._get_category_options(category_name)
            dropdown_options = ["No selection"] + options
            dropdown = DropdownObject(
                controls_frame,
                category_name,
                dropdown_options,
                default_value="No selection",
                width=18 if category_name != "AC/DC" else 12,
            )
            dropdown.pack(side="left", padx=(0, 12), anchor="n")
            self.dropdown_widgets[category_name] = dropdown

    def _get_category_options(self, category_name):
        return list(self.category_options.get(category_name, []))

    def refresh(self):
        for category_name, dropdown in self.dropdown_widgets.items():
            options = self._get_category_options(category_name)
            dropdown_options = ["No selection"] + options
            dropdown.dropdown.configure(values=dropdown_options)
            dropdown.set("No selection")
