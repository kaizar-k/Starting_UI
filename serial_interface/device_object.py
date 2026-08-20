"""
The following Object is one step up from the ChannelObject in the
hierarchy, and manipulates channels and device characteristics.
"""

import serial
import time
from serial_interface.channel_object import ChannelObject
from serial_interface.csv_saver import csv_saver


class DeviceObject(serial.Serial):

    def __init__(self,index,desc,com_port = 'COM3',config_string = "NC:1, SP:2",
                 baud_rate = 115200):
        super().__init__()

        self.index = index
        self.desc = desc
        self.port = com_port
        self.baudrate = baud_rate
        self.__config_string = config_string
        # self.channel_collection is a list of Channel Objects
        self.channel_collection = []
        # The following chunk parses the configuration string to
        # give the number of measurement channels (not inc. time).
        # It assumes that NC is the first item in the configuration string.
        configuration = self.__config_string.split(", ")
        nc = configuration[0]
        raw_nc = nc.split(":")
        self.num_channels = int(raw_nc[1])
        # Safety state variables for certain methods.
        self.running = False
        self.configured = False

    def __str__(self):
        return (f'Device Index: {self.index}, Desc: {self.desc}, '
                f'Port: {self.port}, Config: {self.__config_string}')

    def receive_serial(self):

        channel_output = []

        if self.is_open:
            if self.in_waiting > 0:
                serial_output = self.readline().decode('utf-8',
                                                       errors='ignore').strip()
                split_output = serial_output.split(", ")

                try:
                    timestamp = int(split_output[0])
                    time_channel = self.channel_collection[0]
                    time_channel.add_val(timestamp)
                    channel_output.append(timestamp)

                    for i in range (1,self.num_channels+1):
                        target_channel = self.channel_collection[i]
                        correct_form = target_channel.form

                        channel_data = split_output[i]
                        correct_val = correct_form(channel_data)
                        target_channel.add_val(correct_val)
                        channel_output.append(correct_val)


                except ValueError:
                    # Normally try and except statements are not considered
                    # good programming practice, but here they are used
                    # as a method of identifying a different type of output
                    # rather than a one-size-fits-all error catch.
                    # There are alternative ways to do this i.e. pre-parsing
                    # the string before trying to set value types.
                    channel_output = ["M",serial_output]

            else:
                # If no bytes are waiting i.e. if our query rate exceeds
                # the sampling rate, the channel waits until it can update.
                channel_output = None

        else:
            print("Please connect to device / start device first!")
            channel_output = None

        return channel_output

    def send_string(self,string_input):

        if self.is_open:
            self.write(bytes(string_input, 'utf-8'))
            print("String sent")
            return True
        else:
            print("Please serially connect to device first to send!")
            return False

    def change_config_string(self,new_config_string):
        if not self.running:
            # Same configuration string parsing as in __init__.
            # It may seem redundant to have repeated this, but we
            # cannot rely on the previous values of NC and SP
            # that we assigned at instantiation, as we wish to change them.
            self.__config_string = new_config_string
            configuration = new_config_string.split(", ")
            nc = configuration[0]
            raw_nc = nc.split(":")
            self.num_channels = int(raw_nc[1])
        else:
            print(f"Configuration string cannot be changed while "
                  f"Device{self.index} is running")

    def check_connection(self):
        return self.is_open

    def start_device(self):
        if not self.running:
            # Has several if statements in order to catch and flag any
            # user errors i.e. incorrect order of startup.
            # GUI implementations using this code can add their own
            # instructions to prevent these, but the backend error catch
            # is still recommended.

            if self.is_open:


                start_message = "start"
                start_message += f', {self.__config_string}\n'
                # The time delays are essential here.
                time.sleep(2)
                self.write(bytes(start_message, 'utf-8'))
                time.sleep(0.05)

                print(f"Device{self.index} started!")
                self.running = True
            else:
                print("Please connect to device first to start!")
                self.running = False
        else:
            print("Device already running - please stop and reconfigure before"
                  " restarting!")

        return self.running

    def stop_device(self):

        if self.is_open and self.running:
            stop_message = "stop\n"

            self.write(bytes(stop_message, 'utf-8'))
            time.sleep(0.05)
            print(f"Stopped device{self.index}")
            # Offers the user the chance to save as a csv.
            self.save_as_csv()
            # After saving, channel data is cleared.
            for ch in self.channel_collection:
                ch.clear_data()
            # Safety State Variable changed accordingly.
            self.running = False

        else:
            print("Device cannot be stopped unless serially connected and "
                  "running(started)!")

        return not self.running

    def set_up_channels(self):
        # Instantiates Channel objects - uoms are set to defaults, but can
        # be changed through redefining:
        # DeviceObject.channel_collection[n].uom = 'Amps', for example.
        # Alternatively, the setup code below can be edited directly.

        time_channel = ChannelObject(index = 0,uom = "ms",form = int)
        time_channel.add_val(0)

        self.channel_collection.append(time_channel)

        for i in range(1,self.num_channels+1):
            new_channel = ChannelObject(index = i,uom = "Ohms", form = float)
            new_channel.add_val(0.0)
            self.channel_collection.append(new_channel)
        pass

    def add_channel(self):
        # Currently not used, but provided regardless.
        if not self.running:
            new_channel = ChannelObject(index = self.num_channels + 1 )
            self.num_channels += 1
            self.channel_collection.append(new_channel)
            return True
        else:
            print("Cannot add channel during operation!")
            return False

    def remove_channel(self,channel_no):
        # Used if removing channels, in the event that there are gaps between
        # channels 1 and n.

            if self.num_channels >= channel_no > 0:
                self.channel_collection[channel_no].selected = False
                return True
            else:
                print(f"Channel number {channel_no} invalid")
                return False

    def save_as_csv(self):
        # Simply calls the csv function, and passes it the list of channels.
        csv_saver(self.channel_collection)
        pass

    def serial_clear(self):
        # A more convenient syntax of self.serial_clear for clearing the
        # input and output buffers.
        self.reset_input_buffer()
        self.reset_output_buffer()
        return True







