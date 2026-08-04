# Simple tests for the sensor processing helpers.
# These checks confirm the simulation and conversion behaviour in a clear way.

from serial_interface_library.sensor_processing import (
    convert_resistance_to_force,
    simulate_resistance_readings,
)


def test_simulation_returns_expected_count():
    readings = simulate_resistance_readings(sensor_count=3, samples_per_second=2)
    assert len(readings) == 3


def test_conversion_uses_expected_formula():
    force_values = convert_resistance_to_force([100.0, 200.0])
    assert force_values == [1.0, 2.0]
