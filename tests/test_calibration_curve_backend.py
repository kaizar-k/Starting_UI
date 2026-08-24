import math

import pandas as pd

from backend.calibration_curve_backend import CalibrationCurveBackend


def test_compute_polynomial_intersection_for_linear_regimes():
    backend = CalibrationCurveBackend()

    first = [1.0, 1.0]
    second = [0.0, 2.0]

    intersection = backend.compute_polynomial_intersection(first, second)

    assert math.isclose(intersection, 1.0, rel_tol=1e-9, abs_tol=1e-9)


def test_build_regime_payload_uses_intersection_lower_bounds():
    backend = CalibrationCurveBackend()

    class FakeField:
        def __init__(self, value):
            self.value = str(value)

        def get(self):
            return self.value

    regime_entries = [
        {"lower_bound": FakeField("0"), "coefficients": [FakeField("1"), FakeField("1")]},
        {"lower_bound": FakeField("0"), "coefficients": [FakeField("0"), FakeField("2")]},
    ]

    payload = backend.build_regime_payload(regime_entries)

    assert payload[0]["lower_bound_g"] == 0.0
    assert math.isclose(payload[1]["lower_bound_g"], 1.0, rel_tol=1e-9, abs_tol=1e-9)


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