import tkinter as tk
from tkinter import ttk

from gui.controls.sensor_design_canvas import SensorDesignCanvas
from gui.pages.objects.page_object import PageObject
from visualisation_backend.layer_text_backend import LayerTextBackend

# Live resistance labels are refreshed on this interval rather than per serial read.
LIVE_VALUE_REFRESH_MS = 100


class TwoDVisualisationPage(PageObject):
    """Shows the sensor design diagram for each layer selected in the Options 1 popup."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        self.selected_layers_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.selected_layers_frame.pack(fill="both", expand=True, anchor="w")

        ttk.Label(
            self.selected_layers_frame,
            text="Selected layers:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        # Diagrams are rebuilt inside this frame so the heading above stays in place.
        self.diagrams_frame = ttk.Frame(self.selected_layers_frame)
        self.diagrams_frame.pack(fill="both", expand=True, anchor="w")

        # Rows currently displayed, refreshed whenever the layer selection changes.
        self._live_value_rows = []

        self.refresh_selected_layers_display()
        self.after(LIVE_VALUE_REFRESH_MS, self._update_live_values)

    def refresh_from_config(self):
        """Refresh the 2D page when the config object changes."""
        self.refresh_selected_layers_display()

    def refresh_selected_layers_display(self):
        for widget in self.diagrams_frame.winfo_children():
            widget.destroy()
        self._live_value_rows = []

        config_page = self.master.pages[0]
        selected_layers = config_page.config_values.get("options_1_selected_layers", [])

        if not selected_layers:
            ttk.Label(self.diagrams_frame, text="No layers selected.").pack(anchor="w")
            return

        display_layers = [
            layer_number for layer_number in selected_layers if config_page.is_layer_fully_configured(layer_number)
        ]
        if not display_layers:
            ttk.Label(
                self.diagrams_frame,
                text="No fully configured selected layers to display.",
            ).pack(anchor="w")
            return

        sensor_design_backend = config_page.sensor_design_backend
        layer_text_backend = LayerTextBackend(sensor_design_backend)
        try:
            layer_count = int(config_page.config_values.get("number_of_layers", "1"))
        except ValueError:
            layer_count = 1

        for layer_number in display_layers:
            design_name = sensor_design_backend.get_layer_sensor_type(layer_number)
            geometry = sensor_design_backend.get_design_geometry(design_name) if design_name else None

            layer_frame = ttk.LabelFrame(
                self.diagrams_frame,
                text=f"Layer {layer_number} - {design_name or 'No selection'}",
                padding=10,
            )
            layer_frame.pack(anchor="w", pady=(0, 15), fill="x")

            if geometry is None:
                ttk.Label(
                    layer_frame,
                    text="No sensor design available for this layer.",
                ).pack(anchor="w")
                continue

            layer_content_frame = ttk.Frame(layer_frame)
            layer_content_frame.pack(anchor="w", fill="x")

            dimensions, sensing_points = geometry
            SensorDesignCanvas(layer_content_frame, dimensions, sensing_points).pack(side="left", anchor="n")

            # Vertical list of live resistances, one row per sensing point, next to the diagram.
            points_frame = ttk.Frame(layer_content_frame, padding=(15, 0))
            points_frame.pack(side="left", anchor="n")

            rows = layer_text_backend.build_layer_point_rows(layer_number, layer_count, self.master.active_device)
            for point_index, _channel_number, label_text in rows:
                row_var = tk.StringVar(value=label_text)
                ttk.Label(points_frame, textvariable=row_var).pack(anchor="w")
                self._live_value_rows.append((row_var, layer_number, point_index))

        self._layer_text_backend = layer_text_backend
        self._layer_count = layer_count

    def _update_live_values(self):
        active_device = self.master.active_device
        for row_var, layer_number, point_index in self._live_value_rows:
            rows = self._layer_text_backend.build_layer_point_rows(layer_number, self._layer_count, active_device)
            if point_index - 1 < len(rows):
                row_var.set(rows[point_index - 1][2])

        self.after(LIVE_VALUE_REFRESH_MS, self._update_live_values)
