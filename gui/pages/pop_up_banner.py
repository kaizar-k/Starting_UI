import tkinter as tk

from gui.controls.z_Label import ZLabel
from gui.controls.z_button import ZButton
from gui.frames.container_frame import ContainerFrame
from gui.colour_scheme import *
from gui.font_definitions import *
from gui.frames.label_frame import LabelFrame

# This will be the parent class for all the pop-up windows

class PopUpObject(tk.Frame):
    def __init__(self, master, title_text, page_index, pop_up_index):
        tk.Frame.__init__(self, master)
        self.master = master
        self.title_text = title_text
        self.frame_width_ratio = 4
        self.page_index = page_index
        self.pop_up_page_index = pop_up_index

        screen_height = self.winfo_screenheight()
        screen_width = self.winfo_screenwidth()

        self.configure(width=screen_width/self.frame_width_ratio, height=screen_height, bg=BACKGROUND)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.hide_frame_container = ContainerFrame(self)
        self.hide_frame_container.configure(width=(screen_width / self.frame_width_ratio)/10, height=screen_height)
        self.main_container = ContainerFrame(self)
        self.main_container.configure(width=((screen_width / self.frame_width_ratio )/ 10)*9, height=screen_height)

        # pack layer 2
        self.hide_frame_container.pack(side='left', fill='y', expand=False)
        self.main_container.pack(side='left', fill='y')

        # pack a single toggle button into the parameters button frame
        self.pop_up_button = ZButton(self.hide_frame_container, text='>')
        self.pop_up_button.configure(font=TITLE_FONT)
        self.pop_up_button.pack(fill='y', expand=True)
        self.pop_up_button.configure(width=1, height=int(screen_height))

        # layout - layer 2
        self.title_frame = ContainerFrame(self.main_container)
        self.main_area_frame = ContainerFrame(self.main_container)

        # pack layer 2
        self.title_frame.pack(side='top', fill='x', expand=True)
        self.main_area_frame.pack(side='top', fill='both', expand=True)

        self.main_area_frame.configure(width=((screen_width / self.frame_width_ratio )/ 10)*9, height=screen_height)

        # pack title of page into title_frame
        self.title = LabelFrame(self.title_frame, label_text=self.title_text)
        self.title.pack(side='top', fill='both', expand=True, anchor='w')