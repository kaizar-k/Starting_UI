import tkinter as tk
from tkinter import ttk

from backend.sensor_design_backend import SensorDesignBackend
from gui.controls.dropdown_object import DropdownObject


class AddSensorDesignSection(ttk.LabelFrame):
    """Section for adding a new sensor design option with its point coordinates."""

    def __init__(self, parent, refresh_callback=None):
        super().__init__(parent, text="Add sensor design", padding=12)
        self.refresh_callback = refresh_callback
        self.backend = SensorDesignBackend()
        self.coordinate_entries = []
        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Enter a name for the new sensor design and the (x, y) coordinates of each sensing point.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w", pady=(8, 0))

        ttk.Label(controls_frame, text="Sensor design name:").pack(side="left", padx=(0, 8), anchor="n")
        self.sensor_design_name_var = tk.StringVar(value="")
        self.sensor_design_name_entry = ttk.Entry(controls_frame, textvariable=self.sensor_design_name_var, width=22)
        self.sensor_design_name_entry.pack(side="left", anchor="n")

        self.coordinate_count_frame = ttk.Frame(self)
        self.coordinate_count_frame.pack(fill="x", anchor="w", pady=(10, 0))

        ttk.Label(self.coordinate_count_frame, text="Number of coordinates:").pack(side="left", anchor="n")
        self.coordinate_count_dropdown = DropdownObject(
            self.coordinate_count_frame,
            "",
            [str(value) for value in range(1, 9)],
            default_value="1",
            width=8,
            command=self._refresh_coordinate_rows,
        )
        self.coordinate_count_dropdown.label.pack_forget()
        self.coordinate_count_dropdown.pack(side="left", anchor="n", padx=(8, 0))

        self.coordinate_rows_frame = ttk.Frame(self)
        self.coordinate_rows_frame.pack(fill="x", anchor="w", pady=(8, 0))

        self.message_label = ttk.Label(self, text="", foreground="red", wraplength=1000, justify="left")
        self.message_label.pack(anchor="w", pady=(8, 0))

        self._refresh_coordinate_rows()

        save_button = ttk.Button(self, text="Add sensor design", command=self._add_sensor_design)
        save_button.pack(anchor="e", pady=(8, 0))

    def _refresh_coordinate_rows(self, event=None):
        for widget in self.coordinate_rows_frame.winfo_children():
            widget.destroy()

        self.coordinate_entries = []
        try:
            coordinate_count = int(self.coordinate_count_dropdown.get())
        except ValueError:
            coordinate_count = 1

        for coordinate_index in range(1, coordinate_count + 1):
            coordinate_frame = ttk.Frame(self.coordinate_rows_frame)
            coordinate_frame.pack(fill="x", anchor="w", pady=(0, 6))

            ttk.Label(coordinate_frame, text=f"Coordinate {coordinate_index}:", font=("TkDefaultFont", 9, "bold")).pack(
                side="left", anchor="n", padx=(0, 12)
            )

            ttk.Label(coordinate_frame, text="X-coordinate:").pack(side="left", anchor="n", padx=(0, 5))
            x_var = tk.StringVar(value="0")
            ttk.Entry(coordinate_frame, textvariable=x_var, width=10).pack(side="left", anchor="n", padx=(0, 12))

            ttk.Label(coordinate_frame, text="Y-coordinate:").pack(side="left", anchor="n", padx=(0, 5))
            y_var = tk.StringVar(value="0")
            ttk.Entry(coordinate_frame, textvariable=y_var, width=10).pack(side="left", anchor="n")

            self.coordinate_entries.append({"x": x_var, "y": y_var})

    def _add_sensor_design(self):
        sensor_design_name = self.sensor_design_name_var.get().strip()
        if not sensor_design_name:
            self.message_label.config(text="Please enter a sensor design name.")
            return

        try:
            coordinates = self.backend.build_coordinate_payload(self.coordinate_entries)
        except ValueError as exc:
            self.message_label.config(text=str(exc))
            return

        try:
            self.backend.add_sensor_design(sensor_design_name, coordinates)
        except ValueError as exc:
            self.message_label.config(text=str(exc))
            return

        self.message_label.config(text=f"Sensor design '{sensor_design_name}' added.")
        self.sensor_design_name_var.set("")
        self.coordinate_count_dropdown.set("1")
        self._refresh_coordinate_rows()

        # Let the parent page refresh dependent dropdowns (e.g. the config page's sensor design list).
        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.sensor_design_name_var.set("")
        self.coordinate_count_dropdown.set("1")
        self._refresh_coordinate_rows()
        self.message_label.config(text="")
