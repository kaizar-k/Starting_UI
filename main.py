# This is a test script to interact with an Arduino connected with usb
# via the serial interface class
# allowing the user to configure visualisation and output settings based on a generic GUI
from gui.gui_control import TKinterApp

app = TKinterApp()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.mainloop()

