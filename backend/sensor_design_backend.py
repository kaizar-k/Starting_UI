"""Backend for choosing and storing per-layer sensor designs.

The sensor design will eventually encode the coordinates of each sensing point,
which in turn determines the 2D/3D visualisation layout and point count.
"""

import json
import math
from pathlib import Path

import pandas as pd
from natsort import natsorted, ns


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

        # Strip accidental whitespace so manually edited CSV headings remain usable.
        df.columns = [str(column).strip() for column in df.columns]
        if "Sensor Design" not in df.columns:
            return []

        # Drop duplicates, then naturally sort names for user-facing dropdowns.
        options = []
        for value in df["Sensor Design"].dropna():
            option_value = str(value).strip()
            if option_value and option_value not in options:
                options.append(option_value)

        return natsorted(options, alg=ns.IGNORECASE)

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
            return pd.DataFrame(columns=["Sensor Design", "Dimensions", "Sensing Points"])

        df = pd.read_csv(self.design_data_csv_path)
        df.columns = [str(column).strip() for column in df.columns]
        for column_name in ["Sensor Design", "Dimensions", "Sensing Points"]:
            if column_name not in df.columns:
                df[column_name] = ""
        return df[["Sensor Design", "Dimensions", "Sensing Points"]]

    def add_sensor_design(
        self,
        sensor_design_name: str,
        dimensions: list,
        sensing_points: list,
    ) -> None:
        """Add a sensor design after its dimensions and sensing-point geometry are validated."""
        sensor_design_name = sensor_design_name.strip()
        if not sensor_design_name:
            raise ValueError("Sensor design name cannot be empty.")

        validated_dimensions = self.build_dimensions_payload(dimensions[0], dimensions[1])
        validated_sensing_points = self.validate_sensing_points(sensing_points, validated_dimensions)

        df = self._read_design_data_df()
        if "Sensor Design" in df.columns and sensor_design_name in df["Sensor Design"].astype(str).str.strip().values:
            raise ValueError(f"Sensor design '{sensor_design_name}' already exists.")

        new_row = pd.DataFrame(
            [{
                "Sensor Design": sensor_design_name,
                "Dimensions": json.dumps(validated_dimensions),
                "Sensing Points": json.dumps(validated_sensing_points),
            }]
        )
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
            numeric_value = float(stripped)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a valid number.") from exc

        if not math.isfinite(numeric_value):
            raise ValueError(f"{field_name} must be a finite number.")
        return numeric_value

    @staticmethod
    def parse_optional_float(value, field_name: str) -> float:
        """Treat blank strings as zero so optional geometry fields are easy to leave empty."""
        if value is None:
            return 0.0

        if hasattr(value, "get"):
            value = value.get()

        stripped = str(value).strip()
        if stripped == "":
            return 0.0
        return SensorDesignBackend.validate_float(stripped, field_name)

    @staticmethod
    def get_field_value(entry, field_name: str):
        """Support both Tkinter StringVar objects and plain numeric/string values."""
        if entry is None:
            return ""
        if hasattr(entry, "get"):
            return entry.get()
        return entry

    def build_dimensions_payload(self, width, height) -> list:
        """Validate and return the design dimensions in [width, height] order."""
        width_value = self.validate_float(width, "Width")
        height_value = self.validate_float(height, "Height")
        if width_value <= 0 or height_value <= 0:
            raise ValueError("Width and height must be greater than zero.")
        return [width_value, height_value]

    def build_sensing_point_payload(self, sensing_point_entries) -> list:
        """Collect raw sensing-point fields from the form for later validation."""
        sensing_points = []
        for point_index, point_entry in enumerate(sensing_point_entries, start=1):
            point_data = {
                "x": self.validate_float(
                    self.get_field_value(point_entry["x"], f"X-coordinate for sensing point {point_index}"),
                    f"X-coordinate for sensing point {point_index}",
                ),
                "y": self.validate_float(
                    self.get_field_value(point_entry["y"], f"Y-coordinate for sensing point {point_index}"),
                    f"Y-coordinate for sensing point {point_index}",
                ),
                "radius_outer": self.parse_optional_float(
                    self.get_field_value(point_entry["radius_outer"], f"Outer radius for sensing point {point_index}"),
                    f"Outer radius for sensing point {point_index}",
                ),
                "radius_inner": self.parse_optional_float(
                    self.get_field_value(point_entry["radius_inner"], f"Inner radius for sensing point {point_index}"),
                    f"Inner radius for sensing point {point_index}",
                ),
                "area": self.parse_optional_float(
                    self.get_field_value(point_entry["area"], f"Sensor area for sensing point {point_index}"),
                    f"Sensor area for sensing point {point_index}",
                ),
            }
            sensing_points.append(point_data)
        return sensing_points

    def validate_sensing_points(self, sensing_points: list, dimensions: list) -> list:
        """Ensure every sensing area fits inside the rectangular design."""
        width, height = self.build_dimensions_payload(dimensions[0], dimensions[1])
        if not sensing_points:
            raise ValueError("At least one sensing point is required.")

        validated_points = []
        for point_index, sensing_point in enumerate(sensing_points, start=1):
            x_value = self.validate_float(sensing_point["x"], f"X-coordinate for sensing point {point_index}")
            y_value = self.validate_float(sensing_point["y"], f"Y-coordinate for sensing point {point_index}")
            radius_outer = self.parse_optional_float(
                sensing_point.get("radius_outer", 0.0), f"Outer radius for sensing point {point_index}"
            )
            radius_inner = self.parse_optional_float(
                sensing_point.get("radius_inner", 0.0), f"Inner radius for sensing point {point_index}"
            )
            area_value = self.parse_optional_float(
                sensing_point.get("area", 0.0), f"Sensor area for sensing point {point_index}"
            )

            has_ring_geometry = radius_outer > 0 or radius_inner > 0
            has_area_geometry = area_value > 0

            if has_ring_geometry and has_area_geometry:
                raise ValueError("sensor area not needed if inner and outer radii provided")

            if not has_ring_geometry and not has_area_geometry:
                raise ValueError(
                    f"Provide a positive outer radius or a positive sensor area for sensing point {point_index}."
                )

            if has_ring_geometry:
                if radius_outer <= 0:
                    raise ValueError(f"Outer radius for sensing point {point_index} must be greater than zero.")
                if radius_inner < 0:
                    raise ValueError(f"Inner radius for sensing point {point_index} cannot be negative.")
                if radius_inner >= radius_outer:
                    raise ValueError(f"Inner radius for sensing point {point_index} must be smaller than the outer radius.")
                if x_value - radius_outer < 0 or x_value + radius_outer > width:
                    raise ValueError(f"Sensing point {point_index} extends beyond the design width.")
                if y_value - radius_outer < 0 or y_value + radius_outer > height:
                    raise ValueError(f"Sensing point {point_index} extends beyond the design height.")
                area_value = math.pi * (radius_outer ** 2 - radius_inner ** 2)

            if has_area_geometry and area_value <= 0:
                raise ValueError(f"Sensor area for sensing point {point_index} must be greater than zero.")

            validated_points.append({
                "x": x_value,
                "y": y_value,
                "radius_outer": radius_outer,
                "radius_inner": radius_inner,
                "area": area_value,
            })

        return validated_points

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
