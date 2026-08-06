import tkinter as tk
from tkinter import ttk

from gui.controls.checkbutton import Checkbutton
from gui.pages.pop_up_banner import PopUpObject


class Options1Page(PopUpObject):
    """Popup page for the second main page."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        # Keep track of the BooleanVars for each layer checkbox.
        self.layer_vars = []
        self.options_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.options_frame.pack(fill="both", expand=True, anchor="w")

        # The first page in the app is the config page, which holds the shared state.
        self.config_page = self.master.pages[0]
        self._refresh_layer_checkboxes()

    def refresh_from_config(self):
        # Rebuild the checkbox list when the config page changes the layer count.
        self._refresh_layer_checkboxes()

    def _on_config_change(self, event=None):
        self._refresh_layer_checkboxes()

    def _refresh_layer_checkboxes(self):
        # Remove any old checkboxes before rebuilding them for the new layer count.
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        self.layer_vars.clear()

        layer_count = int(self.config_page.config_values["number_of_layers"])
        selected_layers = self.config_page.config_values.get("options_1_selected_layers", [])

        # Create one checkbox for each layer and restore any previously selected ones.
        for layer_number in range(1, layer_count + 1):
            var = tk.BooleanVar(value=layer_number in selected_layers)
            self.layer_vars.append(var)
            # Watch for checkbox changes so the selection can be saved immediately.
            var.trace_add("write", lambda *args, layer_num=layer_number: self._save_selected_layers())

            checkbox = Checkbutton(
                self.options_frame,
                text=f"Layer {layer_number}",
                variable=var,
            )
            checkbox.pack(anchor="w", pady=2)

    def _save_selected_layers(self):
        # Collect the currently checked layer numbers into a list.
        selected_layers = [
            layer_number
            for layer_number, var in enumerate(self.layer_vars, start=1)
            if var.get()
        ]

        # Save the selection in the shared config state.
        self.config_page.config_values["options_1_selected_layers"] = selected_layers

        # Tell any page that displays these selections to refresh itself.
        for page in self.master.pages:
            if hasattr(page, "refresh_selected_layers_display"):
                page.refresh_selected_layers_display()
