import pandas as pd

from backend.calibration_curve_backend import CalibrationCurveBackend


def test_configuration_names_are_naturally_sorted(tmp_path):
    configurations_path = tmp_path / "configurations.csv"
    pd.DataFrame(
        [
            {"configuration_name": "10 Loops Setup"},
            {"configuration_name": "2 Loops Setup"},
            {"configuration_name": "1 Loop Setup"},
        ]
    ).to_csv(configurations_path, index=False)

    backend = CalibrationCurveBackend(str(configurations_path))

    assert backend.get_configuration_names() == [
        "No selection",
        "1 Loop Setup",
        "2 Loops Setup",
        "10 Loops Setup",
    ]