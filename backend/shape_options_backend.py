"""Backend for reading and writing the shape options used during trial data collection."""

from pathlib import Path

import pandas as pd
from natsort import natsorted, ns


class ShapeOptionsData:
    """Loads and saves the shape labels available for trial data snapshots."""

    # The CSV uses the same category/value layout as the general options file so the
    # add/remove UI logic can mirror the existing options pages.
    CATEGORY_NAME = "Shape"

    def __init__(self, shape_options_csv_path: str | None = None):
        base_dir = Path(__file__).resolve().parents[1]
        self.shape_options_csv_path = (
            Path(shape_options_csv_path) if shape_options_csv_path else base_dir / "data" / "shape_options.csv"
        )

    def get_shapes(self) -> list[str]:
        """Return the saved shape names, naturally sorted."""
        if not self.shape_options_csv_path.exists():
            return []

        try:
            df = pd.read_csv(self.shape_options_csv_path)
        except Exception:
            return []

        # Strip accidental whitespace so manually edited CSV headings remain usable.
        df.columns = [str(column).strip() for column in df.columns]
        if "category" not in df.columns or "value" not in df.columns:
            return []

        shapes = []
        for _, row in df.iterrows():
            category_name = str(row["category"]).strip()
            option_value = str(row["value"]).strip()

            if category_name != self.CATEGORY_NAME or not option_value:
                continue

            if option_value not in shapes:
                shapes.append(option_value)

        return natsorted(shapes, alg=ns.IGNORECASE)

    def save_shapes(self, shapes: list[str]) -> None:
        """Write the current shape list back to shape_options.csv."""
        # Deduplicate while keeping first-seen order so hand edits cannot multiply rows.
        unique_shapes = []
        for shape in shapes:
            option_value = str(shape).strip()
            if option_value and option_value not in unique_shapes:
                unique_shapes.append(option_value)

        df = pd.DataFrame(
            [{"category": self.CATEGORY_NAME, "value": shape} for shape in unique_shapes],
            columns=["category", "value"],
        )
        df.to_csv(self.shape_options_csv_path, index=False)
