import tkinter as tk
from tkinter import ttk

from backend.dropdown_backend import DropdownData
from backend.sensor_design_backend import SensorDesignBackend
from gui.controls.dropdown_object import DropdownObject
from gui.pages.objects.page_object import PageObject


def build_layer_feature_definitions(category_names, category_options):
    """Build the layer feature definitions from the current CSV-backed categories and options."""
    layer_feature_definitions = []
    for category_name in category_names:
        options = list(category_options.get(category_name, []))
        if not options:
            options = [""]
        layer_feature_definitions.append(
            (category_name.lower().replace(" ", "_"), category_name, ["No selection"] + options, "primary")
        )
    return layer_feature_definitions


class ConfigPage(PageObject):
    """Configuration page with dynamically generated per-layer feature controls."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        # Store the selected configuration values so they can be reused later.
        self.config_values = {
            "number_of_layers": "1",
            "layer_features": {},
            "layer_description": [],
            # Store the layers selected in the options popup so other pages can read them.
            "options_1_selected_layers": [],
            # Sensor type selected for each layer, in layer order.
            "layer_sensor_types": [],
        }

        self.dropdown_data = DropdownData()
        self.sensor_design_backend = SensorDesignBackend()
        self.category_names = self.dropdown_data.get_category_names()
        self.category_options = self.dropdown_data.get_options_by_category()

        # Define the per-layer features that should be editable for each layer.
        # Each feature uses the CSV-backed category names and their available options.
        self.layer_feature_definitions = build_layer_feature_definitions(self.category_names, self.category_options)

        # Keep track of the dynamically created dropdowns for each layer and feature.
        self.layer_feature_dropdowns = {}
        self.layer_config_name_dropdowns = {}
        self.layer_sensor_type_dropdowns = {}
        self.layer_warning_vars = {}
        self.layer_status_labels = {}
        self.device_controls_locked = False

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

    def refresh_from_config(self):
        """Reload the CSV-backed categories and options when the add/remove page changes them."""
        self.category_names = self.dropdown_data.get_category_names()
        self.category_options = self.dropdown_data.get_options_by_category()
        self.layer_feature_definitions = build_layer_feature_definitions(self.category_names, self.category_options)
        self._refresh_layer_inputs()

    def _get_configuration_names(self):
        """Return the saved configuration names with a No selection placeholder."""
        return self.dropdown_data.get_configuration_names()

    def is_layer_fully_configured(self, layer_number):
        """A layer is complete only when both configuration name and sensor design are selected."""
        config_dropdown = self.layer_config_name_dropdowns.get(layer_number)
        sensor_dropdown = self.layer_sensor_type_dropdowns.get(layer_number)
        configuration_name = config_dropdown.get() if config_dropdown else "No selection"
        sensor_type = sensor_dropdown.get() if sensor_dropdown else "No selection"
        return configuration_name != "No selection" and sensor_type != "No selection"

    def get_incomplete_layers(self):
        """Return all layer numbers that are missing either config name or sensor design."""
        try:
            layer_count = int(self.config_values.get("number_of_layers", "1"))
        except ValueError:
            layer_count = 1

        return [
            layer_number
            for layer_number in range(1, layer_count + 1)
            if not self.is_layer_fully_configured(layer_number)
        ]

    def set_device_running_state(self, is_running):
        """Lock configuration widgets while the device is active so the recorded CSV is not invalidated mid-run."""
        self.device_controls_locked = bool(is_running)
        state = "disabled" if is_running else "readonly"

        self.layers_dropdown.dropdown.configure(state=state)

        for config_dropdown in self.layer_config_name_dropdowns.values():
            config_dropdown.set_state(state)

        for feature_group in self.layer_feature_dropdowns.values():
            for dropdown in feature_group.values():
                dropdown.set_state(state)

        for sensor_dropdown in self.layer_sensor_type_dropdowns.values():
            sensor_dropdown.set_state(state)

    def _handle_configuration_name_selection(self, layer_number, event=None):
        """When a preset is chosen, fill the layer's manual dropdowns from that configuration."""
        if self.device_controls_locked:
            return

        selected_name = self.layer_config_name_dropdowns[layer_number].get()

        if not selected_name or selected_name == "No selection":
            self._refresh_layer_status(layer_number)
            return

        values = self.dropdown_data.get_configuration_values_by_name(selected_name)
        if values:
            for feature_key, feature_label, _, _ in self.layer_feature_definitions:
                dropdown = self.layer_feature_dropdowns.get(layer_number, {}).get(feature_key)
                if dropdown is None:
                    continue
                option_value = values.get(feature_label, "No selection")
                dropdown.set(option_value if option_value else "No selection")

        self._refresh_layer_status(layer_number)
        self._save_config_values()

    def _handle_manual_selection(self, layer_number, event=None):
        """When a manual category value changes, resolve the matching preset name for that layer."""
        if self.device_controls_locked:
            return

        selected_values = {}
        for feature_key, feature_label, _, _ in self.layer_feature_definitions:
            dropdown = self.layer_feature_dropdowns.get(layer_number, {}).get(feature_key)
            if dropdown is None:
                continue
            value = dropdown.get()
            if value and value != "No selection":
                selected_values[feature_label] = value

        if not selected_values:
            self.layer_config_name_dropdowns[layer_number].set("No selection")
            self._refresh_layer_status(layer_number)
            return

        matched_name = self.dropdown_data.find_configuration_name_for_values(selected_values)
        self.layer_config_name_dropdowns[layer_number].set(matched_name if matched_name else "No selection")
        self._refresh_layer_status(layer_number)
        self._save_config_values()

    def _handle_sensor_type_selection(self, layer_number, event=None):
        """Store the sensor design chosen for this layer."""
        if self.device_controls_locked:
            return

        sensor_type = self.layer_sensor_type_dropdowns[layer_number].get()
        self.sensor_design_backend.set_layer_sensor_type(layer_number, sensor_type)
        self._refresh_layer_status(layer_number)
        self._save_config_values()
        # A changed sensor design changes each layer's sensing-point count, so
        # dependent pages (2D diagrams, live channel count) must refresh too.
        self._notify_layer_change_observers()

    def _refresh_layer_status(self, layer_number):
        """Show the configuration name and sensor design for this layer, or a warning if either is missing."""
        warning_var = self.layer_warning_vars.get(layer_number)
        if warning_var is None:
            return

        config_dropdown = self.layer_config_name_dropdowns.get(layer_number)
        sensor_dropdown = self.layer_sensor_type_dropdowns.get(layer_number)
        configuration_name = config_dropdown.get() if config_dropdown else "No selection"
        sensor_type = sensor_dropdown.get() if sensor_dropdown else "No selection"

        if configuration_name == "No selection" or sensor_type == "No selection":
            warning_var.set("Note: Both sensor design and configuration need to be selected.")
        else:
            warning_var.set(f"Configuration: {configuration_name}, Sensor design: {sensor_type}")

        status_label = self.layer_status_labels.get(layer_number)
        if status_label is not None:
            status_label.configure(foreground="black" if configuration_name != "No selection" and sensor_type != "No selection" else "red")

    def _refresh_layer_inputs(self, event=None):
        """Clear and recreate the per-layer feature dropdowns based on the selected layer count."""
        for widget in self.layer_feature_frame.winfo_children():
            widget.destroy()

        self.layer_feature_dropdowns.clear()
        self.layer_status_labels.clear()

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
            self.layer_warning_vars[layer_number] = tk.StringVar(value="")

            selection_frame = ttk.Frame(layer_frame)
            selection_frame.pack(fill="x", anchor="w", pady=(0, 5))

            configuration_dropdown = DropdownObject(
                selection_frame,
                "Configuration name",
                self._get_configuration_names(),
                default_value="No selection",
                width=22,
            )
            configuration_dropdown.pack(side="left", anchor="n", padx=(0, 12))
            self.layer_config_name_dropdowns[layer_number] = configuration_dropdown
            configuration_dropdown.dropdown.bind(
                "<<ComboboxSelected>>",
                lambda event, number=layer_number: self._handle_configuration_name_selection(number, event),
            )

            or_label = ttk.Label(selection_frame, text="OR", font=("TkDefaultFont", 15, "bold"))
            or_label.pack(side="left", padx=(18, 32), anchor="n")

            for feature_key, feature_label, options, _ in self.layer_feature_definitions:
                dropdown = DropdownObject(
                    selection_frame,
                    feature_label,
                    options,
                    default_value="No selection",
                    width=18,
                    command=lambda event, number=layer_number: self._handle_manual_selection(number, event),
                )
                dropdown.pack(side="left", anchor="w", padx=(0, 15), pady=(0, 5))
                self.layer_feature_dropdowns[layer_number][feature_key] = dropdown

            sensor_type_dropdown = DropdownObject(
                layer_frame,
                "Sensor design",
                self.sensor_design_backend.get_sensor_type_options(),
                default_value="No selection",
                width=18,
                command=lambda event, number=layer_number: self._handle_sensor_type_selection(number, event),
            )
            sensor_type_dropdown.pack(anchor="w", pady=(5, 5))
            self.layer_sensor_type_dropdowns[layer_number] = sensor_type_dropdown
            existing_sensor_type = self.sensor_design_backend.get_layer_sensor_type(layer_number)
            if existing_sensor_type:
                sensor_type_dropdown.set(existing_sensor_type)

            warning_label = ttk.Label(
                layer_frame,
                textvariable=self.layer_warning_vars[layer_number],
                foreground="red",
                wraplength=1000,
                justify="left",
            )
            warning_label.pack(anchor="w", pady=(8, 0))
            self.layer_status_labels[layer_number] = warning_label
            self._refresh_layer_status(layer_number)

        self._save_config_values()
        self.set_device_running_state(bool(getattr(self.master, "active_device", None) and self.master.active_device.running))

        # Force the page canvas to recalculate its scroll region after the new layer controls are added.
        self._schedule_scroll_region_update()

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

            config_dropdown = self.layer_config_name_dropdowns.get(layer_number)
            configuration_name = config_dropdown.get() if config_dropdown else "No selection"
            sensor_dropdown = self.layer_sensor_type_dropdowns.get(layer_number)
            sensor_type = sensor_dropdown.get() if sensor_dropdown else "No selection"
            description_parts.append(f"configuration name={configuration_name}")
            description_parts.append(f"sensor design={sensor_type}")

            layer_description.append(
                f"Layer {layer_number}: " + ", ".join(description_parts)
            )

        self.config_values["layer_features"] = layer_features
        self.config_values["layer_description"] = layer_description
        self.config_values["layer_sensor_types"] = self.sensor_design_backend.get_ordered_sensor_types(layer_count)

        if layer_description:
            self.summary_var.set("\n".join(layer_description))
        else:
            self.summary_var.set("No layers selected.")
