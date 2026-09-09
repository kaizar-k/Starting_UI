"""Backend for appending labelled trial snapshots to trial_data.csv."""

from pathlib import Path

import pandas as pd

from visualisation_backend.pressure_visualisation import PressureVisualisation

# The snapshot stores one resistance value per sensing point. Channel 1 on the
# physical device is reserved for the force gauge, so the 12 sensing points live
# on channels 2..13 (channel_collection indices 2..13).
SENSING_POINT_COUNT = 12

COLUMN_NAMES = (
    ["trial_ID"]
    + [f"r{point_number}" for point_number in range(1, SENSING_POINT_COUNT + 1)]
    + ["shape"]
)


class TrialSnapshotBackend:
    """Reads latest resistance values from the device and appends trial rows to CSV."""

    def __init__(self, trial_data_csv_path: str | None = None):
        base_dir = Path(__file__).resolve().parents[1]
        self.trial_data_csv_path = (
            Path(trial_data_csv_path) if trial_data_csv_path else base_dir / "data" / "trial_data.csv"
        )

    def _next_trial_id(self) -> int:
        """Return one past the highest saved trial_ID so rows stay sequentially numbered."""
        if not self.trial_data_csv_path.exists():
            return 1

        try:
            existing_df = pd.read_csv(self.trial_data_csv_path)
        except Exception:
            return 1

        if "trial_ID" not in existing_df.columns or existing_df.empty:
            return 1

        return int(existing_df["trial_ID"].max()) + 1

    def get_all_trial_ids(self) -> list[int]:
        """Return every saved trial_ID in ascending order for the removal dropdown."""
        if not self.trial_data_csv_path.exists() or self.trial_data_csv_path.stat().st_size == 0:
            return []

        try:
            existing_df = pd.read_csv(self.trial_data_csv_path)
        except Exception:
            return []

        if "trial_ID" not in existing_df.columns or existing_df.empty:
            return []

        # Convert to plain ints so the UI receives stable, sortable values.
        return sorted(int(trial_id) for trial_id in existing_df["trial_ID"].dropna().tolist())

    def get_trial_display_options(self) -> list[str]:
        """Return user-facing dropdown labels such as 'Trial 1 (circle)'."""
        if not self.trial_data_csv_path.exists() or self.trial_data_csv_path.stat().st_size == 0:
            return []

        try:
            existing_df = pd.read_csv(self.trial_data_csv_path)
        except Exception:
            return []

        if "trial_ID" not in existing_df.columns or existing_df.empty:
            return []

        options = []
        sorted_df = existing_df.sort_values("trial_ID")
        for _, row in sorted_df.iterrows():
            trial_id = int(row["trial_ID"])
            shape_value = str(row.get("shape", "")).strip()
            label = f"Trial {trial_id}"
            if shape_value:
                label += f" ({shape_value})"
            options.append(label)
        return options

    def get_latest_relative_resistances(self, device) -> list[float] | None:
        """Return the latest relative resistance of each sensing point, or None.

        The snapshot uses the same runtime baseline path as the live visualisation so
        the saved row stores the already-normalised values instead of raw ohms.
        """
        if device is None or not hasattr(device, "channel_collection"):
            return None

        relative_resistances = []
        for point_number in range(1, SENSING_POINT_COUNT + 1):
            # channel_collection index 0 is the timestamp, index 1 is the reserved
            # force-gauge channel, so sensing point n sits at index n + 1.
            channel_index = point_number + 1
            if channel_index >= len(device.channel_collection):
                return None

            channel_data = device.channel_collection[channel_index].return_raw_data()
            if not channel_data:
                return None

            latest_resistance = float(channel_data[-1])
            point_state = PressureVisualisation._get_or_create_point_state(
                channel_index,
                channel_data,
                [0.0, float("inf")],
                1.0,
            )
            if point_state is None:
                return None

            baseline_resistance = point_state["baseline_resistance"]
            relative_resistances.append(
                PressureVisualisation.get_relative_resistance_from_absolute(
                    latest_resistance,
                    baseline_resistance,
                )
            )

        return relative_resistances

    def save_snapshot(self, resistances: list[float], shape: str) -> int:
        """Append one trial row and return the trial_ID that was written."""
        if len(resistances) != SENSING_POINT_COUNT:
            raise ValueError(
                f"Expected {SENSING_POINT_COUNT} resistance values, got {len(resistances)}."
            )

        trial_id = self._next_trial_id()

        row = {"trial_ID": trial_id}
        for point_number, resistance in enumerate(resistances, start=1):
            row[f"r{point_number}"] = resistance
        row["shape"] = shape

        # Write the header when the file is new or empty so the schema always matches.
        write_header = (
            not self.trial_data_csv_path.exists()
            or self.trial_data_csv_path.stat().st_size == 0
        )
        pd.DataFrame([row], columns=COLUMN_NAMES).to_csv(
            self.trial_data_csv_path, mode="a", index=False, header=write_header
        )

        return trial_id

    def remove_trial(self, trial_id: int) -> bool:
        """Remove one saved trial row and return True when a row was deleted."""
        if not self.trial_data_csv_path.exists() or self.trial_data_csv_path.stat().st_size == 0:
            return False

        try:
            existing_df = pd.read_csv(self.trial_data_csv_path)
        except Exception:
            return False

        if "trial_ID" not in existing_df.columns or existing_df.empty:
            return False

        # Keep sparse IDs after deletion; later rows are not renumbered.
        filtered_df = existing_df[existing_df["trial_ID"] != trial_id]
        if len(filtered_df) == len(existing_df):
            return False

        filtered_df.to_csv(self.trial_data_csv_path, index=False)
        return True
