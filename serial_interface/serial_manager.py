"""
The following object handles serial interfacing for multiple
devices,
"""

import serial
import serial.tools.list_ports
from serial_interface.device_object import DeviceObject

class SerialManager:

    def __init__(self):
        # The following are lists of DeviceObjects. The first is a list
        # of devices plugged in physically, and the second is a subset of
        # the first, containing devices that are serially connected.
        self.devices = []
        self.connected_devices = []

    def __str__(self):
        return (f"Devices Plugged In: {self.devices}, "
                f"Devices Serially Connected: {self.connected_devices}")

    def find_usb_devices(self):
        ports = serial.tools.list_ports.comports()
        # Device lists are reset.
        self.devices = []
        self.connected_devices = []
        device_count = 0

        if len(ports) != 0:
            for port, desc, hwid in sorted(ports):

                if "USB" in desc or "Arduino" in desc or "ESP" in desc:
                    newdevice = DeviceObject(index=device_count, desc=desc,
                                             com_port=port)
                    self.devices.append(newdevice)
                    device_count += 1
                else:
                    print("Unidentified Device Found - Please ensure any"
                          " necessary drivers are installed")
        else:
            print("Nothing connected to ports!")

        return self.devices

    def connect_to_device(self,device_index):
        # TODO return specific error codes!!

        if len(self.devices) == 0:
            print("Please plug in devices first, and find_usb_devices!")
            return False

        elif device_index > len(self.devices) - 1 or device_index < 0:
            print("Please enter a valid device index!")
            return False

        else:
            target_device = self.devices[device_index]
            try:
                if not target_device.is_open:
                    target_device.open()
                    self.connected_devices.append(target_device)
                else: print("Device already connected!")
                return True

            except Exception as e:
                print(e)
                return False

    def check_all_connections(self):

        self.connected_devices = []

        if len(self.devices) == 0 :
            print("No recognised devices physically connected!")
        else:
            for device in self.devices:
                if device.is_open() is False:   pass
                else:   self.connected_devices.append(device)

        return self.connected_devices





