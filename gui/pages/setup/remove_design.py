from tkinter import ttk

from backend.sensor_design_backend import SensorDesignBackend
from gui.controls.dropdown_object import DropdownObject


class RemoveSensorDesignSection(ttk.LabelFrame):
    """Section for removing an existing sensor design option."""

    def __init__(self, parent, refresh_callback=None):
        super().__init__(parent, text="Remove sensor design", padding=12)
        self.refresh_callback = refresh_callback
        self.backend = SensorDesignBackend()
        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Choose a sensor design to remove it from the available options.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w", pady=(8, 0))

        self.sensor_design_dropdown = DropdownObject(
            controls_frame,
            "Sensor design",
            self._get_sensor_design_names(),
            default_value="No selection",
            width=22,
        )
        self.sensor_design_dropdown.pack(side="left", anchor="n", padx=(0, 12))

        self.message_label = ttk.Label(self, text="", foreground="red", wraplength=1000, justify="left")
        self.message_label.pack(anchor="w", pady=(8, 0))

        save_button = ttk.Button(self, text="Remove sensor design", command=self._remove_sensor_design)
        save_button.pack(anchor="e", pady=(8, 0))

    def _get_sensor_design_names(self):
        # Prefix with "No selection" so the dropdown always has a safe default.
        return ["No selection"] + self.backend.get_sensor_type_options()

    def _remove_sensor_design(self):
        sensor_design_name = self.sensor_design_dropdown.get().strip()
        if not sensor_design_name or sensor_design_name == "No selection":
            self.message_label.config(text="Please choose a sensor design before removing it.")
            return

        if not self.backend.remove_sensor_design(sensor_design_name):
            self.message_label.config(text="The selected sensor design does not exist.")
            return

        # Refresh the dropdown values and reset selection so the removed design disappears immediately.
        self.sensor_design_dropdown.dropdown.configure(values=self._get_sensor_design_names())
        self.sensor_design_dropdown.set("No selection")
        self.message_label.config(text=f"Sensor design '{sensor_design_name}' removed.")

        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.sensor_design_dropdown.dropdown.configure(values=self._get_sensor_design_names())
        self.sensor_design_dropdown.set("No selection")
        self.message_label.config(text="")
