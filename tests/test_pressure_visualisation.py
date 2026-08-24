import math

from visualisation_backend.pressure_visualisation import PressureVisualisation


def test_relative_resistance_round_trip_to_force():
    target_relative_resistance = 2.5
    force = PressureVisualisation.solve_force_from_relative_resistance([2.0, 1.0], target_relative_resistance)

    assert math.isclose(force, 0.75, rel_tol=1e-9, abs_tol=1e-9)


def test_force_solver_filters_to_force_bounds_when_two_positive_roots_exist():
    # x^2 - 5x + 6 = 2 has roots x=1 and x=4. Only x=4 lies inside [3, 5].
    force = PressureVisualisation.solve_force_from_relative_resistance(
        [1.0, -5.0, 6.0],
        2.0,
        lower_force_bound=3.0,
        upper_force_bound=5.0,
    )
    assert math.isclose(force, 4.0, rel_tol=1e-9, abs_tol=1e-9)


def test_regime_selection_supports_decreasing_relative_boundaries():
    runtime_regimes = [
        {"relative_boundary_resistance": 0.916173497668656},
        {"relative_boundary_resistance": 0.6639638483112686},
    ]

    # A near-baseline relative value should stay in regime 0 for decreasing curves.
    regime_index = PressureVisualisation.get_regime_index_for_relative_resistance(0.98, runtime_regimes)
    assert regime_index == 0

    # A lower relative value should move into regime 1 once below the second boundary.
    regime_index = PressureVisualisation.get_regime_index_for_relative_resistance(0.60, runtime_regimes)
    assert regime_index == 1


class _FakeChannel:
    def __init__(self, samples):
        self._samples = list(samples)

    def return_raw_data(self):
        return self._samples


class _FakeDevice:
    def __init__(self, channel_collection):
        self.channel_collection = channel_collection


def test_pressure_for_all_points_uses_startup_baseline_cache():
    PressureVisualisation.reset_runtime_state()

    regimes = [
        {"lower_bound_g": 0.0, "coefficients": [1.0, 1.0]},
        {"lower_bound_g": 2.0, "coefficients": [0.5, 1.0]},
    ]
    calibration_data = {
        "threshold_forces": [0.0, 10.0],
        "regimes": regimes,
    }

    # Time channel index 0 is unused here; sensor channel 1 includes a seeded 0.0 then startup samples.
    first_samples = [0.0, 100.0, 101.0, 99.0, 100.0, 100.0, 101.0, 99.0, 100.0, 100.0, 100.0, 130.0]
    device = _FakeDevice([_FakeChannel([0]), _FakeChannel(first_samples)])

    pressure_by_point = PressureVisualisation.get_pressure_for_all_points(
        active_device=device,
        channel_map={1: [1]},
        calibration_data=calibration_data,
        area=380.0,
    )

    assert pressure_by_point[1][0] is not None

    point_state = PressureVisualisation._runtime_point_state[1]
    assert math.isclose(point_state["baseline_resistance"], 100.0, rel_tol=1e-9, abs_tol=1e-9)

    # Baseline must stay fixed once initialised, even if later samples drift.
    baseline_before = point_state["baseline_resistance"]
    device.channel_collection[1] = _FakeChannel(first_samples + [180.0, 190.0, 200.0])
    PressureVisualisation.get_pressure_for_all_points(
        active_device=device,
        channel_map={1: [1]},
        calibration_data=calibration_data,
        area=380.0,
    )
    baseline_after = PressureVisualisation._runtime_point_state[1]["baseline_resistance"]
    assert math.isclose(baseline_before, baseline_after, rel_tol=1e-9, abs_tol=1e-9)


def test_pressure_for_point_uses_runtime_regime_boundaries():
    regimes = [
        {"lower_bound_g": 0.0, "coefficients": [1.0, 2.0]},
        {"lower_bound_g": 5.0, "coefficients": [1.0, 3.0]},
    ]

    baseline_resistance = 100.0
    absolute_resistance = 240.0
    relative_resistance = absolute_resistance / baseline_resistance
    assert relative_resistance == 2.4

    pressure = PressureVisualisation.get_pressure_for_point(
        absolute_resistance=absolute_resistance,
        baseline_resistance=baseline_resistance,
        regimes=regimes,
        area=380.0,
    )

    assert pressure > 0
    assert pressure < 1.0
