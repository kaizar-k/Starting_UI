# this is an object for saving in-coming data from devices
class ChannelObject:
    def __init__(self, uom='Resistance (Ohms)'):
        self.data = []
        self.uom = uom


    def __str__(self):
        str_to_return = 'Channel Object\n'
        str_to_return += f' UOM: {self.uom}\n'
        str_to_return += f' Data: {len(self.data)}\n'

        return str_to_return


    def __repr__(self):
        str_to_return = f' UOM: {self.uom}\n'
        str_to_return += f' Data: {len(self.data)}\n'

        return str_to_return


    def add_value(self, value:float):
        self.data.append(value)


    def clear(self):
        self.data = []