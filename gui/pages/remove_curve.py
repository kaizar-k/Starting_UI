import pandas as pd
import tkinter as tk
from tkinter import ttk

from backend.dropdown_backend import DropdownData
from gui.controls.dropdown_object import DropdownObject


class RemoveCalibrationCurveSection(ttk.LabelFrame):
    """Section for removing a saved calibration threshold force from an existing sensor configuration."""

    def __init__(self, parent, refresh_callback=None):
        super().__init__(parent, text="Remove calibration curve", padding=12)
        self.refresh_callback = refresh_callback
        self.dropdown_data = DropdownData()
        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Choose a configuration and remove its saved threshold-force calibration value.",
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

        save_button = ttk.Button(self, text="Remove threshold force", command=self._remove_threshold_force)
        save_button.pack(anchor="e", pady=(8, 0))

    def _get_configuration_names(self):
        try:
            if not self.dropdown_data.configurations_csv_path.exists():
                return ["No selection"]
            configuration_df = pd.read_csv(self.dropdown_data.configurations_csv_path)
        except Exception:
            return ["No selection"]

        names = configuration_df["configuration_name"].fillna("").astype(str).str.strip().tolist()
        unique_names = []
        for name in names:
            if name and name not in unique_names:
                unique_names.append(name)
        return ["No selection"] + unique_names

    def _remove_threshold_force(self):
        configuration_name = self.configuration_dropdown.get().strip()
        if not configuration_name or configuration_name == "No selection":
            self.message_label.config(text="Please choose a configuration name before removing the threshold force.")
            return

        try:
            df = pd.read_csv(self.dropdown_data.configurations_csv_path)
        except Exception:
            self.message_label.config(text="Could not find the configuration data file.")
            return

        matches = df["configuration_name"].astype(str).str.strip() == configuration_name
        if not matches.any():
            self.message_label.config(text="The selected configuration name does not exist.")
            return

        df.loc[matches, "threshold_force"] = ""
        df.to_csv(self.dropdown_data.configurations_csv_path, index=False)

        self.message_label.config(text=f"Threshold force removed for '{configuration_name}'.")
        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.configuration_dropdown.dropdown.configure(values=self._get_configuration_names())
        self.configuration_dropdown.set("No selection")
        self.message_label.config(text="")
