import tkinter as tk
from tkinter import ttk

from gui.pages.objects.page_object import PageObject


class TwoDVisualisationPage(PageObject):
    """Minimal placeholder page for the 2D force visualisation view."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        # Store the text shown on this page for the selected layers.
        self.selected_layers_var = tk.StringVar(value="No layers selected.")
        self.selected_layers_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.selected_layers_frame.pack(fill="both", expand=True, anchor="w")

        ttk.Label(
            self.selected_layers_frame,
            text="Selected layers:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            self.selected_layers_frame,
            textvariable=self.selected_layers_var,
            justify="left",
            wraplength=800,
        ).pack(anchor="w")

        # Show the currently selected layers as soon as the page is created.
        self.refresh_selected_layers_display()

    def refresh_from_config(self):
        """Refresh the 2D page when the config object changes."""
        self.refresh_selected_layers_display()

    def refresh_selected_layers_display(self):
        # Read the latest selected layer list from the shared config page.
        selected_layers = self.master.pages[0].config_values.get("options_1_selected_layers", [])

        if selected_layers:
            # Convert the selected layer numbers into display names.
            layer_names = [f"Layer {layer_number}" for layer_number in selected_layers]
            self.selected_layers_var.set("\n".join(layer_names))
        else:
            self.selected_layers_var.set("No layers selected.")
