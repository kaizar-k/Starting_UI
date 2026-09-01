"""Embeds a Matplotlib 3D scatter of every layer's sensing points, stacked by layer number.

Layer 1 is drawn at the top of the stack; each following layer sits LAYER_SPACING lower. Marker
colours use the same Turbo palette as the 2D page, but are normalised against one shared maximum
(the largest max_pressure across every displayed point) so the colour scale is consistent across
the whole stack rather than per point.
"""

import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 - required to register the 3D projection


class Sensor3DVisualisationCanvas(tk.Frame):
    """Tkinter frame that renders every configured layer's sensing points as a 3D pressure map."""

    LAYER_SPACING = 1.0
    OUTLINE_SEGMENTS = 24
    CORNER_HALF_WIDTH = 1.0
    MIN_MARKER_SIZE = 40.0
    MARKER_SIZE_PER_RADIUS = 18.0

    def __init__(self, master, azimuth=-60, elevation=15, **kwargs):
        super().__init__(master, **kwargs)

        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.view_azimuth = azimuth
        self.view_elevation = elevation
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.ax.view_init(elev=self.view_elevation, azim=self.view_azimuth)

        # Draw order for every point, so live colour updates can be applied without rebuilding geometry.
        self._point_records = []
        self._scatter = None
        self._point_positions = ([], [], [])
        self._point_sizes = []
        self._draw_empty_state()

    def set_view(self, azimuth=None, elevation=None):
        """Set the camera angle for the 3D plot in degrees."""
        if azimuth is not None:
            self.view_azimuth = azimuth
        if elevation is not None:
            self.view_elevation = elevation
        self.ax.view_init(elev=self.view_elevation, azim=self.view_azimuth)
        self.canvas.draw_idle()

    def _draw_empty_state(self, message="No layers configured."):
        self.ax.clear()
        self.ax.text2D(0.5, 0.5, message, ha="center", va="center", transform=self.ax.transAxes)
        self.ax.view_init(elev=self.view_elevation, azim=self.view_azimuth)
        self.canvas.draw_idle()

    def _draw_point_outline(self, x, y, z, outer, inner):
        # Approximates each ring/corner as a flat polygon at the layer's z-plane.
        angles = np.linspace(0, 2 * np.pi, self.OUTLINE_SEGMENTS)
        if outer > 0:
            self.ax.plot(x + outer * np.cos(angles), y + outer * np.sin(angles), z, color="royalblue", linewidth=1)
            if inner > 0:
                self.ax.plot(x + inner * np.cos(angles), y + inner * np.sin(angles), z, color="royalblue", linewidth=1)
        else:
            half = self.CORNER_HALF_WIDTH
            square_x = [x - half, x + half, x + half, x - half, x - half]
            square_y = [y - half, y - half, y + half, y + half, y - half]
            self.ax.plot(square_x, square_y, z, color="royalblue", linewidth=1)

    def rebuild_structure(self, layer_geometries: dict, show_outlines: bool):
        """Rebuild the static geometry (positions, sizes, outlines) for the current layer set."""
        self.ax.clear()
        self._point_records = []
        self._scatter = None
        self._point_positions = ([], [], [])
        self._point_sizes = []

        if not layer_geometries:
            self._draw_empty_state()
            return

        xs, ys, zs, sizes = [], [], [], []
        for layer_number in sorted(layer_geometries):
            _dimensions, sensing_points = layer_geometries[layer_number]
            # Layer 1 at the top; each subsequent layer sits lower in the stack.
            z = -(layer_number - 1) * self.LAYER_SPACING

            for point_index, point in enumerate(sensing_points, start=1):
                x = float(point["x"])
                y = float(point["y"])
                outer = float(point.get("radius_outer", 0.0) or 0.0)
                inner = float(point.get("radius_inner", 0.0) or 0.0)

                xs.append(x)
                ys.append(y)
                zs.append(z)
                sizes.append(self.MIN_MARKER_SIZE + outer * self.MARKER_SIZE_PER_RADIUS)
                self._point_records.append({"layer_number": layer_number, "point_index": point_index})

                if show_outlines:
                    self._draw_point_outline(x, y, z, outer, inner)

        # Cached so colour updates can recreate the scatter without recomputing layout each tick.
        self._point_positions = (xs, ys, zs)
        self._point_sizes = sizes
        self._scatter = self.ax.scatter(
            xs, ys, zs, s=sizes, c=["white"] * len(xs), edgecolors="royalblue", depthshade=False
        )

        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.set_zlabel("Layer stack")
        self.ax.view_init(elev=self.view_elevation, azim=self.view_azimuth)
        self.canvas.draw_idle()

    def set_heatmap_values(self, pressure_by_layer_point: dict, max_pressure_by_layer_point: dict):
        """Recolour every point (Pa) against one shared global maximum, without touching geometry."""
        if self._scatter is None or not self._point_records:
            return

        global_max_pressure = max(
            (float(max_pressure_by_layer_point.get(self._point_key(record), 0.0) or 0.0) for record in self._point_records),
            default=0.0,
        )

        cmap = plt.get_cmap("turbo")
        colours = []
        for record in self._point_records:
            key = self._point_key(record)
            pressure = pressure_by_layer_point.get(key)
            if pressure is None:
                colours.append((1.0, 1.0, 1.0, 1.0))
                continue
            if global_max_pressure <= 0:
                progress = 0.0
            else:
                progress = max(0.0, min(1.0, float(pressure) / global_max_pressure))
            colours.append(cmap(progress))

        # mplot3d recomputes facecolor from its own cache on redraw, so set_facecolor() alone
        # gets silently overwritten; recreating the scatter with the cached layout is the reliable fix.
        xs, ys, zs = self._point_positions
        self._scatter.remove()
        self._scatter = self.ax.scatter(
            xs, ys, zs, s=self._point_sizes, c=colours, edgecolors="royalblue", depthshade=False
        )
        self.canvas.draw_idle()

    @staticmethod
    def _point_key(record):
        return record["layer_number"], record["point_index"]
