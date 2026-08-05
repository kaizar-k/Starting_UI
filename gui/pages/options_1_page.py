import tkinter as tk
from tkinter import ttk

from gui.controls.checkbutton import Checkbutton
from gui.pages.pop_up_banner import PopUpObject


class Options1Page(PopUpObject):
    """Popup page for the second main page."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        self.layer_vars = []
        self.options_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.options_frame.pack(fill="both", expand=True, anchor="w")

        self.config_page = self.master.pages[0]
        self._refresh_layer_checkboxes()

    def refresh_from_config(self):
        self._refresh_layer_checkboxes()
        self._schedule_scroll_region_update()

    def _on_config_change(self, event=None):
        self._refresh_layer_checkboxes()

    def _refresh_layer_checkboxes(self):
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        self.layer_vars.clear()

        layer_count = int(self.config_page.config_values["number_of_layers"])

        for layer_number in range(1, layer_count + 1):
            var = tk.BooleanVar(value=False)
            self.layer_vars.append(var)

            checkbox = Checkbutton(
                self.options_frame,
                text=f"Layer {layer_number}",
                variable=var,
            )
            checkbox.pack(anchor="w", pady=2)
