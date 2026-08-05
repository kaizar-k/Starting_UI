import tkinter as tk
from tkinter import ttk

from gui.controls.dropdown_object import DropdownObject
from gui.pages.page_object import PageObject


class ConfigPage(PageObject):
    """Configuration page with dynamically generated per-layer feature controls."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        # Store the selected configuration values so they can be reused later.
        self.config_values = {
            "number_of_layers": "1",
            "layer_features": {},
            "layer_description": [],
        }

        # Define the per-layer features that should be editable for each layer.
        # Add new entries with placement="secondary" if you want them to appear in the
        # side column for extra layer descriptions.
        self.layer_feature_definitions = [
            ("sensor", "Sensor", ["Type A", "Type B", "Type C"], "primary"),
            ("ink", "Ink", ["Ink A", "Ink B", "Ink C"], "primary"),
        ]

        # Keep track of the dynamically created dropdowns for each layer and feature.
        self.layer_feature_dropdowns = {}

        # Other pages can register here to be notified when the layer configuration changes.
        self.layer_change_observers = []

        # Create a simple form area inside the main content frame.
        self.form_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.form_frame.configure(borderwidth=1, relief="solid")

        # Number of layers dropdown first.
        self.layers_dropdown = DropdownObject(
            self.form_frame,
            "Number of layers",
            [str(value) for value in range(1, 9)],
            default_value="1",
            command=self._refresh_layer_inputs,
        )
        self.layers_dropdown.pack(anchor="w", pady=(0, 10))

        # Create a separate frame to hold the dynamic layer-specific controls.
        self.layer_feature_frame = ttk.Frame(self.form_frame)
        self.layer_feature_frame.pack(fill="x", anchor="w")

        # Summary label for the generated layer descriptions.
        self.summary_var = tk.StringVar(value="Layer descriptions will appear here.")
        self.summary_label = ttk.Label(
            self.form_frame,
            textvariable=self.summary_var,
            wraplength=1200,
            justify="left",
        )
        self.summary_label.pack(fill="x", expand=True, anchor="w", pady=(10, 0))

        # Build the initial set of per-layer dropdowns.
        self._refresh_layer_inputs()

    def register_layer_change_observer(self, callback):
        """Register a callback to be called whenever the layer configuration changes."""
        self.layer_change_observers.append(callback)

    def _notify_layer_change_observers(self):
        """Tell every registered page to refresh itself after the layer setup changes."""
        for callback in self.layer_change_observers:
            callback()

    def _refresh_layer_inputs(self, event=None):
        """Clear and recreate the per-layer feature dropdowns based on the selected layer count."""
        for widget in self.layer_feature_frame.winfo_children():
            widget.destroy()

        self.layer_feature_dropdowns.clear()

        try:
            layer_count = int(self.layers_dropdown.get())
        except ValueError:
            layer_count = 1

        self.config_values["number_of_layers"] = str(layer_count)

        for layer_number in range(1, layer_count + 1):
            layer_frame = ttk.LabelFrame(
                self.layer_feature_frame,
                text=f"Layer {layer_number}",
                padding=10,
            )
            layer_frame.pack(fill="x", pady=(0, 8), anchor="w")

            self.layer_feature_dropdowns[layer_number] = {}

            primary_frame = ttk.Frame(layer_frame)
            primary_frame.pack(fill="x", anchor="w", pady=(0, 5))

            secondary_frame = ttk.Frame(layer_frame)
            secondary_frame.pack(fill="x", anchor="w", pady=(0, 5))

            for feature_key, feature_label, options, placement in self.layer_feature_definitions:
                dropdown = DropdownObject(
                    primary_frame if placement == "primary" else secondary_frame,
                    f"{feature_label} in layer {layer_number}",
                    options,
                    default_value=options[0],
                    command=self._save_config_values,
                )
                dropdown.pack(side="left", anchor="w", padx=(0, 15), pady=(0, 5))
                self.layer_feature_dropdowns[layer_number][feature_key] = dropdown

        self._save_config_values()

        # Notify any dependent pages so they can rebuild their UI from the latest layer data.
        self._notify_layer_change_observers()

    def _save_config_values(self, event=None):
        """Store the current per-layer selections and build a reusable layer description list."""
        self.config_values["number_of_layers"] = self.layers_dropdown.get()

        layer_features = {}
        layer_description = []

        try:
            layer_count = int(self.config_values["number_of_layers"])
        except ValueError:
            layer_count = 1

        for layer_number in range(1, layer_count + 1):
            feature_values = {}
            for feature_key, feature_label, _, _ in self.layer_feature_definitions:
                dropdown = self.layer_feature_dropdowns.get(layer_number, {}).get(feature_key)
                if dropdown is not None:
                    feature_values[feature_key] = dropdown.get()

            layer_features[layer_number] = feature_values

            description_parts = []
            for feature_key, feature_label, _, _ in self.layer_feature_definitions:
                if feature_key in feature_values:
                    description_parts.append(f"{feature_label.lower()}={feature_values[feature_key]}")

            layer_description.append(
                f"Layer {layer_number}: " + ", ".join(description_parts)
            )

        self.config_values["layer_features"] = layer_features
        self.config_values["layer_description"] = layer_description

        if layer_description:
            self.summary_var.set("\n".join(layer_description))
        else:
            self.summary_var.set("No layers selected.")
