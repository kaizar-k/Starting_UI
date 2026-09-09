import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from visualisation_backend.trace_visualisation import get_live_trace_series


class DeviceAllTraces:
    """Open one live raw-resistance trace window for every configured sensor channel."""

    _windows = {}

    def __init__(self, master, active_device=None, channel_numbers=None, refresh_ms=250):
        self.master = master
        self.active_device = active_device
        self.channel_numbers = list(channel_numbers or [])
        self.refresh_ms = refresh_ms

        self.window = None
        self.figure = None
        self.axes = []
        self.canvas = None
        self.all_lines = []

        if not self.channel_numbers:
            return

        key = tuple(self.channel_numbers)
        existing = self._windows.get(key)
        if existing is not None and existing.winfo_exists():
            self.window = existing
            self.window.lift()
            self.window.focus_force()
            self.axes = getattr(self.window, "_device_all_axes", [])
            self.canvas = getattr(self.window, "_device_all_canvas", None)
            self.all_lines = getattr(self.window, "_device_all_lines", [])
            self._refresh_plot()
            return

        self.window = tk.Toplevel(master)
        self.window.title("Live resistance stream - all sensor points")
        self.window.geometry("1100x700")

        self.figure = Figure(figsize=(11, 6), dpi=100)
        self.axes = self.figure.subplots(len(self.channel_numbers), 1, sharex=True)
        if len(self.channel_numbers) == 1:
            self.axes = [self.axes]
        else:
            self.axes = list(self.axes)

        for axis, channel_number in zip(self.axes, self.channel_numbers):
            axis.set_title(f"CH{channel_number}")
            axis.set_ylabel("")
            axis.tick_params(axis="y", labelleft=False)
            axis.grid(True, alpha=0.3)
            axis.set_xlim(0, 50000)
            line, = axis.plot([], [], color="royalblue", linewidth=1.8)
            self.all_lines.append(line)

        self.axes[-1].set_xlabel("Time (ms)")

        self.canvas = FigureCanvasTkAgg(self.figure, self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        self.window._device_all_axes = self.axes
        self.window._device_all_canvas = self.canvas
        self.window._device_all_lines = self.all_lines
        self._windows[key] = self.window
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.figure.canvas.mpl_connect("close_event", self._on_close)
        self.animation = FuncAnimation(
            self.figure,
            self._update_all,
            frames=None,
            interval=self.refresh_ms,
            blit=False,
            cache_frame_data=False,
            repeat=False,
        )
        self.window._device_all_animation = self.animation

    def _resolve_device(self):
        if self.active_device is not None:
            return self.active_device
        return getattr(self.master, "active_device", None)

    def _on_close(self, _event):
        self.close()

    def _update_all(self, _):
        if self.window is None or not self.window.winfo_exists():
            return []

        device = self._resolve_device()

        for axis, channel_number, line in zip(self.axes, self.channel_numbers, self.all_lines):
            try:
                time_values, resistance_values = get_live_trace_series(device, channel_number)
            except (AttributeError, IndexError, TypeError):
                time_values, resistance_values = [], []

            axis.clear()
            axis.set_title(f"CH{channel_number}")
            axis.set_ylabel("")
            axis.tick_params(axis="y", labelleft=False)
            axis.grid(True, alpha=0.3)
            axis.set_xlim(0, 50000)

            if time_values and resistance_values:
                axis.plot(time_values, resistance_values, color="royalblue", linewidth=1.8)
                if len(resistance_values) > 1:
                    lower = min(resistance_values)
                    upper = max(resistance_values)
                    if upper == lower:
                        axis.set_ylim(lower - 1, upper + 1)
                    else:
                        axis.set_ylim(lower, upper * 1.05)
            else:
                axis.text(0.5, 0.5, "No live data yet", ha="center", va="center", transform=axis.transAxes)

        if self.axes:
            self.axes[-1].set_xlabel("Time (ms)")

        self.canvas.draw_idle()
        return self.all_lines

    def _refresh_plot(self):
        if not self.axes:
            return
        self._update_all(None)

    def close(self):
        animation = getattr(self.window, "_device_all_animation", None) if self.window is not None else None
        if animation is not None:
            try:
                animation.event_source.stop()
            except Exception:
                pass

        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        if self.channel_numbers:
            self._windows.pop(tuple(self.channel_numbers), None)

    @classmethod
    def close_all(cls):
        for window in list(cls._windows.values()):
            if window.winfo_exists():
                animation = getattr(window, "_device_all_animation", None)
                if animation is not None:
                    try:
                        animation.event_source.stop()
                    except Exception:
                        pass
                window.destroy()
        cls._windows.clear()
