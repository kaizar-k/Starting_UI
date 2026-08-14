import tkinter as tk
from tkinter import ttk

from backend.dropdown_backend import DropdownData
from gui.controls.dropdown_object import DropdownObject


class RemoveOptionsSection(ttk.LabelFrame):
    """Section for removing existing values from the dropdown option lists."""

    def __init__(self, parent, category_options, refresh_callback=None):
        super().__init__(parent, text="Remove options", padding=12)
        self.category_options = category_options
        self.refresh_callback = refresh_callback
        self.dropdown_widgets = {}
        self.dropdown_data = DropdownData()
        self.used_options_by_category = self.dropdown_data.get_used_options_by_category()

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Choose an item from each category to remove it from the available dropdown options.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w")

        for category_name in self.category_options.keys():
            dropdown = DropdownObject(
                controls_frame,
                category_name,
                self._get_remove_options(category_name),
                default_value="No selection",
                width=18,
            )
            dropdown.pack(side="left", padx=(0, 12), anchor="n")
            self.dropdown_widgets[category_name] = dropdown

        self.warning_label = ttk.Label(
            self,
            text="",
            foreground="red",
            wraplength=1000,
            justify="left",
        )
        self.warning_label.pack(anchor="w", pady=(8, 0))

        save_button = ttk.Button(self, text="Save choices", command=self._save_removed_options)
        save_button.pack(anchor="e", pady=(8, 0))

    def _get_remove_options(self, category_name):
        options = list(self.category_options.get(category_name, []))
        return ["No selection"] + options

    def _save_removed_options(self):
        self.warning_label.config(text="")

        for category_name, dropdown in self.dropdown_widgets.items():
            selected_value = dropdown.get()
            if not selected_value or selected_value == "No selection":
                continue

            used_values = self.used_options_by_category.get(category_name, [])
            if selected_value in used_values:
                self.warning_label.config(
                    text=(
                        f"Warning: '{selected_value}' is currently used in one or more configuration presets "
                        f"for {category_name}. Remove or update those presets first."
                    )
                )
                return

            options = self.category_options.get(category_name, [])
            if selected_value in options:
                options.remove(selected_value)

        # Save the updated option lists back to disk and reload them immediately.
        self.dropdown_data.save_options_by_category(self.category_options)
        self.category_options.update(self.dropdown_data.get_options_by_category())
        self.used_options_by_category = self.dropdown_data.get_used_options_by_category()

        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.used_options_by_category = self.dropdown_data.get_used_options_by_category()
        for category_name, dropdown in self.dropdown_widgets.items():
            dropdown.dropdown.configure(values=self._get_remove_options(category_name))
            dropdown.set("No selection")
            self.warning_label.config(text="")
