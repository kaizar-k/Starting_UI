import tkinter as tk
from tkinter import ttk

from gui.controls.checkbutton import Checkbutton
from gui.pages.objects.pop_up_banner import PopUpObject


class Options2Page(PopUpObject):
    """Popup page controlling optional 3D visualisation display."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        self.config_page = self.master.pages[0]
        self.options_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.options_frame.pack(fill="both", expand=True, anchor="w")

        self.show_3d_var = tk.BooleanVar(value=self.config_page.config_values.get("show_3d_plot", False))
        self.show_3d_var.trace_add("write", self._save_show_3d_plot)

        self.show_3d_checkbox = Checkbutton(
            self.options_frame,
            text="Show 3D plot",
            variable=self.show_3d_var,
        )
        self.show_3d_checkbox.pack(anchor="w", pady=6)

    def _save_show_3d_plot(self, *args):
        """Persist the 3D visibility selection and refresh dependent pages."""
        self.config_page.config_values["show_3d_plot"] = bool(self.show_3d_var.get())

        # Only notify other pages; refreshing the config page itself would rebuild
        # its dropdowns from the CSV and wipe the current layer selections.
        for page in self.master.pages:
            if page is not self.config_page and hasattr(page, "refresh_from_config"):
                page.refresh_from_config()

    def refresh_from_config(self):
        """Keep the checkbox in sync when shared config values change."""
        self.show_3d_var.set(bool(self.config_page.config_values.get("show_3d_plot", False)))
