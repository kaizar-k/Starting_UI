# This is a test Python script to interact with an arduino connected with usb
# via the serial interface class

from serial_interface_library.serial_interface import SerialInterface
SI = SerialInterface()

def detect_ports():
    # this function detects available ports and then prints them to the terminal
    SI.find_devices()
    print(SI)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    detect_ports()

