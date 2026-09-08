import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


def get_live_trace_series(active_device, channel_number):
    """Return the live time and resistance data for a given channel."""
    if active_device is None:
        return [], []

    channel_collection = getattr(active_device, "channel_collection", [])
    if not channel_collection:
        return [], []

    if channel_number < 0 or channel_number >= len(channel_collection):
        raise IndexError(f"Channel {channel_number} is out of range for this device.")

    raw_time_values = list(channel_collection[0].return_raw_data())
    raw_resistance_values = list(channel_collection[channel_number].return_raw_data())

    samples = []
    last_timestamp = None
    for timestamp, resistance in zip(raw_time_values, raw_resistance_values):
        # A timestamp that moves backwards would make Matplotlib draw a line
        # across an earlier part of the trace. Ignore only that bad sample.
        if last_timestamp is not None and timestamp <= last_timestamp:
            continue
        samples.append((timestamp, resistance))
        last_timestamp = timestamp

    if not samples:
        return [], []

    time_values, resistance_values = zip(*samples)
    return list(time_values), list(resistance_values)


class TracePopup:
    """Tkinter popup that plots resistance against time for one sensor point."""

    _windows = {}

    def __init__(self, master, layer_number, point_index, channel_number, active_device=None,
                 device_provider=None, refresh_ms=250):
        self.master = master
        self.layer_number = layer_number
        self.point_index = point_index
        self.channel_number = channel_number
        self.active_device = active_device
        # Resolved per refresh so a reconnect or restart never leaves the plot bound to a dead device.
        self.device_provider = device_provider
        self.refresh_ms = refresh_ms

        self.window_key = (layer_number, point_index)
        if self.window_key in self._windows and self._windows[self.window_key].winfo_exists():
            self.window = self._windows[self.window_key]
            self.window.lift()
            self.window.focus_force()
            self._refresh_plot()
            return

        self.window = tk.Toplevel(master)
        self.window.title(f"Layer {layer_number} - Point {point_index} trace")
        self.window.geometry("600x400")

        self.figure = Figure(figsize=(5, 3.5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(f"Layer {layer_number} / Point {point_index} / CH{channel_number}")
        self.ax.set_xlabel("Time (ms)")
        self.ax.set_ylabel("Resistance (Ω)")
        self.ax.grid(True, alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.figure, self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        self._windows[self.window_key] = self.window
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self._refresh_plot()

    def _resolve_device(self):
        if self.device_provider is not None:
            return self.device_provider()
        return self.active_device

    def _refresh_plot(self):
        if not self.window.winfo_exists():
            return

        try:
            time_values, resistance_values = get_live_trace_series(self._resolve_device(), self.channel_number)
        except (AttributeError, IndexError, TypeError):
            time_values, resistance_values = [], []

        self.ax.clear()
        self.ax.set_title(f"Layer {self.layer_number} / Point {self.point_index} / CH{self.channel_number}")
        self.ax.set_xlabel("Time (ms)")
        self.ax.set_ylabel("Resistance (Ω)")
        self.ax.grid(True, alpha=0.3)

        if time_values and resistance_values:
            self.ax.plot(time_values, resistance_values, color="royalblue", linewidth=2)
            if len(time_values) > 1:
                self.ax.set_xlim(min(time_values), max(time_values))
            if len(resistance_values) > 1:
                lower = min(resistance_values)
                upper = max(resistance_values)
                if upper == lower:
                    self.ax.set_ylim(lower - 1, upper + 1)
                else:
                    self.ax.set_ylim(lower, upper * 1.05)
        else:
            self.ax.text(0.5, 0.5, "No live data yet", ha="center", va="center", transform=self.ax.transAxes)

        self.canvas.draw_idle()
        if self.window.winfo_exists():
            self.window.after(self.refresh_ms, self._refresh_plot)

    def close(self):
        if self.window.winfo_exists():
            self.window.destroy()
        self._windows.pop(self.window_key, None)

    @classmethod
    def close_all(cls):
        """Destroy every open trace window so a finished run leaves no stale plot behind."""
        for window in list(cls._windows.values()):
            if window.winfo_exists():
                window.destroy()
        cls._windows.clear()
