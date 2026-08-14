import json
import tkinter as tk
from tkinter import ttk

import pandas as pd

# Storage convention for calibration regime data:
# each regime is stored as {"lower_bound_g": ..., "coefficients": [aN, ..., a1, a0]}
# where the list is ordered from the highest present polynomial power down to the constant term,
# and all unused higher-order coefficients are trimmed from the left.
# For example, [1.8, -0.04, 0.0007] represents 1.8*x^2 - 0.04*x + 0.0007 and therefore maps to
# the x^2, x, and constant boxes, not the x^5, x^4, and x^3 boxes.
# This keeps the front of the list as the coefficient we most often inspect first and avoids
# reordering the stored values if the polynomial degree later increases.

from backend.dropdown_backend import DropdownData
from gui.controls.dropdown_object import DropdownObject


class AddCalibrationCurveSection(ttk.LabelFrame):
    """Section for adding a calibration curve to an existing sensor configuration."""

    def __init__(self, parent, refresh_callback=None):
        super().__init__(parent, text="Add calibration curve", padding=12)
        self.refresh_callback = refresh_callback
        self.dropdown_data = DropdownData()
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

        ttk.Label(self.top_frame, text="Threshold force (g):").pack(side="left", padx=(0, 8), anchor="n")
        self.threshold_var = tk.StringVar(value="0")
        self.threshold_entry = ttk.Entry(self.top_frame, textvariable=self.threshold_var, width=18)
        self.threshold_entry.pack(side="left", anchor="n")

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

    def _load_existing_configuration_data(self, event=None):
        configuration_name = self.configuration_dropdown.get()
        if not configuration_name or configuration_name == "No selection":
            self.threshold_var.set("0")
            self.regime_count_dropdown.set("1")
            self._refresh_regime_rows()
            return

        try:
            df = pd.read_csv(self.dropdown_data.configurations_csv_path)
        except Exception:
            self.threshold_var.set("0")
            self.regime_count_dropdown.set("1")
            self._refresh_regime_rows()
            return

        row = df[df["configuration_name"].astype(str).str.strip() == configuration_name.strip()]
        if row.empty:
            self.threshold_var.set("0")
            self.regime_count_dropdown.set("1")
            self._refresh_regime_rows()
            return

        value = row.iloc[0].get("threshold_force")
        self.threshold_var.set("0" if pd.isna(value) else str(value).strip())

        regimes_value = row.iloc[0].get("regimes")
        parsed_regimes = []
        if pd.notna(regimes_value) and str(regimes_value).strip():
            try:
                parsed_regimes = json.loads(str(regimes_value))
                if not isinstance(parsed_regimes, list):
                    parsed_regimes = []
            except Exception:
                parsed_regimes = []

        if not parsed_regimes:
            legacy_regimes = row.iloc[0].get("calibration_regimes")
            if pd.notna(legacy_regimes) and str(legacy_regimes).strip():
                parsed_regimes = [{"lower_bound_g": 0, "coefficients": [0.0] * 6}]

        regime_count = max(1, min(5, len(parsed_regimes)))
        self.regime_count_dropdown.set(str(regime_count))
        self._refresh_regime_rows()

        for index, regime in enumerate(parsed_regimes[:5]):
            if index >= len(self.regime_entries):
                break

            lower_bound = regime.get("lower_bound_g", 0)
            coefficients = regime.get("coefficients", [0.0] * 6)
            coefficients = [float(value) for value in coefficients[:6]]

            while len(coefficients) > 1 and coefficients[0] == 0:
                coefficients = coefficients[1:]

            if not coefficients:
                coefficients = [0.0]

            padded_coefficients = [0.0] * max(0, 6 - len(coefficients)) + coefficients
            for coefficient_var, coefficient_value in zip(self.regime_entries[index]["coefficients"], padded_coefficients):
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
            for power, label_text in [(5, "x^5"), (4, "x^4"), (3, "x^3"), (2, "x^2"), (1, "x"), (0, "")]:
                entry_var = tk.StringVar(value="0")
                coeff_vars.append(entry_var)

                ttk.Entry(regime_frame, textvariable=entry_var, width=8).pack(side="left", anchor="n", padx=(0, 4))
                if label_text:
                    ttk.Label(regime_frame, text=f"{label_text}").pack(side="left", anchor="n", padx=(0, 6))
                if power != 0:
                    ttk.Label(regime_frame, text="+").pack(side="left", anchor="n", padx=(0, 6))

            lower_bound_var = tk.StringVar(value="0")
            ttk.Label(regime_frame, text="Lower bound (g):").pack(side="left", anchor="n", padx=(12, 5))
            ttk.Entry(regime_frame, textvariable=lower_bound_var, width=10).pack(side="left", anchor="n")
            self.regime_entries.append({"lower_bound": lower_bound_var, "coefficients": coeff_vars})

        # Storage convention: we keep the coefficient list in the order [c0, c1, c2, c3, c4, c5],
        # so the coefficient sits at the front of the list. This preserves a simple, stable format
        # even if we later increase the polynomial degree without needing to shift existing values.

    def _validate_float_entry(self, value, field_name):
        if value is None:
            raise ValueError(f"{field_name} is required.")

        stripped = str(value).strip()
        if not stripped:
            raise ValueError(f"{field_name} cannot be empty.")

        try:
            parsed = float(stripped)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a valid number.") from exc

        return parsed

    def _save_calibration_curve(self):
        configuration_name = self.configuration_dropdown.get().strip()
        threshold_value = self.threshold_var.get().strip()

        if not configuration_name or configuration_name == "No selection":
            self.message_label.config(text="Please choose a configuration name before saving the calibration curve.")
            return

        if not threshold_value:
            self.message_label.config(text="Please enter a threshold force value in grams.")
            return

        try:
            threshold_force = self._validate_float_entry(threshold_value, "Threshold force")
        except ValueError as exc:
            self.message_label.config(text=str(exc))
            return

        if not 20 <= threshold_force <= 50:
            self.message_label.config(text="Threshold force must be a number between 20 and 50 g.")
            return

        regimes = []
        for regime_index, regime_entry in enumerate(self.regime_entries, start=1):
            lower_bound_text = regime_entry["lower_bound"].get().strip()
            try:
                lower_bound = self._validate_float_entry(lower_bound_text, f"Lower bound for regime {regime_index}")
            except ValueError as exc:
                self.message_label.config(text=str(exc))
                return

            if lower_bound < 0:
                self.message_label.config(text=f"Lower bound for regime {regime_index} must be 0 or greater.")
                return

            coefficients = []
            for coeff_index, coefficient_var in enumerate(regime_entry["coefficients"], start=1):
                try:
                    coefficient_value = self._validate_float_entry(coefficient_var.get(), f"Coefficient {coeff_index} for regime {regime_index}")
                except ValueError as exc:
                    self.message_label.config(text=str(exc))
                    return
                coefficients.append(coefficient_value)

            while len(coefficients) > 1 and coefficients[0] == 0:
                coefficients = coefficients[1:]

            if not coefficients:
                coefficients = [0.0]

            regimes.append({"lower_bound_g": lower_bound, "coefficients": coefficients})

        try:
            df = pd.read_csv(self.dropdown_data.configurations_csv_path)
        except Exception:
            self.message_label.config(text="Could not find the configuration data file.")
            return

        matches = df["configuration_name"].astype(str).str.strip() == configuration_name
        if not matches.any():
            self.message_label.config(text="The selected configuration name does not exist.")
            return

        df.loc[matches, "threshold_force"] = threshold_force
        df.loc[matches, "regimes"] = json.dumps(regimes)
        df.to_csv(self.dropdown_data.configurations_csv_path, index=False)

        self.message_label.config(text=f"Calibration curve saved for '{configuration_name}'.")
        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.configuration_dropdown.dropdown.configure(values=self._get_configuration_names())
        self.configuration_dropdown.set("No selection")
        self.threshold_var.set("0")
        self.regime_count_dropdown.set("1")
        self._refresh_regime_rows()
        self.message_label.config(text="")
