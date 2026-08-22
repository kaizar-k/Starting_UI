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


def test_save_calibration_curve_persists_area_value(tmp_path):
    configurations_path = tmp_path / "configurations.csv"
    pd.DataFrame(
        [
            {
                "configuration_name": "sensor-a",
                "AC/DC": "DC",
                "Sensor Type": "Loop",
                "Substrate": "PET",
                "Graphene": "GR113B",
                "Coating": "CAD",
                "threshold_forces": "[25.0, 200.0]",
                "regimes": '[{"lower_bound_g": 0.0, "coefficients": [1.0, 2.0]}]',
                "area": "320",
            }
        ]
    ).to_csv(configurations_path, index=False)

    backend = CalibrationCurveBackend(str(configurations_path))

    saved = backend.save_calibration_curve("sensor-a", [25.0, 200.0], [{"lower_bound_g": 0.0, "coefficients": [1.0, 2.0]}], area=380)

    assert saved is True
    saved_row = pd.read_csv(configurations_path)
    assert saved_row.loc[0, "area"] == 380.0
    assert backend.load_configuration_data("sensor-a")["area"] == 380.0