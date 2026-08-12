import tkinter as tk
from tkinter import ttk

import pandas as pd

from backend.dropdown_data import DropdownData
from gui.controls.dropdown_object import DropdownObject


class AddConfigSection(ttk.LabelFrame):
    """Section for selecting the values used in the Add configuration form."""

    def __init__(self, parent, category_options, refresh_callback=None):
        super().__init__(parent, text="Add", padding=12)
        self.category_options = category_options
        self.dropdown_widgets = {}
        self.dropdown_data = DropdownData()
        self.refresh_callback = refresh_callback

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Create a new configuration preset here.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w", pady=(8, 0))

        name_frame = ttk.Frame(self)
        name_frame.pack(fill="x", anchor="w", pady=(0, 8))
        ttk.Label(name_frame, text="Configuration name:").pack(anchor="w")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=30)
        self.name_entry.pack(anchor="w", pady=(4, 0))

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

        self.message_label = ttk.Label(self, text="", foreground="red", wraplength=1000, justify="left")
        self.message_label.pack(anchor="w", pady=(8, 0))

        save_button = ttk.Button(self, text="Save configuration", command=self._save_configuration)
        save_button.pack(anchor="e", pady=(8, 0))

    def _get_category_options(self, category_name):
        return list(self.category_options.get(category_name, []))

    def _save_configuration(self):
        configuration_name = self.name_var.get().strip()
        selected_values = {category_name: dropdown.get() for category_name, dropdown in self.dropdown_widgets.items()}

        if not configuration_name or any(value in {"", "No selection"} for value in selected_values.values()):
            self.message_label.config(text="Please fill in all fields, including the configuration name.")
            return

        self.message_label.config(text="")

        matching_name = self.dropdown_data.find_configuration_name_for_values(
            {category_name: value for category_name, value in selected_values.items() if value not in {"", "No selection"}}
        )
        if matching_name is not None:
            self.message_label.config(text=f"This configuration already exists as '{matching_name}'.")
            return

        config_row = {"configuration_name": configuration_name}
        for category_name, value in selected_values.items():
            config_row[category_name] = value

        config_row["calibration_regimes"] = ""

        if self.dropdown_data.configurations_csv_path.exists():
            existing_df = pd.read_csv(self.dropdown_data.configurations_csv_path)
        else:
            existing_df = pd.DataFrame()

        updated_df = pd.concat([existing_df, pd.DataFrame([config_row])], ignore_index=True)
        updated_df.to_csv(self.dropdown_data.configurations_csv_path, index=False)

        if self.refresh_callback is not None:
            self.refresh_callback()

        self.name_var.set("")
        for category_name, dropdown in self.dropdown_widgets.items():
            dropdown.set("No selection")

    def refresh(self):
        for category_name, dropdown in self.dropdown_widgets.items():
            options = self._get_category_options(category_name)
            dropdown_options = ["No selection"] + options
            dropdown.dropdown.configure(values=dropdown_options)
            dropdown.set("No selection")
        self.message_label.config(text="")
