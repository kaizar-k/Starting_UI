"""
The following function gives the user the choice of saving channel data to
a csv file.
"""

from tkinter import messagebox as mb
from tkinter import filedialog
import csv

def csv_saver(channel_list):

    res = mb.askquestion('Save', 'Save experiment data?')

    if res == "yes":

        nc = len(channel_list)-1
        data_lengths = [len(channel.return_raw_data()) for channel in channel_list]
        data_length = max(data_lengths) if data_lengths else 0
        data_container = {}

        for k in range(nc+1):
            list_name =f"channel_{k}"
            channel_data = channel_list[k].return_raw_data()
            data_container[list_name] = channel_data

        file_path = (filedialog.asksaveasfilename(defaultextension=".csv",
                                                  filetypes=[("csv file",
                                                              ".csv")], ))

        with open(file_path, 'w', newline='') as csvfile:
            csvfile.write("sep=,\n")
            writer = csv.writer(csvfile, delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)
            writer.writerow([])
            writer.writerow([f'{nc}-channel data'])
            writer.writerow([])

            title_row = []
            for i in range(0,nc+1):
                uom = channel_list[i].uom
                title_row.append(f'Channel-{i} Data - {uom}')

            writer.writerow(title_row)
            writer.writerow([])

            for i in range(data_length):
                newrow = []
                for j in range(nc+1):
                    if channel_list[j].selected is True:
                        channel_data = data_container[f"channel_{j}"]
                        datapoint = channel_data[i] if i < len(channel_data) else ''
                    else:
                        # If the channel is not selected, write 'X'.
                        datapoint = 'X'
                    newrow.append(datapoint)
                writer.writerow(newrow)



















