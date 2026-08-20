import tkinter as tk


class SensorDesignCanvas(tk.Canvas):
    """Fixed-size canvas that draws one sensor design and highlights sensing points on hover."""

    PADDING = 30
    # Zero-radius corner points have no radius to hit test against, so they use a fixed region.
    CORNER_HOVER_RADIUS = 2.0
    CORNER_SQUARE_HALF_WIDTH = 1.0

    def __init__(self, master, dimensions, sensing_points, width=420, height=320, **kwargs):
        super().__init__(master, width=width, height=height, bg="white", highlightthickness=0, **kwargs)
        self.dimensions = dimensions
        self.sensing_points = sensing_points

        self.bind("<Configure>", lambda event: self.draw())
        self.bind("<Motion>", lambda event: self._update_hover_highlight(event.x, event.y))
        self.bind("<Leave>", lambda event: self._reset_highlight())

        self.draw()

    def _get_transform(self):
        """Return the scale and centre used to map design coordinates onto canvas pixels."""
        width, height = self.dimensions
        # Before the widget is mapped winfo_width reports 1, so fall back to the requested size.
        canvas_w = self.winfo_width() if self.winfo_width() > 1 else self.winfo_reqwidth()
        canvas_h = self.winfo_height() if self.winfo_height() > 1 else self.winfo_reqheight()
        scale = min(
            (canvas_w - 2 * self.PADDING) / width,
            (canvas_h - 2 * self.PADDING) / height,
        )
        return scale, canvas_w / 2, canvas_h / 2

    def _to_pixels(self, x, y, scale, cx, cy):
        width, height = self.dimensions
        # Canvas y grows downwards, so the design y axis is flipped here.
        return cx + (x - width / 2) * scale, cy - (y - height / 2) * scale

    def draw(self):
        width, height = self.dimensions
        self.update_idletasks()
        self.delete("all")

        scale, cx, cy = self._get_transform()

        left = cx - (width * scale / 2)
        top = cy - (height * scale / 2)
        self.create_rectangle(left, top, left + width * scale, top + height * scale, outline="black", width=2)

        for index, point in enumerate(self.sensing_points, start=1):
            outer = float(point.get("radius_outer", 0.0) or 0.0)
            inner = float(point.get("radius_inner", 0.0) or 0.0)
            x_px, y_px = self._to_pixels(float(point["x"]), float(point["y"]), scale, cx, cy)

            if outer > 0:
                ring = self.create_oval(
                    x_px - outer * scale,
                    y_px - outer * scale,
                    x_px + outer * scale,
                    y_px + outer * scale,
                    outline="royalblue",
                    width=2,
                    fill="white",
                    tags=(f"ring_{index}", "sensor_ring"),
                )
                if inner > 0:
                    self.create_oval(
                        x_px - inner * scale,
                        y_px - inner * scale,
                        x_px + inner * scale,
                        y_px + inner * scale,
                        outline="royalblue",
                        width=1,
                        fill="white",
                        tags=(f"hole_{index}", "sensor_hole"),
                    )
                self.tag_lower(ring)
            elif outer == 0 and inner == 0:
                # A zero-radius point marks a corner, drawn as a square of side length 2 design units.
                half_width = self.CORNER_SQUARE_HALF_WIDTH * scale
                self.create_rectangle(
                    x_px - half_width,
                    y_px - half_width,
                    x_px + half_width,
                    y_px + half_width,
                    outline="royalblue",
                    width=2,
                    fill="white",
                    tags=(f"ring_{index}", "sensor_ring"),
                )

            self.create_text(
                x_px,
                y_px,
                text=str(index),
                fill="black",
                font=("TkDefaultFont", 8, "bold"),
                tags=(f"label_{index}", "sensor_label"),
            )

    def _update_hover_highlight(self, mouse_x, mouse_y):
        scale, cx, cy = self._get_transform()

        hovered_index = None
        for index, point in enumerate(self.sensing_points, start=1):
            outer = float(point.get("radius_outer", 0.0) or 0.0)
            x_px, y_px = self._to_pixels(float(point["x"]), float(point["y"]), scale, cx, cy)

            radius_px = (outer if outer > 0 else self.CORNER_HOVER_RADIUS) * scale
            distance = ((mouse_x - x_px) ** 2 + (mouse_y - y_px) ** 2) ** 0.5

            if distance <= radius_px:
                hovered_index = index
                break

        for index in range(1, len(self.sensing_points) + 1):
            if index == hovered_index:
                self.itemconfig(f"ring_{index}", outline="black", width=5)
            else:
                self.itemconfig(f"ring_{index}", outline="royalblue", width=2)

    def _reset_highlight(self):
        self.itemconfig("sensor_ring", outline="royalblue", width=2)
