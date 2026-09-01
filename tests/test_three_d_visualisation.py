import tkinter as tk

import pytest

from visualisation_backend.three_d_visualisation import Sensor3DVisualisationCanvas


def _create_tk_root_or_skip():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk is unavailable in this environment: {exc}")
    root.withdraw()
    return root


def _build_canvas(root, show_outlines=True):
    layer_geometries = {
        1: ((10, 10), [{"x": 5, "y": 5, "radius_outer": 4, "radius_inner": 2}]),
        2: ((10, 10), [{"x": 5, "y": 5, "radius_outer": 2, "radius_inner": 0}]),
    }
    canvas = Sensor3DVisualisationCanvas(root)
    canvas.rebuild_structure(layer_geometries, show_outlines)
    return canvas


def test_layer_one_is_drawn_above_later_layers():
    root = _create_tk_root_or_skip()
    try:
        canvas = _build_canvas(root)

        z_by_layer = {record["layer_number"]: z for record, z in zip(canvas._point_records, canvas._scatter._offsets3d[2])}
        assert z_by_layer[1] > z_by_layer[2]
    finally:
        root.destroy()


def test_marker_size_scales_with_outer_radius():
    root = _create_tk_root_or_skip()
    try:
        canvas = _build_canvas(root)

        sizes = list(canvas._scatter.get_sizes())
        # Layer 1's point has a larger outer radius (4) than layer 2's point (2).
        assert sizes[0] > sizes[1]
    finally:
        root.destroy()


def test_heatmap_uses_shared_global_max_and_turbo_endpoints():
    import matplotlib.pyplot as plt

    root = _create_tk_root_or_skip()
    try:
        canvas = _build_canvas(root)

        pressure_by_layer_point = {(1, 1): 0.0, (2, 1): 100.0}
        max_pressure_by_layer_point = {(1, 1): 100.0, (2, 1): 50.0}

        canvas.set_heatmap_values(pressure_by_layer_point, max_pressure_by_layer_point)
        # mplot3d only finalises depth-sorted facecolors on an actual draw, not draw_idle.
        canvas.canvas.draw()
        colours = {tuple(colour) for colour in canvas._scatter.get_facecolor()}

        cmap = plt.get_cmap("turbo")
        # Global max is 100.0 (from point (1, 1)'s max_pressure), so point (2, 1) at 100 Pa
        # reaches the top of the shared scale even though its own max_pressure is only 50.
        assert colours == {cmap(0.0), cmap(1.0)}
    finally:
        root.destroy()


def test_heatmap_uses_white_for_unavailable_pressure():
    root = _create_tk_root_or_skip()
    try:
        canvas = _build_canvas(root)

        canvas.set_heatmap_values(
            pressure_by_layer_point={(1, 1): None, (2, 1): 100.0},
            max_pressure_by_layer_point={(1, 1): 100.0, (2, 1): 100.0},
        )
        canvas.canvas.draw()
        colours = {tuple(colour) for colour in canvas._scatter.get_facecolor()}

        assert (1.0, 1.0, 1.0, 1.0) in colours
    finally:
        root.destroy()


def test_show_outlines_toggle_adds_line_artists():
    root = _create_tk_root_or_skip()
    try:
        canvas_with_outlines = _build_canvas(root, show_outlines=True)
        lines_with_outlines = len(canvas_with_outlines.ax.lines)

        canvas_without_outlines = _build_canvas(root, show_outlines=False)
        lines_without_outlines = len(canvas_without_outlines.ax.lines)

        assert lines_with_outlines > lines_without_outlines
        assert lines_without_outlines == 0
    finally:
        root.destroy()


def test_refresh_from_config_hides_3d_plot_when_disabled():
    root = _create_tk_root_or_skip()
    try:
        from gui.pages.page_visualisations.three_d_visualisation_page import ThreeDVisualisationPage

        canvas = type(
            "FakeCanvas",
            (),
            {"_draw_empty_state": lambda self, message="No layers configured.": setattr(self, "empty_drawn", True) or setattr(self, "last_message", message)},
        )()
        page = object.__new__(ThreeDVisualisationPage)
        page.canvas_3d = canvas
        page.master = type(
            "FakeMaster",
            (),
            {
                "pages": [
                    type(
                        "FakeConfigPage",
                        (),
                        {"config_values": {"show_3d_plot": False}, "sensor_design_backend": object()},
                    )()
                ]
            },
        )()
        page._live_update_job = None

        page.refresh_from_config()

        assert page.canvas_3d.empty_drawn is True
    finally:
        root.destroy()
