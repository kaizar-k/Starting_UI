from tkinter import ttk

from gui.controls.sensor_design_canvas import SensorDesignCanvas
from gui.pages.objects.page_object import PageObject


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

        self.refresh_selected_layers_display()

    def refresh_from_config(self):
        """Refresh the 2D page when the config object changes."""
        self.refresh_selected_layers_display()

    def refresh_selected_layers_display(self):
        for widget in self.diagrams_frame.winfo_children():
            widget.destroy()

        config_page = self.master.pages[0]
        selected_layers = config_page.config_values.get("options_1_selected_layers", [])

        if not selected_layers:
            ttk.Label(self.diagrams_frame, text="No layers selected.").pack(anchor="w")
            return

        sensor_design_backend = config_page.sensor_design_backend

        for layer_number in selected_layers:
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

            dimensions, sensing_points = geometry
            SensorDesignCanvas(layer_frame, dimensions, sensing_points).pack(anchor="w")
