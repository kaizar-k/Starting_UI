import tkinter as tk
from tkinter import ttk

import pandas as pd

from backend.dropdown_backend import DropdownData
from gui.controls.dropdown_object import DropdownObject


class RemoveConfigSection(ttk.LabelFrame):
    """Section for selecting an existing configuration preset to remove."""

    def __init__(self, parent, category_options):
        super().__init__(parent, text="Remove", padding=12)
        self.category_options = category_options
        self.dropdown_widgets = {}
        self.dropdown_data = DropdownData()
        self.warning_var = tk.StringVar(value="")

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Remove an existing configuration preset here.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w", pady=(8, 0))

        configuration_dropdown = DropdownObject(
            controls_frame,
            "Configuration name",
            self._get_configuration_names(),
            default_value="No selection",
            width=30,
        )
        configuration_dropdown.pack(side="left", padx=(0, 12), anchor="n")
        self.dropdown_widgets["configuration_name"] = configuration_dropdown
        configuration_dropdown.dropdown.bind("<<ComboboxSelected>>", self._handle_configuration_name_selection)

        or_label = ttk.Label(controls_frame, text="OR", font=("TkDefaultFont", 15, "bold"))
        or_label.pack(side="left", padx=(18, 32), anchor="n")

        for category_name in self.category_options.keys():
            dropdown = DropdownObject(
                controls_frame,
                category_name,
                ["No selection"] + self._get_category_options(category_name),
                default_value="No selection",
                width=18 if category_name != "AC/DC" else 12,
            )
            dropdown.pack(side="left", padx=(0, 12), anchor="n")
            dropdown.dropdown.bind("<<ComboboxSelected>>", self._handle_manual_selection)
            self.dropdown_widgets[category_name] = dropdown

        self.warning_label = ttk.Label(self, textvariable=self.warning_var, foreground="red", wraplength=1000, justify="left")
        self.warning_label.pack(anchor="w", pady=(8, 0))

        remove_button = ttk.Button(self, text="Remove configuration", command=self._remove_configuration)
        remove_button.pack(anchor="e", pady=(8, 0))

    def _get_category_options(self, category_name):
        return list(self.category_options.get(category_name, []))

    def _get_configuration_names(self):
        return self.dropdown_data.get_configuration_names()

    def _handle_configuration_name_selection(self, event=None):
        selected_name = self.dropdown_widgets["configuration_name"].get()
        if not selected_name or selected_name == "No selection":
            self.warning_var.set("")
            return

        values = self.dropdown_data.get_configuration_values_by_name(selected_name)
        if not values:
            self.warning_var.set("Unable to remove configuration as it does not exist")
            return

        self.warning_var.set(f"You are removing configuration: {selected_name}")
        for category_name, dropdown in self.dropdown_widgets.items():
            if category_name == "configuration_name":
                continue

            option_value = values.get(category_name, "No selection")
            dropdown.set(option_value if option_value else "No selection")

    def _handle_manual_selection(self, event=None):
        selected_values = {}
        for category_name, dropdown in self.dropdown_widgets.items():
            if category_name == "configuration_name":
                continue
            value = dropdown.get()
            if value and value != "No selection":
                selected_values[category_name] = value

        if not selected_values:
            self.warning_var.set("")
            return

        matched_name = self.dropdown_data.find_configuration_name_for_values(selected_values)
        if matched_name is None:
            self.warning_var.set("Unable to remove configuration as it does not exist")
            self.dropdown_widgets["configuration_name"].set("No selection")
            return

        self.warning_var.set(f"You are removing configuration: {matched_name}")
        self.dropdown_widgets["configuration_name"].set(matched_name)

    def _remove_configuration(self):
        selected_name = self.dropdown_widgets["configuration_name"].get()
        if selected_name in {"", "No selection"}:
            selected_values = {}
            for category_name, dropdown in self.dropdown_widgets.items():
                if category_name == "configuration_name":
                    continue
                value = dropdown.get()
                if value and value != "No selection":
                    selected_values[category_name] = value

            if not selected_values:
                self.warning_var.set("Unable to remove configuration as it does not exist")
                return

            selected_name = self.dropdown_data.find_configuration_name_for_values(selected_values)
            if not selected_name:
                self.warning_var.set("Unable to remove configuration as it does not exist")
                return

        deleted = self.dropdown_data.delete_configuration_by_name(selected_name)
        if not deleted:
            self.warning_var.set("Unable to remove configuration as it does not exist")
            return

        self.warning_var.set("")
        self.refresh()

    def refresh(self):
        for category_name, dropdown in self.dropdown_widgets.items():
            if category_name == "configuration_name":
                dropdown.dropdown.configure(values=self._get_configuration_names())
            else:
                dropdown.dropdown.configure(values=["No selection"] + self._get_category_options(category_name))
            dropdown.set("No selection")
        self.warning_var.set("")
