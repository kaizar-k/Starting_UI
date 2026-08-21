"""Backend for the live sensing-point text list shown next to each layer's
diagram on the 2D visualisation page."""


class LayerTextBackend:
    """Builds per-layer sensing-point labels and their live resistance text."""

    def __init__(self, sensor_design_backend):
        self.sensor_design_backend = sensor_design_backend

    def get_layer_point_channels(self, layer_number: int, layer_count: int) -> list:
        """Return the channel number for each sensing point of a layer, in point order."""
        channel_map = self.sensor_design_backend.build_channel_map(layer_count)
        return channel_map.get(layer_number, [])

    def build_layer_point_rows(self, layer_number: int, layer_count: int, active_device) -> list:
        """Return [(point_index, channel_number, label_text), ...] for one layer's point list."""
        channel_numbers = self.get_layer_point_channels(layer_number, layer_count)
        rows = []
        for point_index, channel_number in enumerate(channel_numbers, start=1):
            value_text = self.format_channel_value(active_device, channel_number)
            rows.append((point_index, channel_number, f"Point {point_index}: {value_text}"))
        return rows

    @staticmethod
    def format_channel_value(active_device, channel_number: int) -> str:
        """Return the latest resistance reading for a channel, or "--" if unavailable."""
        if active_device is None:
            return "--"

        channel_collection = active_device.channel_collection
        # Channels are created lazily by set_up_channels(), so the collection may still be short.
        if channel_number >= len(channel_collection):
            return "--"

        raw_data = channel_collection[channel_number].return_raw_data()
        if not raw_data:
            return "--"

        return f"{raw_data[-1]:.2f} \u03a9"
