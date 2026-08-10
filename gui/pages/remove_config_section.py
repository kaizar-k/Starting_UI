import tkinter as tk
from tkinter import ttk

from gui.controls.dropdown_object import DropdownObject


class RemoveConfigSection(ttk.LabelFrame):
    """Section for selecting an existing configuration preset to remove."""

    def __init__(self, parent, category_options):
        super().__init__(parent, text="Remove", padding=12)
        self.category_options = category_options
        self.dropdown_widgets = {}

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Remove an existing configuration preset here.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w", pady=(8, 0))

        for category_name in ["Sensor type", "AC/DC", "Substrate", "Graphene", "Coating"]:
            dropdown = DropdownObject(
                controls_frame,
                category_name,
                ["No selection"] + self._get_category_options(category_name),
                default_value="No selection",
                width=18 if category_name != "AC/DC" else 12,
            )
            dropdown.pack(side="left", padx=(0, 12), anchor="n")
            self.dropdown_widgets[category_name] = dropdown

    def _get_category_options(self, category_name):
        return list(self.category_options.get(category_name, []))

    def refresh(self):
        for category_name, dropdown in self.dropdown_widgets.items():
            dropdown.dropdown.configure(values=["No selection"] + self._get_category_options(category_name))
            dropdown.set("No selection")
