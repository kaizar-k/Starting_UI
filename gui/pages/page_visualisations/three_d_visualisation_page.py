import tkinter as tk
from tkinter import ttk

from backend.calibration_curve_backend import CalibrationCurveBackend
from gui.controls.colourbar import create_turbo_colorbar
from gui.pages.objects.page_object import PageObject
from visualisation_backend.pressure_visualisation import PressureVisualisation
from visualisation_backend.three_d_visualisation import Sensor3DVisualisationCanvas

# Live values refresh on the same cadence as the 2D page so both views stay in sync.
LIVE_VALUE_REFRESH_MS = 100
# 1 gram-force per mm^2 equals 9806.65 Pascals.
GRAM_PER_MM2_TO_PA = 9806.65


class ThreeDVisualisationPage(PageObject):
    """Shows every fully-configured layer stacked in 3D, coloured by live pressure."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        self.content_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.content_frame.pack(fill="both", expand=True, anchor="w")

        self.canvas_frame = ttk.Frame(self.content_frame)
        self.canvas_frame.pack(side="left", fill="both", expand=True, anchor="n")

        self.colorbar_frame = ttk.Frame(self.canvas_frame, padding=(0, 0, 10, 0))
        self.colorbar_frame.pack(side="left", anchor="n")
        _, self.colorbar_ax, self.colorbar_canvas = create_turbo_colorbar(self.colorbar_frame, width=0.7, height=3.2)
        self.colorbar_canvas.get_tk_widget().pack(anchor="n")

        self.canvas_3d = Sensor3DVisualisationCanvas(self.canvas_frame)
        self.canvas_3d.pack(side="left", fill="both", expand=True)

        self.pressure_list_frame = ttk.Frame(self.content_frame, padding=(20, 0, 0, 0))
        self.pressure_list_frame.pack(side="left", anchor="n")
        self._pressure_value_rows = []
        self.global_max_pressure_var = tk.StringVar(value="Global maximum pressure: -- Pa")

        # channel_number -> (layer_number, point_index), used to translate live pressure lookups.
        self._channel_to_layer_point = {}
        self._layer_calibration_inputs = {}
        self._layer_channel_map = {}
        self._calibration_backend = CalibrationCurveBackend()
        self._live_update_job = None

        self.refresh_from_config()

    def _clear_pressure_list(self):
        """Remove pressure rows when the plotted layer set changes or the plot is hidden."""
        pressure_list_frame = getattr(self, "pressure_list_frame", None)
        if pressure_list_frame is None:
            self._pressure_value_rows = []
            return

        for widget in pressure_list_frame.winfo_children():
            widget.destroy()
        self._pressure_value_rows = []
        self.global_max_pressure_var.set("Global maximum pressure: -- Pa")

        ttk.Label(
            self.pressure_list_frame,
            textvariable=self.global_max_pressure_var,
            width=32,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))

    def _build_pressure_list(self, layer_geometries):
        """Create a vertical live pressure readout for every sensing point in the 3D plot."""
        self._clear_pressure_list()
        for layer_number in sorted(layer_geometries):
            ttk.Label(
                self.pressure_list_frame,
                text=f"Layer {layer_number}",
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", pady=(0, 3))

            _dimensions, sensing_points = layer_geometries[layer_number]
            for point_index, _point in enumerate(sensing_points, start=1):
                pressure_var = tk.StringVar(value=f"Point {point_index} pressure: -- Pa")
                ttk.Label(self.pressure_list_frame, textvariable=pressure_var, width=28, anchor="w").pack(anchor="w", padx=(10, 0))
                self._pressure_value_rows.append((pressure_var, layer_number, point_index))

            ttk.Frame(self.pressure_list_frame, height=8).pack()

    def _schedule_live_updates(self):
        """Queue the next 3D redraw only while the plot is enabled and visible."""
        if self._live_update_job is not None:
            self.after_cancel(self._live_update_job)
            self._live_update_job = None

        config_page = self.master.pages[0]
        if not config_page.config_values.get("show_3d_plot", False):
            return

        self._live_update_job = self.after(LIVE_VALUE_REFRESH_MS, self._update_live_values)

    def refresh_from_config(self):
        """Rebuild the stacked-layer structure from the current config page state."""
        config_page = self.master.pages[0]
        if not config_page.config_values.get("show_3d_plot", False):
            if self._live_update_job is not None:
                self.after_cancel(self._live_update_job)
                self._live_update_job = None
            self._clear_pressure_list()
            self.canvas_3d._draw_empty_state("No plot selected.")
            return

        try:
            layer_count = int(config_page.config_values.get("number_of_layers", "1"))
        except ValueError:
            layer_count = 1

        sensor_design_backend = config_page.sensor_design_backend
        layer_channel_map = sensor_design_backend.build_channel_map(layer_count)

        layer_geometries = {}
        self._channel_to_layer_point = {}
        self._layer_calibration_inputs = {}

        for layer_number in range(1, layer_count + 1):
            if not config_page.is_layer_fully_configured(layer_number):
                continue

            design_name = sensor_design_backend.get_layer_sensor_type(layer_number)
            geometry = sensor_design_backend.get_design_geometry(design_name) if design_name else None
            if geometry is None:
                continue

            layer_geometries[layer_number] = geometry

            config_dropdown = config_page.layer_config_name_dropdowns.get(layer_number)
            configuration_name = config_dropdown.get() if config_dropdown is not None else "No selection"
            calibration_data = self._calibration_backend.load_configuration_data(configuration_name)
            self._layer_calibration_inputs[layer_number] = {
                "calibration_data": calibration_data,
                "area": float(calibration_data.get("area", 836.0)),
            }

            channel_numbers = layer_channel_map.get(layer_number, [])
            for point_index, channel_number in enumerate(channel_numbers, start=1):
                self._channel_to_layer_point[channel_number] = (layer_number, point_index)

        self._layer_channel_map = layer_channel_map
        # Sensor design outlines are always shown in the 3D view.
        self.canvas_3d.rebuild_structure(layer_geometries, True)
        self._build_pressure_list(layer_geometries)
        self._schedule_live_updates()

    def _update_live_values(self):
        self._live_update_job = None
        config_page = self.master.pages[0]
        if not config_page.config_values.get("show_3d_plot", False):
            return

        active_device = self.master.active_device

        pressure_by_layer_point = {}
        max_pressure_by_layer_point = {}

        for layer_number, calibration_input in self._layer_calibration_inputs.items():
            channel_numbers = self._layer_channel_map.get(layer_number, [])
            if not channel_numbers:
                continue

            layer_pressures = PressureVisualisation.get_pressure_for_all_points(
                active_device=active_device,
                channel_map={layer_number: channel_numbers},
                calibration_data=calibration_input["calibration_data"],
                area=calibration_input["area"],
            ).get(layer_number, [])

            fallback_max_pressure = float(calibration_input["calibration_data"].get("max_pressure", 0.0) or 0.0)

            for point_index, channel_number in enumerate(channel_numbers, start=1):
                key = (layer_number, point_index)

                point_state = PressureVisualisation._runtime_point_state.get(channel_number)
                max_pressure_by_layer_point[key] = float(
                    point_state.get("max_pressure", fallback_max_pressure) if point_state is not None else fallback_max_pressure
                )

                if point_index - 1 < len(layer_pressures) and layer_pressures[point_index - 1] is not None:
                    pressure_by_layer_point[key] = layer_pressures[point_index - 1] * GRAM_PER_MM2_TO_PA

        self.canvas_3d.set_heatmap_values(pressure_by_layer_point, max_pressure_by_layer_point)

        global_max_pressure = max(max_pressure_by_layer_point.values(), default=0.0)
        if global_max_pressure > 0:
            self.global_max_pressure_var.set(f"Global maximum pressure: {global_max_pressure:.2f} Pa")
        else:
            self.global_max_pressure_var.set("Global maximum pressure: -- Pa")

        for pressure_var, layer_number, point_index in self._pressure_value_rows:
            pressure_value = pressure_by_layer_point.get((layer_number, point_index))
            pressure_text = "--" if pressure_value is None else f"{pressure_value:.2f}"
            pressure_var.set(f"Point {point_index} pressure: {pressure_text} Pa")

        self._schedule_live_updates()
