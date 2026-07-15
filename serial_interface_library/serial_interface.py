import serial
import serial.tools.list_ports
from serial_interface_library.device_object import DeviceObject

# This will be a single object for controlling all devices
class SerialInterface:
    def __init__(self):
        # set up the serial interface
        self.available_ports = []
        self.device = DeviceObject() # dummy object to test stuff
        self.devices = [] # the list of connected, or previously connected, devices


    def __str__(self):
        str_to_return = '\nSerial Interface:\n'
        port_index = 0

        if len(self.available_ports) > 0:
            for port in self.available_ports:
                str_to_return += f' Port: {port_index}\n'
                str_to_return += f'     COM: {port}\n'
        else:
            str_to_return += '  No devices found'

        return str_to_return


    def check_connected_devices(self):
        if len(self.devices) > 0:
            device_index = 0
            for device in self.devices:
                print(f'Device: {device_index} - ')
                if device.check_connection():
                    print('Connected\n')
                else:
                    print('Disconnected\n')

                print(repr(device))
        else:
            print('No devices found')


    def find_devices(self):
        self.available_ports = []
        try:
            port, desc, hwid = serial.tools.list_ports.comports()
            self.available_ports = port
        except ValueError:
            print('find_devices: No devices found')


    def connect_by_port(self, port='COM4', baud_rate=115200):
        self.device.baudrate = baud_rate
        self.device.port = port
        self.device.open()


    def connect_by_index(self, index=0, baud_rate=115200):
        self.device.baudrate = baud_rate
        self.device.port = self.available_ports[index]
        self.device.open()