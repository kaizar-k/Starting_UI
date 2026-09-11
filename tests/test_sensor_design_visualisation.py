import argparse
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pytest
import tkinter as tk
from tkinter import ttk

from gui.controls.sensor_design_canvas import SensorDesignCanvas


ROOT = Path(__file__).resolve().parents[1]
DESIGN_CSV = ROOT / "data" / "design_data.csv"


def _create_tk_root_or_skip():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk is unavailable in this environment: {exc}")
    root.withdraw()
    return root


def load_design(name: str):
    df = pd.read_csv(DESIGN_CSV)
    row = df[df["Sensor Design"].astype(str).str.strip() == name].iloc[0]
    dimensions = json.loads(row["Dimensions"])
    sensing_points = json.loads(row["Sensing Points"])
    return dimensions, sensing_points


def interpolate_rgb(start_rgb, end_rgb, t):
    """Linearly blend between two RGB tuples using t in the range [0, 1]."""
    return tuple(int(start + (end - start) * t) for start, end in zip(start_rgb, end_rgb))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def get_scientific_colour(progress: float):
    """Sample the Matplotlib 'turbo' scientific palette for a smooth blue-green-yellow-orange-red transition."""
    progress = min(max(progress, 0.0), 1.0)
    colour = plt.get_cmap("turbo")(progress)
    return tuple(int(channel * 255) for channel in colour[:3])


def animate_sensor_colours(canvas: tk.Canvas, duration_seconds: float = 10.0):
    """Drive every sensing shape on the canvas from one shared clock so the colours stay in sync."""
    # A redraw must cancel the previous loop, otherwise stacked callbacks fight over the same items.
    pending_id = getattr(canvas, "_colour_animation_id", None)
    if pending_id is not None:
        canvas.after_cancel(pending_id)
        canvas._colour_animation_id = None

    start_time = time.monotonic()

    def update_colour():
        if not canvas.winfo_exists():
            return

        # Wrapping with modulo keeps the cycle seamless instead of restarting the whole loop.
        elapsed = (time.monotonic() - start_time) % duration_seconds
        colour = rgb_to_hex(get_scientific_colour(elapsed / duration_seconds))
        canvas.itemconfig("sensor_ring", fill=colour)
        canvas._colour_animation_id = canvas.after(20, update_colour)

    canvas._colour_animation_id = canvas.after(20, update_colour)


def test_sensor_design_canvas_inner_ring_matches_outer_border_style():
    root = _create_tk_root_or_skip()
    try:
        canvas = SensorDesignCanvas(
            root,
            dimensions=(10, 10),
            sensing_points=[{"x": 5, "y": 5, "radius_outer": 4, "radius_inner": 2}],
            width=200,
            height=200,
        )

        assert canvas.itemcget("ring_1", "width") in {"2", "2.0"}
        assert canvas.itemcget("hole_1", "width") in {"2", "2.0"}

        canvas._update_hover_highlight(100, 100)
        assert canvas.itemcget("ring_1", "outline") == "black"
        assert canvas.itemcget("ring_1", "width") in {"5", "5.0"}
        assert canvas.itemcget("hole_1", "outline") == "black"
        assert canvas.itemcget("hole_1", "width") in {"5", "5.0"}
    finally:
        root.destroy()


def test_sensor_design_canvas_heatmap_scales_between_zero_and_max_pressure():
    root = _create_tk_root_or_skip()
    try:
        canvas = SensorDesignCanvas(
            root,
            dimensions=(10, 10),
            sensing_points=[{"x": 5, "y": 5, "radius_outer": 4, "radius_inner": 2}],
            width=200,
            height=200,
        )

        canvas.set_heatmap_values([0.0], [1000.0])
        zero_fill = canvas.itemcget("ring_1", "fill")

        canvas.set_heatmap_values([1000.0], [1000.0])
        max_fill = canvas.itemcget("ring_1", "fill")

        assert zero_fill == SensorDesignCanvas._turbo_colour_hex(0.0)
        assert max_fill == SensorDesignCanvas._turbo_colour_hex(1.0)
        assert zero_fill != max_fill
    finally:
        root.destroy()


def test_sensor_design_canvas_uses_white_for_unavailable_pressure():
    root = _create_tk_root_or_skip()
    try:
        canvas = SensorDesignCanvas(
            root,
            dimensions=(10, 10),
            sensing_points=[{"x": 5, "y": 5, "radius_outer": 4, "radius_inner": 2}],
            width=200,
            height=200,
        )

        canvas.set_heatmap_values([None], [1000.0])

        assert canvas.itemcget("ring_1", "fill") == "white"
    finally:
        root.destroy()


