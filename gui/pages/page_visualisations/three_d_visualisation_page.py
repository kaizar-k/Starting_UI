import tkinter as tk
from tkinter import ttk

from backend.calibration_curve_backend import CalibrationCurveBackend
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

        self.canvas_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.canvas_frame.pack(fill="both", expand=True, anchor="w")

        self.canvas_3d = Sensor3DVisualisationCanvas(self.canvas_frame)
        self.canvas_3d.pack(fill="both", expand=True)

        # channel_number -> (layer_number, point_index), used to translate live pressure lookups.
        self._channel_to_layer_point = {}
        self._layer_calibration_inputs = {}
        self._layer_channel_map = {}
        self._calibration_backend = CalibrationCurveBackend()
        self._live_update_job = None

        self.refresh_from_config()

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
            self.canvas_3d._draw_empty_state("No plot selected.")
            return

        PressureVisualisation.reset_runtime_state()

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
                "area": float(calibration_data.get("area", 380.0)),
            }

            channel_numbers = layer_channel_map.get(layer_number, [])
            for point_index, channel_number in enumerate(channel_numbers, start=1):
                self._channel_to_layer_point[channel_number] = (layer_number, point_index)

        self._layer_channel_map = layer_channel_map
        # Sensor design outlines are always shown in the 3D view.
        self.canvas_3d.rebuild_structure(layer_geometries, True)
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
        self._schedule_live_updates()
