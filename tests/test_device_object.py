from serial_interface.device_object import DeviceObject


class StubSerial:
    def __init__(self, payload):
        self.in_waiting = 1
        self._payload = payload
        self.is_open = True
        self._buffer = payload.encode("utf-8")

    def readline(self):
        data = self._buffer
        self._buffer = b""
        self.in_waiting = 0
        return data

    def reset_input_buffer(self):
        return None

    def reset_output_buffer(self):
        return None


def test_receive_serial_ignores_short_partial_payloads():
    device = DeviceObject(0, "test", config_string="NC:5, SP:10")
    device.is_open = True
    device.in_waiting = 1
    device.channel_collection = [type("Channel", (), {"add_val": lambda self, val: None, "form": int})()]
    device.channel_collection[0].form = int

    device.readline = lambda: b"1234, 100.0, 200.0\n"
    result = device.receive_serial()

    assert result is None
