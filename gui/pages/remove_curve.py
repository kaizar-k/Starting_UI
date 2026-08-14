import tkinter as tk
from tkinter import ttk

from backend.calibration_curve_backend import CalibrationCurveBackend
from gui.controls.dropdown_object import DropdownObject


class RemoveCalibrationCurveSection(ttk.LabelFrame):
    """Section for removing a saved calibration curve from an existing sensor configuration."""

    def __init__(self, parent, refresh_callback=None):
        super().__init__(parent, text="Remove calibration curve", padding=12)
        self.refresh_callback = refresh_callback
        self.backend = CalibrationCurveBackend()
        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Choose a configuration and remove its saved threshold-force and regime calibration data.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w", pady=(8, 0))

        self.configuration_dropdown = DropdownObject(
            controls_frame,
            "Configuration name",
            self._get_configuration_names(),
            default_value="No selection",
            width=22,
        )
        self.configuration_dropdown.pack(side="left", anchor="n", padx=(0, 12))

        self.message_label = ttk.Label(self, text="", foreground="red", wraplength=1000, justify="left")
        self.message_label.pack(anchor="w", pady=(8, 0))

        save_button = ttk.Button(self, text="Remove calibration curve", command=self._remove_calibration_curve)
        save_button.pack(anchor="e", pady=(8, 0))

    def _get_configuration_names(self):
        return self.backend.get_configuration_names()

    def _remove_calibration_curve(self):
        configuration_name = self.configuration_dropdown.get().strip()
        if not configuration_name or configuration_name == "No selection":
            self.message_label.config(text="Please choose a configuration name before removing the calibration curve.")
            return

        try:
            self.backend.remove_calibration_curve(configuration_name)
        except ValueError as exc:
            self.message_label.config(text=str(exc))
            return

        # Reset the visible selector after the row is cleared so the remove section always reflects
        # the current saved data. Without this, the old selected configuration can remain in the UI even
        # though the CSV has already been updated.
        self.configuration_dropdown.dropdown.configure(values=self._get_configuration_names())
        self.configuration_dropdown.set("No selection")
        self.message_label.config(text=f"Calibration curve removed for '{configuration_name}'.")

        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.configuration_dropdown.dropdown.configure(values=self._get_configuration_names())
        self.configuration_dropdown.set("No selection")
        self.message_label.config(text="")
