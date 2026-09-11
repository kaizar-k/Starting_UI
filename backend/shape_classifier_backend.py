"""Backend for loading the saved shape classifier and predicting one live snapshot."""

from pathlib import Path

import joblib
import pandas as pd

from backend.resistance_snapshot_backend import SENSING_POINT_COUNT


FEATURE_COLUMNS = [f"r{point_number}" for point_number in range(1, SENSING_POINT_COUNT + 1)]
MODEL_FILENAME = "model_with_shape_none.joblib"  # Change this name to load a different model from ml/models.


class ShapeClassifierBackend:
    """Loads the frozen Random Forest model and predicts shape labels from live readings."""

    def __init__(self, model_path: str | Path | None = None):
        base_dir = Path(__file__).resolve().parents[1]
        self.model_path = Path(model_path) if model_path else base_dir / "ml" / "models" / MODEL_FILENAME
        self._model = None

    def _load_model(self):
        """Load the saved classifier once, then reuse it for later button clicks."""
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            raise FileNotFoundError(f"Saved model not found: {self.model_path}")

        self._model = joblib.load(self.model_path)
        return self._model

    def predict_shape(self, relative_resistances: list[float]) -> str:
        """Return the model's predicted shape for one 12-feature resistance snapshot."""
        if len(relative_resistances) != SENSING_POINT_COUNT:
            raise ValueError(f"Expected {SENSING_POINT_COUNT} readings, got {len(relative_resistances)}.")

        feature_row = pd.DataFrame([relative_resistances], columns=FEATURE_COLUMNS)
        prediction = self._load_model().predict(feature_row)
        return str(prediction[0])