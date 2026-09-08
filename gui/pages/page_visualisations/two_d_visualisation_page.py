import tkinter as tk
from tkinter import ttk

from backend.calibration_curve_backend import CalibrationCurveBackend
from gui.controls.colourbar import create_turbo_colorbar
from gui.controls.sensor_design_canvas import SensorDesignCanvas
from gui.pages.objects.page_object import PageObject
from visualisation_backend.layer_text_backend import LayerTextBackend
from visualisation_backend.pressure_visualisation import PressureVisualisation
from visualisation_backend.trace_visualisation import TracePopup

# Live resistance labels are refreshed on this interval rather than per serial read.
LIVE_VALUE_REFRESH_MS = 100
# 1 gram-force per mm^2 equals 9806.65 Pascals.
GRAM_PER_MM2_TO_PA = 9806.65


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
        self._trace_windows = {}
        self._layer_channel_map = {}
        self._layer_calibration_inputs = {}
        self._layer_canvases = {}
        self._layer_colorbars = {}
        self._calibration_backend = CalibrationCurveBackend()

        self.refresh_selected_layers_display()
        self.after(LIVE_VALUE_REFRESH_MS, self._update_live_values)

    def refresh_from_config(self):
        """Refresh the 2D page when the config object changes."""
        self.refresh_selected_layers_display()

    def open_trace_for_point(self, layer_number, point_index, channel_number):
        """Open a live trace window for the clicked sensor point."""
        if self.master.active_device is None:
            return

        key = (layer_number, point_index)
        existing = self._trace_windows.get(key)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return

        popup = TracePopup(
            self,
            layer_number=layer_number,
            point_index=point_index,
            channel_number=channel_number,
            device_provider=lambda: self.master.active_device,
        )
        self._trace_windows[key] = popup.window

    def close_trace_windows(self):
        """Drop every open trace window so a new run cannot show the previous run's curve."""
        TracePopup.close_all()
        self._trace_windows = {}

    def refresh_selected_layers_display(self):
        for widget in self.diagrams_frame.winfo_children():
            widget.destroy()
        self._live_value_rows = []
        self._layer_channel_map = {}
        self._layer_calibration_inputs = {}
        self._layer_canvases = {}

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

        self._layer_channel_map = sensor_design_backend.build_channel_map(layer_count)

        for layer_number in display_layers:
            design_name = sensor_design_backend.get_layer_sensor_type(layer_number)
            geometry = sensor_design_backend.get_design_geometry(design_name) if design_name else None
            config_dropdown = config_page.layer_config_name_dropdowns.get(layer_number)
            configuration_name = config_dropdown.get() if config_dropdown is not None else "No selection"
            calibration_data = self._calibration_backend.load_configuration_data(configuration_name)
            self._layer_calibration_inputs[layer_number] = {
                "calibration_data": calibration_data,
                "area": float(calibration_data.get("area", 836.0)),
            }

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

            layer_max_drdt = config_page.config_values.get("layer_max_drdt", {}).get(layer_number)
            ttk.Label(
                layer_frame,
                text=f"Max dR_rel/dt: {layer_max_drdt if layer_max_drdt is not None else 'Not set'}",
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", pady=(0, 6))

            dimensions, sensing_points = geometry
            sensor_canvas = SensorDesignCanvas(
                layer_content_frame,
                dimensions,
                sensing_points,
                layer_number=layer_number,
                layer_count=layer_count,
                sensor_design_backend=sensor_design_backend,
                open_trace_callback=self.open_trace_for_point,
            )
            sensor_canvas.pack(side="left", anchor="n")
            self._layer_canvases[layer_number] = sensor_canvas

            _, colorbar_ax, colorbar_canvas = create_turbo_colorbar(layer_content_frame, width=0.7, height=2.5)
            colorbar_canvas.get_tk_widget().pack(side="left", anchor="n", padx=(10, 0))
            self._layer_colorbars[layer_number] = (colorbar_canvas, colorbar_ax)

            # Vertical list of live pressures and resistances, one row per sensing point, next to the diagram.
            points_frame = ttk.Frame(layer_content_frame, padding=(15, 0))
            points_frame.pack(side="left", anchor="n")

            heading_frame = ttk.Frame(points_frame)
            heading_frame.pack(anchor="w", pady=(0, 4))
            ttk.Label(heading_frame, text="Point", font=("Segoe UI", 10, "bold"), width=8).grid(
                row=0, column=0, sticky="w", padx=(0, 10)
            )
            ttk.Label(heading_frame, text="Pressure (Pa)", font=("Segoe UI", 10, "bold"), width=18).grid(
                row=0, column=1, sticky="w", padx=(0, 10)
            )
            ttk.Label(heading_frame, text="Resistance (Ω)", font=("Segoe UI", 10, "bold"), width=18).grid(
                row=0, column=2, sticky="w"
            )
            ttk.Label(heading_frame, text="Max pressure (Pa)", font=("Segoe UI", 10, "bold"), width=18).grid(
                row=0, column=3, sticky="w"
            )

            rows = layer_text_backend.build_layer_point_rows(layer_number, layer_count, self.master.active_device)
            for point_index, channel_number, _label_text in rows:
                row_frame = ttk.Frame(points_frame)
                row_frame.pack(anchor="w", pady=(0, 1))

                ttk.Label(row_frame, text=f"Point {point_index}", width=8).grid(row=0, column=0, sticky="w", padx=(0, 10))

                pressure_var = tk.StringVar(value="--")
                resistance_var = tk.StringVar(value="--")
                max_pressure_var = tk.StringVar(value="--")
                ttk.Label(row_frame, textvariable=pressure_var, width=18).grid(row=0, column=1, sticky="w", padx=(0, 10))
                ttk.Label(row_frame, textvariable=resistance_var, width=18).grid(row=0, column=2, sticky="w", padx=(0, 10))
                ttk.Label(row_frame, textvariable=max_pressure_var, width=18).grid(row=0, column=3, sticky="w")
                self._live_value_rows.append(
                    (pressure_var, resistance_var, max_pressure_var, layer_number, point_index, channel_number)
                )

        self._layer_text_backend = layer_text_backend
        self._layer_count = layer_count

    def _update_live_values(self):
        active_device = self.master.active_device
        rows_by_layer = {}
        for _pressure_var, _resistance_var, _max_pressure_var, layer_number, _point_index, _channel_number in self._live_value_rows:
            if layer_number not in rows_by_layer:
                rows_by_layer[layer_number] = self._layer_text_backend.build_layer_point_rows(
                    layer_number,
                    self._layer_count,
                    active_device,
                )

        pressure_by_layer = {}
        for layer_number, calibration_input in self._layer_calibration_inputs.items():
            channel_numbers = self._layer_channel_map.get(layer_number, [])
            if not channel_numbers:
                pressure_by_layer[layer_number] = []
                continue

            layer_pressures = PressureVisualisation.get_pressure_for_all_points(
                active_device=active_device,
                channel_map={layer_number: channel_numbers},
                calibration_data=calibration_input["calibration_data"],
                area=calibration_input["area"],
            )
            pressure_by_layer[layer_number] = layer_pressures.get(layer_number, [])

        for layer_number, sensor_canvas in self._layer_canvases.items():
            layer_pressures = pressure_by_layer.get(layer_number, [])
            point_pressures_pa = [
                None if pressure_value is None else pressure_value * GRAM_PER_MM2_TO_PA
                for pressure_value in layer_pressures
            ]

            calibration_input = self._layer_calibration_inputs.get(layer_number, {})
            fallback_max_pressure = float(calibration_input.get("calibration_data", {}).get("max_pressure", 0.0) or 0.0)
            point_max_pressures_pa = []
            for channel_number in self._layer_channel_map.get(layer_number, []):
                point_state = PressureVisualisation._runtime_point_state.get(channel_number)
                if point_state is not None:
                    point_max_pressures_pa.append(float(point_state.get("max_pressure", fallback_max_pressure) or 0.0))
                else:
                    point_max_pressures_pa.append(fallback_max_pressure)

            sensor_canvas.set_heatmap_values(point_pressures_pa, point_max_pressures_pa)

        for pressure_var, resistance_var, max_pressure_var, layer_number, point_index, channel_number in self._live_value_rows:
            rows = rows_by_layer.get(layer_number, [])
            if point_index - 1 >= len(rows):
                continue

            resistance_label = rows[point_index - 1][2]
            resistance_text = resistance_label.split(": ", 1)[1] if ": " in resistance_label else resistance_label
            layer_pressures = pressure_by_layer.get(layer_number, [])
            pressure_value = layer_pressures[point_index - 1] if point_index - 1 < len(layer_pressures) else None
            if pressure_value is None:
                pressure_text = "--"
            else:
                pressure_text = f"{pressure_value * GRAM_PER_MM2_TO_PA:.2f}"

            pressure_var.set(pressure_text)
            resistance_var.set(resistance_text)

            calibration_input = self._layer_calibration_inputs.get(layer_number, {})
            fallback_max_pressure = float(calibration_input.get("calibration_data", {}).get("max_pressure", 0.0) or 0.0)
            point_state = PressureVisualisation._runtime_point_state.get(channel_number)
            max_pressure = float(point_state.get("max_pressure", fallback_max_pressure) if point_state else fallback_max_pressure)
            max_pressure_var.set(f"{max_pressure:.2f}" if max_pressure > 0 else "--")

        self.after(LIVE_VALUE_REFRESH_MS, self._update_live_values)
