# This is a test script to interact with an Arduino connected with usb
# via the serial interface class
# allowing the user to configure visualisation and output settings based on a generic GUI
from backend.creating_dropdowns import DropdownData
from gui.gui_control import TKinterApp
from serial_interface_library.serial_interface import SerialInterface

SI = SerialInterface()
app = TKinterApp()

def detect_ports():
    # this function detects available ports and then prints them to the terminal
    SI.find_devices()
    print(SI)


def print_dropdown_data():
    dropdown_data = DropdownData()
    categories = dropdown_data.get_category_names()
    options_by_category = dropdown_data.get_options_by_category()

    print("Categories:", categories)
    for category in categories:
        print(f"{category}: {options_by_category.get(category, [])}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    detect_ports()
    print_dropdown_data()
    app.mainloop()

