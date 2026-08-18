import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd
from natsort import natsorted, ns


class DropdownData:
    sensor_identity_columns = ["AC/DC", "Sensor Type", "Substrate", "Graphene", "Coating"]
    _ignored_config_columns = {
        "configuration_name",
        "calibration_regimes",
        "threshold_force",
        "threshold_forces",
        "regimes",
        "hysteresis_ratios",
    }

    def _get_sensor_identity_columns(self, df: pd.DataFrame) -> List[str]:
        present_columns = [column_name for column_name in self.sensor_identity_columns if column_name in df.columns]
        if present_columns:
            return present_columns

        return [
            str(column_name).strip()
            for column_name in df.columns
            if column_name and str(column_name).strip() not in self._ignored_config_columns
        ]

    def __init__(self, options_csv_path: str | None = None, configurations_csv_path: str | None = None):
        # Find the project root so the CSV files can be read from the data folder.
        base_dir = Path(__file__).resolve().parents[1]

        # Store the file paths to the two CSV files.
        self.options_csv_path = Path(options_csv_path) if options_csv_path else base_dir / "data" / "options.csv"
        self.configurations_csv_path = (
            Path(configurations_csv_path) if configurations_csv_path else base_dir / "data" / "configurations.csv"
        )

    def get_category_names(self) -> List[str]:
        """Read the category names from the configuration CSV headers."""
        if not self.configurations_csv_path.exists():
            return ["AC/DC", "Sensor Type", "Substrate", "Graphene", "Coating"]

        try:
            df = pd.read_csv(self.configurations_csv_path)
        except Exception:
            return ["AC/DC", "Sensor Type", "Substrate", "Graphene", "Coating"]

        sensor_columns = self._get_sensor_identity_columns(df)
        if sensor_columns:
            return sensor_columns

        return ["AC/DC", "Sensor Type", "Substrate", "Graphene", "Coating"]

    def get_configuration_names(self) -> List[str]:
        """Return saved configuration names naturally sorted after the placeholder."""
        if not self.configurations_csv_path.exists():
            return ["No selection"]

        try:
            df = pd.read_csv(self.configurations_csv_path)
        except Exception:
            return ["No selection"]

        if "configuration_name" not in df.columns:
            return ["No selection"]

        names = df["configuration_name"].fillna("").astype(str).str.strip().tolist()
        unique_names = []
        for name in names:
            if name and name not in unique_names:
                unique_names.append(name)

        return ["No selection"] + natsorted(unique_names, alg=ns.IGNORECASE)

    def get_options_by_category(self) -> Dict[str, List[str]]:
        """Read the options from options.csv and group them by category."""
        if not self.options_csv_path.exists():
            return {}

        try:
            df = pd.read_csv(self.options_csv_path)
        except Exception:
            return {}

        options_by_category: Dict[str, List[str]] = {}

        for _, row in df.iterrows():
            category_name = str(row["category"]).strip()
            option_value = str(row["value"]).strip()

            if not category_name or not option_value:
                continue

            if category_name not in options_by_category:
                options_by_category[category_name] = []

            if option_value not in options_by_category[category_name]:
                options_by_category[category_name].append(option_value)

        for category_name, values in options_by_category.items():
            options_by_category[category_name] = natsorted(values, alg=ns.IGNORECASE)

        return options_by_category

    def get_used_options_by_category(self) -> Dict[str, List[str]]:
        """Return the option values that are currently referenced by saved configurations."""
        if not self.configurations_csv_path.exists():
            return {}

        try:
            df = pd.read_csv(self.configurations_csv_path)
        except Exception:
            return {}

        used_options_by_category: Dict[str, List[str]] = {}
        for column_name in self._get_sensor_identity_columns(df):
            values = []
            for value in df[column_name].dropna():
                option_value = str(value).strip()
                if option_value and option_value not in values:
                    values.append(option_value)

            if values:
                used_options_by_category[column_name] = natsorted(values, alg=ns.IGNORECASE)

        return used_options_by_category

    def get_configuration_values_by_name(self, configuration_name: str) -> Dict[str, str]:
        """Return the full row for a configuration preset, keyed by column name."""
        if not configuration_name:
            return {}

        if not self.configurations_csv_path.exists():
            return {}

        try:
            df = pd.read_csv(self.configurations_csv_path)
        except Exception:
            return {}

        matching_row = df[df["configuration_name"].astype(str).str.strip() == configuration_name.strip()]
        if matching_row.empty:
            return {}

        row = matching_row.iloc[0].to_dict()
        return {str(key).strip(): "" if pd.isna(value) else str(value).strip() for key, value in row.items()}

    def find_configuration_name_for_values(self, selected_values: Dict[str, str]) -> str | None:
        """Return the preset name whose column values match the provided selected values."""
        if not self.configurations_csv_path.exists():
            return None

        try:
            df = pd.read_csv(self.configurations_csv_path)
        except Exception:
            return None

        if df.empty:
            return None

        candidate_columns = self._get_sensor_identity_columns(df)

        for _, row in df.iterrows():
            matches = True
            for column_name in candidate_columns:
                if column_name not in selected_values:
                    continue
                actual_value = str(row.get(column_name, "")).strip()
                expected_value = str(selected_values[column_name]).strip()
                if actual_value != expected_value:
                    matches = False
                    break

            if matches:
                name_value = str(row.get("configuration_name", "")).strip()
                if name_value:
                    return name_value

        return None

    def delete_configuration_by_name(self, configuration_name: str) -> bool:
        """Delete the configuration preset with the given name and return whether it existed."""
        if not configuration_name:
            return False

        if not self.configurations_csv_path.exists():
            return False

        try:
            df = pd.read_csv(self.configurations_csv_path)
        except Exception:
            return False

        original_count = len(df)
        filtered_df = df[df["configuration_name"].astype(str).str.strip() != configuration_name.strip()]

        if len(filtered_df) == original_count:
            return False

        filtered_df.to_csv(self.configurations_csv_path, index=False)
        return True

    def save_options_by_category(self, options_by_category: Dict[str, List[str]]) -> None:
        """Write the current options mapping back to options.csv."""
        # Convert the in-memory category->options mapping into row-based CSV data.
        rows = []
        for category_name, options in options_by_category.items():
            for option_value in options:
                rows.append({"category": category_name, "value": option_value})

        # Save the rows to disk so the values persist after closing the app.
        df = pd.DataFrame(rows, columns=["category", "value"])
        df.to_csv(self.options_csv_path, index=False)
