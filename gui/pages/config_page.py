import tkinter as tk
from tkinter import ttk

from gui.controls.z_Label import ZLabel
from gui.pages.page_object import PageObject


class ConfigPage(PageObject):
    """Configuration page with layered sensor selection controls."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        # Store the selected configuration values so they can be reused later.
        self.config_values = {
            "ink_type": None,
            "number_of_layers": None,
        }

        # Keep track of the dynamically created layer-specific controls.
        self.layer_sensor_vars = []
        self.layer_sensor_dropdowns = []

        # Create a simple form area inside the main content frame.
        self.form_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.form_frame.configure(borderwidth=1, relief="solid")

        # Dropdown for selecting the number of layers. This appears first.
        self.layers_label = ZLabel(self.form_frame, text="Number of layers")
        self.layers_label.pack(anchor="w", pady=(0, 5))

        self.layer_options = [str(value) for value in range(1, 6)]
        self.layers_var = tk.StringVar(value=self.layer_options[0])
        self.layers_dropdown = ttk.Combobox(
            self.form_frame,
            textvariable=self.layers_var,
            values=self.layer_options,
            state="readonly",
            width=20,
        )
        self.layers_dropdown.pack(anchor="w", pady=(0, 10))
        self.layers_dropdown.bind("<<ComboboxSelected>>", self._refresh_layer_inputs)

        # Create a separate frame to hold the dynamic layer-specific sensor selectors.
        self.layer_sensor_frame = ttk.Frame(self.form_frame)
        self.layer_sensor_frame.pack(fill="x", anchor="w")

        # Dropdown for selecting the ink type.
        self.ink_label = ZLabel(self.form_frame, text="Ink type")
        self.ink_label.pack(anchor="w", pady=(0, 10))

        self.ink_options = ["Ink A", "Ink B", "Ink C"]
        self.ink_var = tk.StringVar(value=self.ink_options[0])
        self.ink_dropdown = ttk.Combobox(
            self.form_frame,
            textvariable=self.ink_var,
            values=self.ink_options,
            state="readonly",
            width=20,
        )
        self.ink_dropdown.pack(anchor="w")
        self.ink_dropdown.bind("<<ComboboxSelected>>", self._save_config_values)

        # Build the initial set of layer-specific sensor selectors.
        self._refresh_layer_inputs()

    def _refresh_layer_inputs(self, event=None):
        """Clear and recreate the per-layer sensor dropdowns based on the selected layer count."""
        # Remove any old layer-specific widgets before rebuilding the form.
        for widget in self.layer_sensor_frame.winfo_children():
            widget.destroy()

        self.layer_sensor_vars.clear()
        self.layer_sensor_dropdowns.clear()

        # Default to one layer if the selection cannot be parsed.
        try:
            layer_count = int(self.layers_var.get())
        except ValueError:
            layer_count = 1

        self.config_values["number_of_layers"] = str(layer_count)

        self.sensor_options = ["Type A", "Type B", "Type C"]

        # Create one sensor selector for each selected layer.
        for layer_number in range(1, layer_count + 1):
            label = ZLabel(self.layer_sensor_frame, text=f"Layer {layer_number} sensor")
            label.pack(anchor="w", pady=(0, 5))

            sensor_var = tk.StringVar(value=self.sensor_options[0])
            sensor_dropdown = ttk.Combobox(
                self.layer_sensor_frame,
                textvariable=sensor_var,
                values=self.sensor_options,
                state="readonly",
                width=20,
            )
            sensor_dropdown.pack(anchor="w", pady=(0, 10))
            sensor_dropdown.bind("<<ComboboxSelected>>", self._save_config_values)

            self.layer_sensor_vars.append(sensor_var)
            self.layer_sensor_dropdowns.append(sensor_dropdown)

        # Save the current values after rebuilding the dynamic controls.
        self._save_config_values()

    def _save_config_values(self, event=None):
        """Store the current dropdown selections for later use."""
        self.config_values["ink_type"] = self.ink_var.get()
        self.config_values["number_of_layers"] = self.layers_var.get()

        # Save each layer-specific sensor selection under a dedicated key.
        for layer_index, sensor_var in enumerate(self.layer_sensor_vars, start=1):
            self.config_values[f"layer_{layer_index}_sensor"] = sensor_var.get()
