"""
The following is the lowest (hierarchy-wise) in a collection of nested
objects designed for handling serial communications. All explanations are
written at their point of relevance.
"""

class ChannelObject:

    def __init__(self,index,uom = "Ohms",form = float):
        # Sets the index, unit of measure, type of value.
        # Self.selected is used for removing channels,
        # in the event that there are gaps between channels 1 and n.
        self.index = index
        self.uom = uom
        self.form = form
        self.selected = True
        self.__data = []

    def __str__(self):
        stringform = str(self.form)
        return f'Channel No.{self.index}, UOM: {self.uom}, Form: {stringform} '

    def add_val(self,val):
        # Ensures that only valid data is actually added.
        # Additionally, the privatisation of self.__data
        # eliminates the risk of corrupting it accidentally.
        message = True
        if type(val) is self.form:  self.__data.append(val)
        else: message = (f"Type Error - please ensure that the data being added"
                         f" to channel{self.index} is in the correct format")
        return message

    def clear_data(self):
        self.__data.clear()
        return True

    def return_raw_data(self):
        return self.__data

    def csv_data(self):
        # Currently not used, but if ever required, the method exists.
        csv_format = ''
        for reading in self.__data:
            csv_format += f'{reading}, '
        csv_format = csv_format.rstrip(', ')
        return csv_format





