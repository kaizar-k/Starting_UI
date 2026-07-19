import serial
from serial_interface_library.channel_object import ChannelObject

# this will be an object for interfacing with individual connected devices
class DeviceObject(serial.Serial):
    def __init__(self, config_str='NC:1, SP:2', com_port='COM4', baud_rate=115200):
        super().__init__()

        # device settings
        self.connected = False
        self.port = com_port
        self.baudrate = baud_rate
        self.config_str = config_str

        # channel values / data
        self.time_values = []
        self.channels = []
        self.add_channel()


    def __str__(self):
        str_to_return = '\nDevice Object:\n'
        str_to_return += f' com port: {self.port}\n'
        str_to_return += f' baud rate: {self.baudrate}\n'
        str_to_return += f' channels: {len(self.channels)}\n'
        str_to_return += f'     data points: {len(self.time_values)}\n'

        return str_to_return


    def __repr__(self):
        str_to_return = f' com port: {self.port}\n'
        str_to_return += f' baud rate: {self.baudrate}\n'
        str_to_return += f' channels: {len(self.channels)}\n'
        str_to_return += f'     data points: {len(self.time_values)}\n'

        return str_to_return


    def add_channel(self, uom='Resistance (Ohms)'):
        self.channels.append(ChannelObject(uom))


    def remove_channel(self, index=None):
        if len(self.channels) > 1:
            if index is None:
                self.channels.pop()
            else:
                self.channels.pop(index)


    def check_connection(self):
        self.connected = False
        if self.is_open:
            self.connected = True

        return self.connected


    def connect(self):
        try:
            self.open()
            self.connected = True
            print(f'Connected on port: {self.port}')

        except serial.SerialException:
            self.connected = False
            print(f'Could not connect port: {self.port}')

        return self.connected


    def send_command(self, command:str):
        success = False
        command += '\n'

        try:
            self.write(bytes(command,'utf-8'))
            success = True

        except serial.SerialException:
            print(f'Could not send command: {command}')

        return success


    def start_experiment(self):
        start_message = 'start'
        start_message += f', {self.config_str}'
        start_message += '\n'

        self.send_command(start_message)


    def stop_experiment(self):
        stop_message = 'stop\n'
        self.send_command(stop_message)


    def receive_data(self):
        to_return = True
        return_data = False
        data = None

        # TODO if multiple lines are waiting then intake all lines, instead of just one.
        if self.in_waiting > 0:
            data = self.readline()

        if data:
            data = data.decode('utf-8').split(', ', -1)

            # less than num_channels + 1 = command
            if len(data) < len(self.channels) + 1:
                print(data)
                return_data = True

            # equal to num_channels + 1 = data
            if len(data) == len(self.channels) + 1:
                self.time_values.append(int(data[0]))
                for i in range(1, len(self.channels)):
                    self.channels[i].add_value(float(data[i+1]))

            # more than num_channels + 1 = error
            if len(data) > len(self.channels) + 1:
                print('ERROR: Incomming data string too long')

        else:
            to_return = False

        if return_data:
            return to_return, data
        else:
            return to_return, return_data