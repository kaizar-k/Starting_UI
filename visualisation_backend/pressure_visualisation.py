# Converts a live resistance reading into the active force regime and then into a pressure value.
# The calibration polynomials are treated as force-to-relative-resistance curves, so the runtime
# process is: absolute resistance -> relative resistance -> regime lookup -> polynomial inversion -> force -> pressure.

import math
import json

import numpy as np


class PressureVisualisation:
    """Runtime conversion helpers for resistance, force, and pressure."""

    # Runtime cache (RAM only) used while a stream is active.
    _runtime_states = {}
    _runtime_signature = None
    _runtime_regimes = []
    _runtime_point_state = {}
    _runtime_pending_baselines = {}
    _baseline_window_size = 10

    @staticmethod
    def reset_runtime_state():
        """Clear all cached runtime state so the next call re-initialises baselines."""
        PressureVisualisation._runtime_states = {}
        PressureVisualisation._runtime_signature = None
        PressureVisualisation._runtime_regimes = []
        PressureVisualisation._runtime_point_state = {}
        PressureVisualisation._runtime_pending_baselines = {}

    @staticmethod
    def rebase_runtime_state(baselines):
        """Set live baselines to captured readings without interrupting the device stream."""
        for channel_number, baseline in baselines.items():
            try:
                baseline = float(baseline)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(baseline) or baseline <= 0:
                continue

            state = PressureVisualisation._runtime_point_state.get(channel_number)
            if state is None:
                # Preserve the instantaneous value until pressure processing creates its state.
                PressureVisualisation._runtime_pending_baselines[channel_number] = baseline
                continue

            state["baseline_resistance"] = baseline
            state["previous_force"] = None
            for regime in state.get("regimes", []):
                regime["absolute_boundary_resistance"] = float(
                    baseline * regime["relative_boundary_resistance"]
                )

    @staticmethod
    def _normalise_polynomial(coefficients):
        if coefficients is None:
            return [0.0]

        cleaned = [float(value) for value in coefficients]
        if not cleaned:
            return [0.0]

        while len(cleaned) > 1 and abs(cleaned[0]) < 1e-12:
            cleaned = cleaned[1:]

        return cleaned if cleaned else [0.0]

    @staticmethod
    def _build_runtime_signature(calibration_data, area):
        # If calibration payload changes, the point cache must be rebuilt to keep boundaries valid.
        payload = {
            "regimes": calibration_data.get("regimes", []),
            "threshold_forces": calibration_data.get("threshold_forces", [0.0, 0.0]),
            "area": float(area),
        }
        return json.dumps(payload, sort_keys=True)

    @staticmethod
    def _build_runtime_regimes(regimes, threshold_forces):
        runtime_regimes = []
        if not regimes:
            return runtime_regimes

        upper_threshold = float(threshold_forces[1]) if len(threshold_forces) >= 2 else float("inf")
        for index, regime in enumerate(regimes):
            lower_bound_g = float(regime.get("lower_bound_g", 0.0))
            if index < len(regimes) - 1:
                upper_bound_g = float(regimes[index + 1].get("lower_bound_g", lower_bound_g))
            else:
                upper_bound_g = upper_threshold

            coefficients = PressureVisualisation._normalise_polynomial(regime.get("coefficients", []))
            relative_boundary = PressureVisualisation.evaluate_polynomial(coefficients, lower_bound_g)
            runtime_regimes.append(
                {
                    "lower_bound_g": lower_bound_g,
                    "upper_bound_g": upper_bound_g,
                    "coefficients": coefficients,
                    "relative_boundary_resistance": float(relative_boundary),
                }
            )
        return runtime_regimes

    @staticmethod
    def _extract_startup_baseline(samples, window_size):
        # Channels are seeded with a startup 0.0 value before live data arrives; skip that placeholder.
        numeric = [float(value) for value in samples if math.isfinite(float(value))]
        if len(numeric) > 1 and abs(numeric[0]) < 1e-12:
            numeric = numeric[1:]

        if len(numeric) < window_size:
            return None

        startup_window = numeric[:window_size]
        baseline = float(sum(startup_window) / window_size)
        if baseline <= 0:
            return None
        return baseline

    @staticmethod
    def _ensure_runtime_ready(calibration_data, area):
        signature = PressureVisualisation._build_runtime_signature(calibration_data, area)
        # Keep an independent cache per calibration signature so switching layers/configurations
        # does not wipe baselines that were already established for other signatures.
        if signature not in PressureVisualisation._runtime_states:
            PressureVisualisation._runtime_states[signature] = {
                "regimes": PressureVisualisation._build_runtime_regimes(
                    calibration_data.get("regimes", []),
                    calibration_data.get("threshold_forces", [0.0, 0.0]),
                ),
                "point_state": {},
            }

        state_bundle = PressureVisualisation._runtime_states[signature]
        # Expose the active signature bundle through legacy class attributes used elsewhere.
        PressureVisualisation._runtime_signature = signature
        PressureVisualisation._runtime_regimes = state_bundle["regimes"]
        PressureVisualisation._runtime_point_state = state_bundle["point_state"]

    @staticmethod
    def _compute_max_pressure_from_configuration(threshold_forces, area):
        # Convert the configured force ceiling into Pa so each point can be colour-scaled
        # against the same physical max for that configuration.
        max_force = float(threshold_forces[1]) if len(threshold_forces) >= 2 else 0.0
        if area <= 0:
            return 0.0
        return float((max_force / area) * 9806.65)

    @staticmethod
    def _get_or_create_point_state(channel_number, samples, threshold_forces, area):
        state = PressureVisualisation._runtime_point_state.get(channel_number)
        if state is not None:
            return state

        baseline = PressureVisualisation._runtime_pending_baselines.pop(channel_number, None)
        if baseline is None:
            baseline = PressureVisualisation._extract_startup_baseline(
                samples,
                PressureVisualisation._baseline_window_size,
            )
        if baseline is None:
            return None

        runtime_regimes = []
        for regime in PressureVisualisation._runtime_regimes:
            runtime_regimes.append(
                {
                    **dict(regime),
                    "absolute_boundary_resistance": float(baseline * regime["relative_boundary_resistance"]),
                }
            )

        max_pressure = PressureVisualisation._compute_max_pressure_from_configuration(threshold_forces, area)

        state = {
            "sensor_point_channel": int(channel_number),
            "baseline_resistance": baseline,
            "previous_force": None,
            "max_pressure": max_pressure,
            "regimes": runtime_regimes,
        }
        PressureVisualisation._runtime_point_state[channel_number] = state

        # One-time runtime snapshot for this point, printed when the startup baseline is first locked.
        print(
            "[PressureVisualisation] Sensor runtime state initialised:\n"
            f"{json.dumps(state, indent=2)}"
        )
        return state

    @staticmethod
    def evaluate_polynomial(coefficients, force_value):
        """Evaluate a calibration curve where coefficients are stored highest-power first."""
        coefficients = PressureVisualisation._normalise_polynomial(coefficients)
        return float(np.polyval(np.array(coefficients, dtype=float), float(force_value)))

    @staticmethod
    def get_relative_resistance_from_absolute(absolute_resistance, baseline_resistance):
        # The calibration curves are defined relative to a baseline resistance, not absolute raw ohms.
        # This normalisation lets us compare each live reading against the same scale independent of
        # the sensor's absolute starting resistance.
        if baseline_resistance <= 0:
            raise ValueError("Baseline resistance must be greater than zero.")
        return float(absolute_resistance / baseline_resistance)

    @staticmethod
    def solve_force_from_relative_resistance(
        coefficients,
        relative_resistance,
        lower_force_bound=0.0,
        upper_force_bound=float("inf"),
        previous_force=None,
    ):
        """Invert the active calibration polynomial for the force that produced this relative resistance."""
        coefficients = PressureVisualisation._normalise_polynomial(coefficients)
        if len(coefficients) == 1:
            if abs(coefficients[0] - relative_resistance) < 1e-9:
                if lower_force_bound <= 0.0 <= upper_force_bound:
                    return 0.0
                raise ValueError("Constant-curve solution is outside the active regime force bounds.")
            raise ValueError("This relative resistance is not consistent with the constant calibration curve.")

        polynomial = np.array([float(value) for value in coefficients], dtype=float)
        adjusted = polynomial.copy()
        adjusted[-1] = adjusted[-1] - float(relative_resistance)

        roots = np.roots(adjusted)
        candidates = []
        for root in roots:
            if abs(root.imag) > 1e-9:
                continue
            value = float(root.real)
            if not math.isfinite(value):
                continue
            if value < -1e-9:
                continue
            if value < (lower_force_bound - 1e-9) or value > (upper_force_bound + 1e-9):
                continue
            if value >= -1e-9:
                candidates.append(value)

        if not candidates:
            raise ValueError("No valid force root was found inside the active regime force bounds.")

        if previous_force is not None:
            return float(min(candidates, key=lambda candidate: abs(candidate - previous_force)))

        return float(min(candidates))

    @staticmethod
    def get_regime_index_for_relative_resistance(relative_resistance, runtime_regimes):
        if not runtime_regimes:
            return 0

        boundaries = [float(regime["relative_boundary_resistance"]) for regime in runtime_regimes]
        trend = 0
        for index in range(1, len(boundaries)):
            delta = boundaries[index] - boundaries[index - 1]
            if abs(delta) > 1e-12:
                trend = 1 if delta > 0 else -1
                break

        selected_index = 0
        if trend < 0:
            # Relative boundary values can decrease as force increases.
            for index in range(1, len(boundaries)):
                if relative_resistance <= (boundaries[index] + 1e-9):
                    selected_index = index
                else:
                    break
            return selected_index

        # Default path for increasing or flat boundary sequences.
        for index in range(1, len(boundaries)):
            if relative_resistance >= (boundaries[index] - 1e-9):
                selected_index = index
            else:
                break
        return selected_index

    @staticmethod
    def get_force_for_point(absolute_resistance, baseline_resistance, regimes):
        """Return the force and the active regime for a single absolute-resistance reading."""
        if not regimes:
            raise ValueError("No calibration regimes are available.")

        runtime_regimes = PressureVisualisation._build_runtime_regimes(regimes, [0.0, float("inf")])
        relative_resistance = PressureVisualisation.get_relative_resistance_from_absolute(
            absolute_resistance,
            baseline_resistance,
        )
        regime_index = PressureVisualisation.get_regime_index_for_relative_resistance(
            relative_resistance,
            runtime_regimes,
        )
        active_regime = runtime_regimes[regime_index]
        force = PressureVisualisation.solve_force_from_relative_resistance(
            active_regime["coefficients"],
            relative_resistance,
            lower_force_bound=active_regime["lower_bound_g"],
            upper_force_bound=active_regime["upper_bound_g"],
        )
        return float(force), regime_index

    @staticmethod
    def get_pressure_for_point(absolute_resistance, baseline_resistance, regimes, area):
        """Convert a single resistance reading into pressure by division by the applicator area."""
        if area <= 0:
            raise ValueError("Force applicator area must be greater than zero.")

        force, _ = PressureVisualisation.get_force_for_point(
            absolute_resistance,
            baseline_resistance,
            regimes,
        )
        return float(force / area)

    @staticmethod
    def get_pressure_for_all_points(active_device, channel_map, calibration_data, area):
        """Return a dictionary keyed by layer number containing pressure values for each sensor point."""
        if active_device is None or not hasattr(active_device, "channel_collection"):
            return {}

        # This is the live runtime state: the device keeps a channel Collection, and each channel keeps
        # a list of measured resistance samples. The pressure computation uses the newest sample and a
        # short rolling baseline from recent samples to make the classification stable in real time.

        channel_collection = active_device.channel_collection
        if not channel_collection:
            return {}

        PressureVisualisation._ensure_runtime_ready(calibration_data, area)
        if not PressureVisualisation._runtime_regimes:
            return {}

        threshold_forces = calibration_data.get("threshold_forces", [0.0, 0.0])

        pressure_by_point = {}
        for layer_number, channel_numbers in channel_map.items():
            layer_values = []
            for channel_number in channel_numbers:
                if channel_number < 0 or channel_number >= len(channel_collection):
                    layer_values.append(None)
                    continue

                channel = channel_collection[channel_number]
                samples = channel.return_raw_data()
                if not samples:
                    layer_values.append(None)
                    continue

                latest_resistance = float(samples[-1])
                point_state = PressureVisualisation._get_or_create_point_state(
                    channel_number,
                    samples,
                    threshold_forces,
                    area,
                )
                if point_state is None:
                    # Not enough startup values yet to lock a baseline for this sensor point.
                    layer_values.append(None)
                    continue

                baseline_resistance = point_state["baseline_resistance"]
                relative_resistance = PressureVisualisation.get_relative_resistance_from_absolute(
                    latest_resistance,
                    baseline_resistance,
                )
                regime_index = PressureVisualisation.get_regime_index_for_relative_resistance(
                    relative_resistance,
                    point_state["regimes"],
                )
                regime = point_state["regimes"][regime_index]
                try:
                    force = PressureVisualisation.solve_force_from_relative_resistance(
                        regime["coefficients"],
                        relative_resistance,
                        lower_force_bound=regime["lower_bound_g"],
                        upper_force_bound=regime["upper_bound_g"],
                        previous_force=point_state["previous_force"],
                    )
                    point_state["previous_force"] = force
                    value = float(force / area)
                except ValueError:
                    value = None
                layer_values.append(value)
            pressure_by_point[layer_number] = layer_values

        return pressure_by_point
