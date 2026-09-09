import math
import tkinter as tk

from visualisation_backend.pressure_visualisation import PressureVisualisation


class DeviceAllTraces:
    """Open one lightweight live relative-resistance window for each sensor channel."""

    _windows = {}

    def __init__(self, master, active_device=None, channel_numbers=None, refresh_ms=250):
        self.master = master
        self.active_device = active_device
        self.channel_numbers = list(channel_numbers or [])
        self.refresh_ms = refresh_ms
        self.value_vars = {}
        self._update_job = None

        self.window = None

        if not self.channel_numbers:
            return

        key = tuple(self.channel_numbers)
        existing = self._windows.get(key)
        if existing is not None and existing.winfo_exists():
            self.window = existing
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(master)
        self.window.title("Live relative resistance")
        self.window.geometry("420x500")

        content = tk.Frame(self.window, padx=18, pady=14)
        content.pack(fill="both", expand=True)
        tk.Label(
            content,
            text="Relative resistance (R / R0)",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        for channel_number in self.channel_numbers:
            row = tk.Frame(content)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"Channel {channel_number}", width=14, anchor="w").pack(side="left")
            value_var = tk.StringVar(value="--")
            tk.Label(row, textvariable=value_var, width=14, anchor="e").pack(side="right")
            self.value_vars[channel_number] = value_var

        self._windows[key] = self.window
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self._update_values()

    def _resolve_device(self):
        if self.active_device is not None:
            return self.active_device
        return getattr(self.master, "active_device", None)

    def _update_values(self):
        if self.window is None or not self.window.winfo_exists():
            return

        device = self._resolve_device()
        channel_collection = getattr(device, "channel_collection", []) if device is not None else []
        runtime_states = PressureVisualisation._runtime_point_state

        for channel_number, value_var in self.value_vars.items():
            value_var.set(self._format_relative_value(channel_collection, runtime_states, channel_number))

        self._update_job = self.window.after(self.refresh_ms, self._update_values)

    @staticmethod
    def _format_relative_value(channel_collection, runtime_states, channel_number):
        """Return the latest resistance divided by its established runtime baseline."""
        if channel_number >= len(channel_collection):
            return "--"

        samples = channel_collection[channel_number].return_raw_data()
        state = runtime_states.get(channel_number)
        if not samples:
            return "--"

        try:
            latest_resistance = float(samples[-1])
            if state is not None:
                baseline = float(state["baseline_resistance"])
            else:
                baseline = PressureVisualisation._runtime_pending_baselines.get(channel_number)
                if baseline is None:
                    numeric_samples = [float(value) for value in samples if math.isfinite(float(value))]
                    if len(numeric_samples) > 1 and abs(numeric_samples[0]) < 1e-12:
                        numeric_samples = numeric_samples[1:]
                    if len(numeric_samples) < PressureVisualisation._baseline_window_size:
                        return "--"
                    baseline = sum(numeric_samples[:PressureVisualisation._baseline_window_size]) / PressureVisualisation._baseline_window_size
            relative_resistance = PressureVisualisation.get_relative_resistance_from_absolute(
                latest_resistance,
                baseline,
            )
            if not math.isfinite(relative_resistance):
                return "--"
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            return "--"

        return f"{relative_resistance:.4f}"

    def close(self):
        if self._update_job is not None and self.window is not None:
            try:
                self.window.after_cancel(self._update_job)
            except tk.TclError:
                pass
            self._update_job = None
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        if self.channel_numbers:
            self._windows.pop(tuple(self.channel_numbers), None)

    @classmethod
    def close_all(cls):
        for window in list(cls._windows.values()):
            if window.winfo_exists():
                window.destroy()
        cls._windows.clear()
