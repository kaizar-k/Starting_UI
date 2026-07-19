# This is a test script to interact with an Arduino connected with usb
# via the serial interface class
# allowing the user to configure visualisation and output settings based on a generic GUI
from gui.gui_control import TKinterApp
from serial_interface_library.serial_interface import SerialInterface

SI = SerialInterface()
app = TKinterApp()

def detect_ports():
    # this function detects available ports and then prints them to the terminal
    SI.find_devices()
    print(SI)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    detect_ports()
    app.mainloop()

