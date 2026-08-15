import tkinter as tk
from tkinter import ttk

from backend.calibration_curve_backend import CalibrationCurveBackend
from gui.controls.dropdown_object import DropdownObject


class AddCalibrationCurveSection(ttk.LabelFrame):
    """Section for adding or replacing a calibration curve on an existing sensor configuration."""

    def __init__(self, parent, refresh_callback=None):
        super().__init__(parent, text="Add/ Replace calibration curve", padding=12)
        self.refresh_callback = refresh_callback
        self.backend = CalibrationCurveBackend()
        self.regime_entries = []
        self.regime_count_var = tk.StringVar(value="1")
        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Choose an existing configuration, add the threshold force, and define the regime polynomial coefficients.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w")

        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(fill="x", anchor="w", pady=(8, 0))

        self.configuration_dropdown = DropdownObject(
            self.top_frame,
            "Configuration name",
            self._get_configuration_names(),
            default_value="No selection",
            width=22,
        )
        self.configuration_dropdown.pack(side="left", anchor="n", padx=(0, 12))
        self.configuration_dropdown.dropdown.bind("<<ComboboxSelected>>", self._load_existing_configuration_data)

        ttk.Label(self.top_frame, text="Lower threshold (g):").pack(side="left", padx=(0, 8), anchor="n")
        self.lower_threshold_var = tk.StringVar(value="0")
        self.lower_threshold_entry = ttk.Entry(self.top_frame, textvariable=self.lower_threshold_var, width=14)
        self.lower_threshold_entry.pack(side="left", anchor="n")

        ttk.Label(self.top_frame, text="Upper threshold (g):").pack(side="left", padx=(8, 8), anchor="n")
        self.upper_threshold_var = tk.StringVar(value="0")
        self.upper_threshold_entry = ttk.Entry(self.top_frame, textvariable=self.upper_threshold_var, width=14)
        self.upper_threshold_entry.pack(side="left", anchor="n")

        self.regime_count_frame = ttk.Frame(self)
        self.regime_count_frame.pack(fill="x", anchor="w", pady=(10, 0))

        ttk.Label(self.regime_count_frame, text="Number of curve regimes:").pack(side="left", anchor="n")
        self.regime_count_dropdown = DropdownObject(
            self.regime_count_frame,
            "",
            [str(value) for value in range(1, 6)],
            default_value="1",
            width=8,
            command=self._refresh_regime_rows,
        )
        self.regime_count_dropdown.label.pack_forget()
        self.regime_count_dropdown.pack(side="left", anchor="n", padx=(8, 0))

        self.regime_rows_frame = ttk.Frame(self)
        self.regime_rows_frame.pack(fill="x", anchor="w", pady=(8, 0))

        self.message_label = ttk.Label(self, text="", foreground="red", wraplength=1000, justify="left")
        self.message_label.pack(anchor="w", pady=(8, 0))

        self._refresh_regime_rows()

        save_button = ttk.Button(self, text="Save calibration curve", command=self._save_calibration_curve)
        save_button.pack(anchor="e", pady=(8, 0))

    def _get_configuration_names(self):
        return self.backend.get_configuration_names()

    def _load_existing_configuration_data(self, event=None):
        configuration_name = self.configuration_dropdown.get()
        if not configuration_name or configuration_name == "No selection":
            self.lower_threshold_var.set("0")
            self.upper_threshold_var.set("0")
            self.regime_count_dropdown.set("1")
            self._refresh_regime_rows()
            return

        data = self.backend.load_configuration_data(configuration_name)
        threshold_forces = data.get("threshold_forces", [0.0, 0.0])
        self.lower_threshold_var.set(str(threshold_forces[0]))
        self.upper_threshold_var.set(str(threshold_forces[1]))

        regime_count = max(1, min(5, data["regime_count"]))
        self.regime_count_dropdown.set(str(regime_count))
        self._refresh_regime_rows()

        for index, regime in enumerate(data["regimes"][:5]):
            if index >= len(self.regime_entries):
                break

            lower_bound = regime.get("lower_bound_g", 0)
            coefficients = self.backend.normalize_coefficients_for_ui(regime.get("coefficients", [0.0] * 6))
            for coefficient_var, coefficient_value in zip(self.regime_entries[index]["coefficients"], coefficients):
                coefficient_var.set(str(coefficient_value))
            self.regime_entries[index]["lower_bound"].set(str(lower_bound))

    def _refresh_regime_rows(self, event=None):
        for widget in self.regime_rows_frame.winfo_children():
            widget.destroy()

        self.regime_entries = []
        try:
            regime_count = int(self.regime_count_dropdown.get())
        except ValueError:
            regime_count = 1

        for regime_index in range(1, regime_count + 1):
            regime_frame = ttk.Frame(self.regime_rows_frame)
            regime_frame.pack(fill="x", anchor="w", pady=(0, 8))

            ttk.Label(regime_frame, text=f"Regime {regime_index}", font=("TkDefaultFont", 9, "bold")).pack(
                side="left", anchor="n", padx=(0, 12)
            )

            coeff_vars = []
            power_font = ("TkDefaultFont", 18, "italic")
            superscript_labels = {5: "𝑥⁵", 4: "𝑥⁴", 3: "𝑥³", 2: "𝑥²", 1: "𝑥", 0: ""}
            for power in [5, 4, 3, 2, 1, 0]:
                label_text = superscript_labels[power]
                entry_var = tk.StringVar(value="0")
                coeff_vars.append(entry_var)

                ttk.Entry(regime_frame, textvariable=entry_var, width=8).pack(side="left", anchor="n", padx=(0, 4))
                if label_text:
                    ttk.Label(regime_frame, text=label_text, font=power_font).pack(side="left", anchor="n", padx=(0, 6))
                if power != 0:
                    ttk.Label(regime_frame, text="+", font=power_font).pack(side="left", anchor="n", padx=(0, 6))

            lower_bound_var = tk.StringVar(value="0")
            ttk.Label(regime_frame, text="Lower bound (g):").pack(side="left", anchor="n", padx=(12, 5))
            ttk.Entry(regime_frame, textvariable=lower_bound_var, width=10).pack(side="left", anchor="n")
            self.regime_entries.append({"lower_bound": lower_bound_var, "coefficients": coeff_vars})

        # Storage convention: we keep the coefficient list in the order [c0, c1, c2, c3, c4, c5],
        # so the coefficient sits at the front of the list. This preserves a simple, stable format
        # even if we later increase the polynomial degree without needing to shift existing values.

    def _save_calibration_curve(self):
        configuration_name = self.configuration_dropdown.get().strip()
        lower_threshold_value = self.lower_threshold_var.get().strip()
        upper_threshold_value = self.upper_threshold_var.get().strip()

        if not configuration_name or configuration_name == "No selection":
            self.message_label.config(text="Please choose a configuration name before saving the calibration curve.")
            return

        if not lower_threshold_value or not upper_threshold_value:
            self.message_label.config(text="Please enter both the lower and upper threshold force values in grams.")
            return

        try:
            lower_threshold = self.backend.validate_float(lower_threshold_value, "Lower threshold force")
            upper_threshold = self.backend.validate_float(upper_threshold_value, "Upper threshold force")
        except ValueError as exc:
            self.message_label.config(text=str(exc))
            return

        if upper_threshold <= lower_threshold:
            self.message_label.config(text="Upper threshold force must be greater than the lower threshold force.")
            return

        try:
            regimes = self.backend.build_regime_payload(self.regime_entries)
        except ValueError as exc:
            self.message_label.config(text=str(exc))
            return

        try:
            self.backend.save_calibration_curve(configuration_name, [lower_threshold, upper_threshold], regimes)
        except ValueError as exc:
            self.message_label.config(text=str(exc))
            return

        self.message_label.config(text=f"Calibration curve saved for '{configuration_name}'.")
        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.configuration_dropdown.dropdown.configure(values=self._get_configuration_names())
        self.configuration_dropdown.set("No selection")
        self.lower_threshold_var.set("0")
        self.upper_threshold_var.set("0")
        self.regime_count_dropdown.set("1")
        self._refresh_regime_rows()
        self.message_label.config(text="")
