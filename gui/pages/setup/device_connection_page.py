import threading
import time
import tkinter as tk
from tkinter import ttk

from gui.pages.objects.page_object import PageObject


class DeviceConnectionPage(PageObject):
    """Page for scanning, connecting to, and starting/stopping the serial device."""

    # Matches the polling interval used in serial_interface/animation_threading_plot.py.
    POLL_INTERVAL_SECONDS = 0.001

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        self._stop_polling = threading.Event()

        self.form_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.form_frame.configure(borderwidth=1, relief="solid")

        self.status_var = tk.StringVar(value="No devices scanned yet.")
        ttk.Label(
            self.form_frame,
            textvariable=self.status_var,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        self.device_dropdown = ttk.Combobox(self.form_frame, state="readonly", width=70)
        self.device_dropdown.pack(anchor="w", pady=(0, 10))

        button_row = ttk.Frame(self.form_frame)
        button_row.pack(anchor="w")

        ttk.Button(button_row, text="Scan devices", command=self._scan_devices).pack(side="left", padx=(0, 5))
        ttk.Button(button_row, text="Connect", command=self._connect_device).pack(side="left", padx=(0, 5))
        ttk.Button(button_row, text="Start", command=self._start_device).pack(side="left", padx=(0, 5))
        ttk.Button(button_row, text="Stop", command=self._stop_device).pack(side="left", padx=(0, 5))

        self._schedule_scroll_region_update()

    def _scan_devices(self):
        devices = self.master.serial_manager.find_usb_devices()
        if not devices:
            self.status_var.set("No USB/Arduino/ESP devices found.")
            self.device_dropdown.configure(values=[])
            return

        self.device_dropdown.configure(values=[str(device) for device in devices])
        self.device_dropdown.current(0)
        self.status_var.set(f"Found {len(devices)} device(s). Select one and press Connect.")

    def _connect_device(self):
        selected_index = self.device_dropdown.current()
        if selected_index < 0:
            self.status_var.set("Scan for devices first.")
            return

        connected = self.master.serial_manager.connect_to_device(selected_index)
        if connected:
            self.master.active_device = self.master.serial_manager.devices[selected_index]
            self.status_var.set(f"Connected: {self.master.active_device}")
        else:
            self.status_var.set("Failed to connect - see console for details.")

    def _refresh_device_dropdown_entry(self, selected_index, device):
        """The dropdown values are a static snapshot from the last scan, so patch the entry in place."""
        values = list(self.device_dropdown.cget("values"))
        if 0 <= selected_index < len(values):
            values[selected_index] = str(device)
            self.device_dropdown.configure(values=values)
            self.device_dropdown.current(selected_index)

    def _compute_channel_count(self):
        """Total sensing points across every configured layer, per the current Config page state."""
        config_page = self.master.pages[0]
        try:
            layer_count = int(config_page.config_values.get("number_of_layers", "1"))
        except ValueError:
            layer_count = 1
        return config_page.sensor_design_backend.get_total_channel_count(layer_count)

    def _start_polling(self, device):
        if getattr(self, '_poll_thread', None) is not None and self._poll_thread.is_alive():
            self._stop_polling.set()
            self._poll_thread.join(timeout=0.25)

        self._stop_polling = threading.Event()
        self._poll_thread = threading.Thread(target=self._poll_device, args=(device, self._stop_polling), daemon=True)
        self._poll_thread.start()

    def _start_device(self):
        device = self.master.active_device
        config_page = self.master.pages[0]

        if device is None or not device.is_open:
            self.status_var.set("Connect to a device before starting.")
            return

        if device.running:
            self.status_var.set("Device is already running.")
            return

        incomplete_layers = config_page.get_incomplete_layers()
        if incomplete_layers:
            layer_list = ", ".join(str(layer_number) for layer_number in incomplete_layers)
            self.status_var.set(
                "Cannot start: every layer must have both a configuration name and a sensor design "
                f"(incomplete layer(s): {layer_list})."
            )
            return

        # NC must cover every sensing point across all configured layers, computed fresh each start.
        channel_count = self._compute_channel_count()

        if channel_count == 0:
            self.status_var.set("No sensing points configured - select sensor designs on the Config page first.")
            return

        device.change_config_string(f"NC:{channel_count}, SP:10")
        device.set_up_channels()
        device.start_device()
        self._start_polling(device)
        self.master.pages[0].set_device_running_state(device.running)

        # Reflect the config string actually sent to the device, not the stale scan-time snapshot.
        self._refresh_device_dropdown_entry(self.device_dropdown.current(), device)
        self.status_var.set(f"Running with {channel_count} channel(s). {device}")

    def refresh_from_config(self):
        """Keep the device's channel count in sync as soon as sensor designs change on the Config page."""
        super().refresh_from_config()

        device = self.master.active_device
        if device is None or not device.is_open:
            return

        channel_count = self._compute_channel_count()
        if channel_count == 0:
            return

        # Only reconfigure when the channel count has actually changed, so idle browsing
        # of the config page doesn't needlessly restart an already-correct device.
        if device.num_channels == channel_count and device.channel_collection:
            return

        was_running = device.running
        if was_running:
            self._stop_polling.set()

        device.restart_with_new_config(f"NC:{channel_count}, SP:10")

        if device.running:
            self._start_polling(device)
            self._refresh_device_dropdown_entry(self.device_dropdown.current(), device)
            self.status_var.set(f"Running with {channel_count} channel(s). {device}")

    def _poll_device(self, device, stop_event):
        # Runs on a background thread so the GUI stays responsive while reading serial data.
        while not stop_event.is_set() and device.running:
            device.receive_serial()
            time.sleep(self.POLL_INTERVAL_SECONDS)

    def _stop_device(self):
        device = self.master.active_device
        if device is None or not device.running:
            self.status_var.set("Device is not running.")
            return

        if getattr(self, '_poll_thread', None) is not None and self._poll_thread.is_alive():
            self._stop_polling.set()
            self._poll_thread.join(timeout=0.25)
        device.stop_device()
        self.master.pages[0].set_device_running_state(device.running)
        self.status_var.set("Device stopped.")
