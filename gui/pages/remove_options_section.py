import tkinter as tk
from tkinter import ttk

from gui.controls.dropdown_object import DropdownObject


class RemoveOptionsSection(ttk.LabelFrame):
    """Section for removing existing values from the dropdown option lists."""

    def __init__(self, parent, category_options, refresh_callback=None):
        super().__init__(parent, text="Remove options", padding=12)
        self.category_options = category_options
        self.refresh_callback = refresh_callback
        self.dropdown_widgets = {}

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Choose an item from each category to remove it from the available dropdown options.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w")

        for category_name in ["Sensor type", "Substrate", "Coating", "Graphene"]:
            dropdown = DropdownObject(
                controls_frame,
                category_name,
                self._get_remove_options(category_name),
                default_value="No selection",
                width=18,
            )
            dropdown.pack(side="left", padx=(0, 12), anchor="n")
            self.dropdown_widgets[category_name] = dropdown

        save_button = ttk.Button(self, text="Save choices", command=self._save_removed_options)
        save_button.pack(anchor="e", pady=(8, 0))

    def _get_remove_options(self, category_name):
        options = list(self.category_options.get(category_name, []))
        return ["No selection"] + options

    def _save_removed_options(self):
        for category_name, dropdown in self.dropdown_widgets.items():
            selected_value = dropdown.get()
            if not selected_value or selected_value == "No selection":
                continue

            options = self.category_options.get(category_name, [])
            if selected_value in options:
                options.remove(selected_value)

        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        for category_name, dropdown in self.dropdown_widgets.items():
            dropdown.dropdown.configure(values=self._get_remove_options(category_name))
            dropdown.set("No selection")
