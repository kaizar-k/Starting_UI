import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd


class DropdownData:
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

        headers = [str(column).strip() for column in df.columns]
        category_names = []
        for header in headers:
            if header and header not in {"configuration_name", "calibration_regimes"}:
                category_names.append(header)

        return category_names

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

        return options_by_category