def test_live_trace_series_uses_host_time_when_firmware_timestamp_stalls():
    class FakeChannel:
        def __init__(self, values):
            self._values = values

        def return_raw_data(self):
            return self._values

    class FakeDevice:
        channel_collection = [
            FakeChannel([0, 1, 1]),
            FakeChannel([100.0, 101.0, 102.0]),
        ]
        host_time_values = [10.0, 25.0, 40.0]

    from visualisation_backend.trace_visualisation import get_live_trace_series

    time_values, resistance_values = get_live_trace_series(FakeDevice(), 1)

    assert time_values == [10.0, 25.0, 40.0]
    assert resistance_values == [100.0, 101.0, 102.0]


def update_hover_highlight(canvas: tk.Canvas, dimensions, sensing_points, mouse_x, mouse_y):
    width, height = dimensions
    padding = 30
    canvas_w = max(canvas.winfo_width(), 1)
    canvas_h = max(canvas.winfo_height(), 1)
    scale = min((canvas_w - 2 * padding) / width, (canvas_h - 2 * padding) / height)
    cx = canvas_w / 2
    cy = canvas_h / 2

    hovered_index = None
    for index, point in enumerate(sensing_points, start=1):
        x = float(point["x"])
        y = float(point["y"])
        outer = float(point.get("radius_outer", 0.0) or 0.0)

        x_px = cx + (x - width / 2) * scale
        y_px = cy - (y - height / 2) * scale
        # Zero-radius corner squares get a fixed circular hover region so the hit test stays uniform.
        radius_px = (outer if outer > 0 else 2.0) * scale
        distance = ((mouse_x - x_px) ** 2 + (mouse_y - y_px) ** 2) ** 0.5

        if distance <= radius_px:
            hovered_index = index
            break

    for index, point in enumerate(sensing_points, start=1):
        ring_tag = f"ring_{index}"
        hole_tag = f"hole_{index}"
        label_tag = f"label_{index}"
        highlight_width = 5 if hovered_index == index else 2
        outline = "black" if hovered_index == index else "royalblue"
        canvas.itemconfig(ring_tag, outline=outline, width=highlight_width)
        if canvas.find_withtag(hole_tag):
            canvas.itemconfig(hole_tag, outline=outline, width=highlight_width)
        canvas.itemconfig(label_tag, fill="black")


def draw_sensor(canvas: tk.Canvas, design_name: str, dimensions, sensing_points):
    width, height = dimensions
    canvas.update_idletasks()
    canvas.delete("all")
    canvas.create_text(10, 10, anchor="nw", text=design_name, fill="black", font=("TkDefaultFont", 10, "bold"))

    # Use the actual canvas size once the widget has been laid out, then centre the sensor
    # rectangle in that panel. This avoids the previous top-left anchoring issue while keeping
    # the x/y coordinates mapped directly to the design geometry.
    padding = 30
    canvas_w = max(canvas.winfo_width(), 1)
    canvas_h = max(canvas.winfo_height(), 1)
    scale = min((canvas_w - 2 * padding) / width, (canvas_h - 2 * padding) / height)
    cx = canvas_w / 2
    cy = canvas_h / 2

    left = cx - (width * scale / 2)
    top = cy - (height * scale / 2)
    right = left + width * scale
    bottom = top + height * scale
    canvas.create_rectangle(left, top, right, bottom, outline="black", width=2)

    for index, point in enumerate(sensing_points, start=1):
        x = float(point["x"])
        y = float(point["y"])
        outer = float(point.get("radius_outer", 0.0) or 0.0)
        inner = float(point.get("radius_inner", 0.0) or 0.0)

        x_px = cx + (x - width / 2) * scale
        y_px = cy - (y - height / 2) * scale

        if outer > 0:
            # The live sensor region is the annulus between the inner and outer radius, so fill that
            # area with blue to visually show the changing region. The inner hole remains empty.
            ring = canvas.create_oval(
                x_px - outer * scale,
                y_px - outer * scale,
                x_px + outer * scale,
                y_px + outer * scale,
                outline="royalblue",
                width=2,
                fill="blue",
                tags=(f"ring_{index}", "sensor_ring"),
            )
            if inner > 0:
                # Cut out the centre hole by drawing a smaller oval whose border matches the outer ring.
                canvas.create_oval(
                    x_px - inner * scale,
                    y_px - inner * scale,
                    x_px + inner * scale,
                    y_px + inner * scale,
                    outline="royalblue",
                    width=2,
                    fill="white",
                    tags=(f"hole_{index}", "sensor_hole"),
                )
            canvas.tag_lower(ring)
        elif outer == 0 and inner == 0:
            # A zero-radius sensor point represents a corner marker, so draw a square centred on the
            # point with a side length of 2 in design units. This keeps it visually clear while staying
            # aligned with the existing coordinate system.
            square_half_width = 1.0 * scale
            canvas.create_rectangle(
                x_px - square_half_width,
                y_px - square_half_width,
                x_px + square_half_width,
                y_px + square_half_width,
                outline="royalblue",
                width=2,
                fill="blue",
                tags=(f"ring_{index}", "sensor_ring"),
            )

        canvas.create_text(x_px, y_px, text=str(index), fill="black", font=("TkDefaultFont", 8, "bold"), tags=(f"label_{index}", "sensor_label"))

    # One loop per canvas keeps every ring and corner square on the same colour timeline.
    animate_sensor_colours(canvas)


