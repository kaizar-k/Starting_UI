import tkinter as tk
from tkinter import ttk

from gui.controls.z_Label import ZLabel
from gui.pages.page_object import PageObject


class ConfigPage(PageObject):
    """Configuration page with simple dropdown selectors for user settings."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        # Store the selected configuration values so they can be reused later.
        self.config_values = {
            "sensor_type": None,
            "ink_type": None,
        }

        # Remove the default side panels from the base page layout so the form has room to show clearly.
        if hasattr(self, "figure_area_frame"):
            self.figure_area_frame.pack_forget()
        if hasattr(self, "parameters_button_frame"):
            self.parameters_button_frame.pack_forget()

        # Create a simple form area inside the main content frame.
        self.form_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.form_frame.configure(borderwidth=1, relief="solid")

        # Dropdown for selecting the sensor type.
        self.sensor_label = ZLabel(self.form_frame, text="Sensor type")
        self.sensor_label.pack(anchor="w", pady=(0, 5))

        self.sensor_options = ["Type A", "Type B", "Type C"]
        self.sensor_var = tk.StringVar(value=self.sensor_options[0])
        self.sensor_dropdown = ttk.Combobox(
            self.form_frame,
            textvariable=self.sensor_var,
            values=self.sensor_options,
            state="readonly",
            width=20,
        )
        self.sensor_dropdown.pack(anchor="w", pady=(0, 15))
        self.sensor_dropdown.bind("<<ComboboxSelected>>", self._save_config_values)

        # Dropdown for selecting the ink type.
        self.ink_label = ZLabel(self.form_frame, text="Ink type")
        self.ink_label.pack(anchor="w", pady=(0, 5))

        self.ink_options = ["Ink A", "Ink B", "Ink C"]
        self.ink_var = tk.StringVar(value=self.ink_options[0])
        self.ink_dropdown = ttk.Combobox(
            self.form_frame,
            textvariable=self.ink_var,
            values=self.ink_options,
            state="readonly",
            width=20,
        )
        #places dropdown in the form frame and binds the selection event to save the configuration values
        self.ink_dropdown.pack(anchor="w")
        self.ink_dropdown.bind("<<ComboboxSelected>>", self._save_config_values)

        # Save the initial default values as soon as the page is created.
        self._save_config_values()

    def _save_config_values(self, event=None):
        """Store the current dropdown selections for later use."""
        self.config_values["sensor_type"] = self.sensor_var.get()
        self.config_values["ink_type"] = self.ink_var.get()
