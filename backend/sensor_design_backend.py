"""Backend for choosing and storing per-layer sensor designs.

The sensor design will eventually encode the coordinates of each sensing point,
which in turn determines the 2D/3D visualisation layout and point count.
"""

import json
from pathlib import Path

import pandas as pd


class SensorDesignBackend:
    """Stores the selected sensor type for each layer, in layer order."""

    def __init__(self, design_data_csv_path: str | None = None):
        base_dir = Path(__file__).resolve().parents[1]
        self.design_data_csv_path = (
            Path(design_data_csv_path) if design_data_csv_path else base_dir / "data" / "design_data.csv"
        )
        # Selections are kept in memory only, keyed by layer number.
        self.layer_sensor_types = {}

    def get_sensor_type_options(self) -> list:
        # No CSV yet means no sensor designs are available to choose from.
        if not self.design_data_csv_path.exists():
            return []

        try:
            df = pd.read_csv(self.design_data_csv_path)
        except Exception:
            return []

        # The header in design_data.csv has a leading space ("Sensor Design, Coordinates"), so strip it.
        df.columns = [str(column).strip() for column in df.columns]
        if "Sensor Design" not in df.columns:
            return []

        # Preserve CSV row order and drop duplicates so the dropdown list stays clean.
        options = []
        for value in df["Sensor Design"].dropna():
            option_value = str(value).strip()
            if option_value and option_value not in options:
                options.append(option_value)

        return options

    def set_layer_sensor_type(self, layer_number: int, sensor_type: str):
        self.layer_sensor_types[layer_number] = sensor_type

    def get_layer_sensor_type(self, layer_number: int) -> str | None:
        return self.layer_sensor_types.get(layer_number)

    def get_ordered_sensor_types(self, layer_count: int) -> list:
        """Return the selected sensor type for each layer, from layer 1 to layer_count."""
        # Layers without a saved selection default to "No selection" instead of being omitted.
        return [self.layer_sensor_types.get(layer_number, "No selection") for layer_number in range(1, layer_count + 1)]

    def _read_design_data_df(self) -> pd.DataFrame:
        # Return an empty frame with the expected columns when the CSV doesn't exist yet.
        if not self.design_data_csv_path.exists():
            return pd.DataFrame(columns=["Sensor Design", "Coordinates"])

        df = pd.read_csv(self.design_data_csv_path)
        df.columns = [str(column).strip() for column in df.columns]
        return df

    def add_sensor_design(self, sensor_design_name: str, coordinates: list | None = None) -> None:
        """Add a new sensor design row with the given coordinates (or blank if none provided)."""
        sensor_design_name = sensor_design_name.strip()
        if not sensor_design_name:
            raise ValueError("Sensor design name cannot be empty.")

        df = self._read_design_data_df()
        if "Sensor Design" in df.columns and sensor_design_name in df["Sensor Design"].astype(str).str.strip().values:
            raise ValueError(f"Sensor design '{sensor_design_name}' already exists.")

        # Coordinates are stored as a JSON list of [x, y] pairs so any point count can be represented.
        coordinates_value = json.dumps(coordinates) if coordinates else ""
        new_row = pd.DataFrame([{"Sensor Design": sensor_design_name, "Coordinates": coordinates_value}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.design_data_csv_path, index=False)

    # @staticmethod means this method doesn't receive self and doesn't touch any instance data,
    # so it behaves like a plain function that just happens to live inside the class for organisation.
    # It's still called as self.validate_float(...) or SensorDesignBackend.validate_float(...).
    @staticmethod
    def validate_float(value, field_name: str) -> float:
        stripped = str(value).strip()
        if not stripped:
            raise ValueError(f"{field_name} cannot be empty.")

        try:
            return float(stripped)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a valid number.") from exc

    def build_coordinate_payload(self, coordinate_entries) -> list:
        """Validate and collect the [x, y] pairs entered for each coordinate row."""
        coordinates = []
        for coordinate_index, coordinate_entry in enumerate(coordinate_entries, start=1):
            x_value = self.validate_float(coordinate_entry["x"].get(), f"X-coordinate for coordinate {coordinate_index}")
            y_value = self.validate_float(coordinate_entry["y"].get(), f"Y-coordinate for coordinate {coordinate_index}")
            coordinates.append([x_value, y_value])

        return coordinates

    def remove_sensor_design(self, sensor_design_name: str) -> bool:
        """Remove the sensor design row with the given name. Returns whether it existed."""
        df = self._read_design_data_df()
        if df.empty or "Sensor Design" not in df.columns:
            return False

        original_count = len(df)
        filtered_df = df[df["Sensor Design"].astype(str).str.strip() != sensor_design_name.strip()]

        if len(filtered_df) == original_count:
            return False

        filtered_df.to_csv(self.design_data_csv_path, index=False)
        return True