def add_colourbar(frame, width=24, height=220):
    """Add a simple vertical Turbo colourbar with blue at the bottom and red at the top."""
    cmap = plt.get_cmap("turbo")
    gradient_canvas = tk.Canvas(frame, width=width, height=height, bg="white", highlightthickness=0)
    gradient_canvas.pack(side="left", padx=(0, 8), pady=10)

    for i in range(height):
        # Flip the direction so low values are at the bottom and high values are at the top.
        t = 1.0 - (i / max(height - 1, 1))
        r, g, b, _ = cmap(t)
        hex_colour = rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))
        gradient_canvas.create_line(0, i, width, i, fill=hex_colour, width=1)

    labels = ["0", "0.5", "1.0"]
    y_positions = [height, height / 2, 0]
    for label_text, y_offset in zip(labels, y_positions):
        gradient_canvas.create_text(width + 8, y_offset, anchor="w", text=label_text, fill="black", font=("TkDefaultFont", 8))

    gradient_canvas.create_text(width / 2, -12, text="Pressure", fill="black", font=("TkDefaultFont", 8, "bold"))


def build_ui(root: tk.Tk, design_names):
    root.title("Sensor Design Visualisation")
    root.geometry("1180x420")

    canvas_panel = ttk.Frame(root, padding=10)
    canvas_panel.pack(fill="both", expand=True)

    for design_name in design_names:
        frame = ttk.LabelFrame(canvas_panel, text=design_name, padding=10)
        frame.pack(side="left", padx=10, pady=10, fill="both", expand=True)

        plot_container = ttk.Frame(frame)
        plot_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(plot_container, width=420, height=320, bg="white")
        canvas.pack(side="left", fill="both", expand=True)

        add_colourbar(plot_container, width=28, height=220)

        canvas.bind("<Configure>", lambda event, name=design_name, c=canvas: draw_sensor(c, name, load_design(name)[0], load_design(name)[1]))
        canvas.bind("<Motion>", lambda event, c=canvas, dims=load_design(design_name)[0], points=load_design(design_name)[1]: update_hover_highlight(c, dims, points, event.x, event.y))
        canvas.bind("<Leave>", lambda event, c=canvas, dims=load_design(design_name)[0], points=load_design(design_name)[1]: [canvas.itemconfig(f"ring_{idx}", outline="royalblue", width=2) for idx in range(1, len(points) + 1)])

        dimensions, sensing_points = load_design(design_name)
        draw_sensor(canvas, design_name, dimensions, sensing_points)


def main():
    parser = argparse.ArgumentParser(description="Render a quick Tkinter-only view of the sensor designs.")
    parser.add_argument("--close-after-ms", type=int, default=0, help="Optional auto-close delay for headless verification.")
    args = parser.parse_args()

    design_names = ["1-Loop-Top", "4-Loop-Top", "1-Loop-2-Corner-Top"]
    root = tk.Tk()
    build_ui(root, design_names)

    if args.close_after_ms > 0:
        root.after(args.close_after_ms, root.destroy)

    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - this is a visual smoke test, not a library function.
        raise SystemExit(f"Failed to render sensor design visualisation: {exc}")
