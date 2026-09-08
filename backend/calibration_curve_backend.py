import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from backend.dropdown_backend import DropdownData


class CalibrationCurveBackend:
    """Backend helpers for calibration-curve validation, loading, and persistence."""

    def __init__(self, configurations_csv_path: str | None = None):
        base_dir = Path(__file__).resolve().parents[1]
        self.configurations_csv_path = (
            Path(configurations_csv_path) if configurations_csv_path else base_dir / "data" / "configurations.csv"
        )

    def _normalize_threshold_forces_column(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        if "threshold_force" in df.columns and "threshold_forces" not in df.columns:
            df = df.rename(columns={"threshold_force": "threshold_forces"})

        if "threshold_forces" not in df.columns:
            return df

        for index, value in df["threshold_forces"].items():
            if pd.isna(value) or str(value).strip() in ("", "nan", "NaN"):
                continue

            try:
                parsed = json.loads(str(value))
            except Exception:
                parsed = str(value).strip()

            if isinstance(parsed, list) and len(parsed) >= 2:
                df.at[index, "threshold_forces"] = json.dumps([float(parsed[0]), float(parsed[1])])
            elif isinstance(parsed, (int, float)):
                df.at[index, "threshold_forces"] = json.dumps([float(parsed), float(parsed)])
            elif isinstance(parsed, str):
                try:
                    numeric_value = float(parsed)
                except ValueError:
                    continue
                df.at[index, "threshold_forces"] = json.dumps([numeric_value, numeric_value])

        return df

    def _read_configurations_df(self) -> pd.DataFrame:
        if not self.configurations_csv_path.exists():
            return pd.DataFrame()

        df = pd.read_csv(self.configurations_csv_path)
        return self._normalize_threshold_forces_column(df)

    def get_configuration_names(self):
        return DropdownData(configurations_csv_path=str(self.configurations_csv_path)).get_configuration_names()

    def load_configuration_data(self, configuration_name: str):
        if not configuration_name or configuration_name == "No selection":
            return {"threshold_forces": [0.0, 0.0], "regimes": [], "regime_count": 1, "area": 836.0}

        try:
            df = self._read_configurations_df()
        except Exception:
            return {"threshold_forces": [0.0, 0.0], "regimes": [], "regime_count": 1, "area": 836.0}

        row = df[df["configuration_name"].astype(str).str.strip() == configuration_name.strip()]
        if row.empty:
            return {"threshold_forces": [0.0, 0.0], "regimes": [], "regime_count": 1, "area": 836.0}

        row = row.iloc[0]

        threshold_value = row.get("threshold_forces")
        if pd.isna(threshold_value) or threshold_value in (None, ""):
            legacy_threshold = row.get("threshold_force")
            if pd.notna(legacy_threshold) and str(legacy_threshold).strip():
                threshold_value = str(legacy_threshold).strip()

        threshold_forces = [0.0, 0.0]
        if pd.notna(threshold_value) and str(threshold_value).strip():
            try:
                parsed_thresholds = json.loads(str(threshold_value))
                if isinstance(parsed_thresholds, list) and len(parsed_thresholds) >= 2:
                    threshold_forces = [float(parsed_thresholds[0]), float(parsed_thresholds[1])]
                elif isinstance(parsed_thresholds, (int, float)):
                    threshold_forces = [float(parsed_thresholds), float(parsed_thresholds)]
            except Exception:
                raw_parts = str(threshold_value).strip().strip('[]()')
                pieces = [piece.strip() for piece in raw_parts.split(',') if piece.strip()]
                if len(pieces) >= 2:
                    try:
                        threshold_forces = [float(pieces[0]), float(pieces[1])]
                    except Exception:
                        threshold_forces = [0.0, 0.0]

        area_value = row.get("area")
        area = 836.0
        if pd.notna(area_value) and str(area_value).strip():
            try:
                area = float(str(area_value).strip())
            except ValueError:
                area = 836.0

        max_force = float(threshold_forces[1]) if len(threshold_forces) >= 2 else 0.0
        max_pressure = 0.0
        if area > 0:
            max_pressure = (max_force / area) * 9806.65

        regimes_value = row.get("regimes")
        parsed_regimes = []
        if pd.notna(regimes_value) and str(regimes_value).strip():
            try:
                parsed_regimes = json.loads(str(regimes_value))
                if not isinstance(parsed_regimes, list):
                    parsed_regimes = []
            except Exception:
                parsed_regimes = []

        if not parsed_regimes:
            legacy_regimes = row.get("calibration_regimes")
            if pd.notna(legacy_regimes) and str(legacy_regimes).strip():
                parsed_regimes = [{"lower_bound_g": 0, "coefficients": [0.0] * 6}]

        # This is the in-memory runtime structure used by the rest of the app after a config has
        # been loaded from the CSV. It keeps the ordered list of calibration regimes together so the
        # code can classify each live resistance reading against the correct regime in sequence.
        regime_count = max(1, min(5, len(parsed_regimes)))
        return {
            "threshold_forces": threshold_forces,
            "regimes": parsed_regimes[:5],
            "regime_count": regime_count,
            "area": area,
            "max_pressure": max_pressure,
        }

    # @staticmethod means this method doesn't receive self and doesn't touch any instance data,
    # so it behaves like a plain function that just happens to live inside the class for organisation.
    # It's still called as self.validate_float(...) or CalibrationCurveBackend.validate_float(...).
    @staticmethod
    def validate_float(value, field_name: str) -> float:
        if value is None:
            raise ValueError(f"{field_name} is required.")

        stripped = str(value).strip()
        if not stripped:
            raise ValueError(f"{field_name} cannot be empty.")

        try:
            return float(stripped)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a valid number.") from exc

    def normalize_coefficients_for_ui(self, coefficients):
        cleaned = self._normalise_polynomial_coefficients(coefficients[:6] if coefficients else [0.0])
        return [0.0] * max(0, 6 - len(cleaned)) + cleaned

    @staticmethod
    def _normalise_polynomial_coefficients(coefficients):
        # Coefficients are stored highest-power first (e.g. [a2, a1, a0] for a quadratic),
        # which is the same convention expected by numpy.poly1d/polyval/roots.
        if coefficients is None:
            return [0.0]

        cleaned = [float(value) for value in coefficients]
        if not cleaned:
            return [0.0]

        while len(cleaned) > 1 and abs(cleaned[0]) < 1e-12:
            cleaned = cleaned[1:]

        return cleaned if cleaned else [0.0]

    def compute_polynomial_intersection(self, previous_coefficients, current_coefficients, previous_lower_bound=0.0):
        previous_coefficients = self._normalise_polynomial_coefficients(previous_coefficients)
        current_coefficients = self._normalise_polynomial_coefficients(current_coefficients)

        previous_poly = np.poly1d(previous_coefficients)
        current_poly = np.poly1d(current_coefficients)
        difference_poly = previous_poly - current_poly

        roots = np.roots(difference_poly.coeffs)
        valid_roots = []
        for root in roots:
            if abs(root.imag) > 1e-9:
                continue

            real_root = float(root.real)
            if not math.isfinite(real_root):
                continue

            if real_root > previous_lower_bound:
                valid_roots.append(real_root)

        if not valid_roots:
            raise ValueError("No valid intersection was found for the adjacent calibration regimes.")

        return min(valid_roots)

    def build_regime_payload(self, regime_entries):
        # Regimes are stored in a list, not a dictionary, because order matters. The runtime code
        # compares each regime in sequence to find the active regime for a new resistance reading.
        regimes = []
        previous_lower_bound = 0.0
        for regime_index, regime_entry in enumerate(regime_entries, start=1):
            if regime_index == 1:
                lower_bound = 0.0
            else:
                previous_coefficients = self._normalise_polynomial_coefficients(regimes[-1]["coefficients"])
                current_coefficients = []
                for coeff_index, coefficient_var in enumerate(regime_entry["coefficients"], start=1):
                    coefficient_value = self.validate_float(
                        coefficient_var.get(),
                        f"Coefficient {coeff_index} for regime {regime_index}",
                    )
                    current_coefficients.append(coefficient_value)
                current_coefficients = self._normalise_polynomial_coefficients(current_coefficients)
                lower_bound = self.compute_polynomial_intersection(
                    previous_coefficients,
                    current_coefficients,
                    previous_lower_bound=previous_lower_bound,
                )

            if lower_bound < 0:
                raise ValueError(f"Lower bound for regime {regime_index} must be 0 or greater.")

            if regime_index > 1 and lower_bound <= previous_lower_bound:
                raise ValueError(
                    f"Lower bound for regime {regime_index} must be greater than the lower bound of the previous regime."
                )

            coefficients = []
            for coeff_index, coefficient_var in enumerate(regime_entry["coefficients"], start=1):
                coefficient_value = self.validate_float(
                    coefficient_var.get(),
                    f"Coefficient {coeff_index} for regime {regime_index}",
                )
                coefficients.append(coefficient_value)

            while len(coefficients) > 1 and coefficients[0] == 0:
                coefficients = coefficients[1:]

            if not coefficients:
                coefficients = [0.0]

            # Final runtime payload shape: every regime is a dict containing the lower force boundary
            # for that regime and the polynomial coefficients for the resistance-vs-force curve.
            regimes.append({"lower_bound_g": lower_bound, "coefficients": coefficients})
            previous_lower_bound = lower_bound

        return regimes

    def save_calibration_curve(self, configuration_name: str, threshold_forces, regimes, area: float | str | None = None):
        df = self._read_configurations_df()
        if df.empty or "configuration_name" not in df.columns:
            raise ValueError("Could not find the configuration data file.")

        matches = df["configuration_name"].astype(str).str.strip() == configuration_name
        if not matches.any():
            raise ValueError("The selected configuration name does not exist.")

        if not isinstance(threshold_forces, (list, tuple)) or len(threshold_forces) != 2:
            raise ValueError("Threshold forces must contain both a lower and upper value.")

        if area is not None:
            validated_area = self.validate_float(area, "Force applicator area")
            if validated_area <= 0:
                raise ValueError("Force applicator area must be greater than zero.")
            if "area" not in df.columns:
                df["area"] = None
            df.loc[matches, "area"] = float(validated_area)

        # Persist the runtime calibration payload to the CSV as JSON text. This is the filesystem
        # format, while the Python code uses the parsed dict/list version in memory.
        df.loc[matches, "threshold_forces"] = json.dumps([float(threshold_forces[0]), float(threshold_forces[1])])
        df.loc[matches, "regimes"] = json.dumps(regimes)
        df.to_csv(self.configurations_csv_path, index=False)
        return True

    def remove_calibration_curve(self, configuration_name: str):
        df = self._read_configurations_df()
        if df.empty or "configuration_name" not in df.columns:
            raise ValueError("Could not find the configuration data file.")

        matches = df["configuration_name"].astype(str).str.strip() == configuration_name
        if not matches.any():
            raise ValueError("The selected configuration name does not exist.")

        # The CSV loader infers numeric columns like threshold_force as float64.
        # pandas refuses to assign an empty string to a float64 column because it can't represent
        # that value cleanly, which caused the tracebacks we were seeing.
        # Converting those columns to object before clearing them allows the saved CSV to keep a blank
        # value while preserving the rest of the row data.
        if "threshold_forces" in df.columns:
            df["threshold_forces"] = df["threshold_forces"].astype("object")
            df.loc[matches, "threshold_forces"] = ""
        elif "threshold_force" in df.columns:
            df["threshold_force"] = df["threshold_force"].astype("object")
            df.loc[matches, "threshold_force"] = ""

        if "regimes" in df.columns:
            df["regimes"] = df["regimes"].astype("object")
            df.loc[matches, "regimes"] = ""

        df.to_csv(self.configurations_csv_path, index=False)
        return True
