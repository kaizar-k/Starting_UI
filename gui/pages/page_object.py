import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont

from gui.controls.zLabel import ZLabel
from gui.controls.z_button import ZButton
from gui.font_definitions import TITLE_FONT
from gui.frames.container_frame import ContainerFrame


# This will be the parent class for all the pages

class PageObject(tk.Frame):
    def __init__(self, master, title_text):
        tk.Frame.__init__(self, master)
        self.title_text = title_text
        screen_height = self.winfo_screenheight()
        screen_width = self.winfo_screenwidth()
        self.configure(bg='green')

        # we want this to have a header row with a logo and a title of a fixed height but varying width

        # layout - layer 1
        self.title_frame = ContainerFrame(self)
        self.title_frame.configure(height=int(screen_height * 0.1))
        self.main_area_frame = ContainerFrame(self)
        self.main_area_frame.configure(height=int(screen_height * 0.75), bg='blue')
        self.footer_frame = ContainerFrame(self)
        self.footer_frame.configure(height=int(screen_height * 0.1))

        # pack layer 1
        self.title_frame.pack(side='top', fill='x')
        self.main_area_frame.pack(side='top', fill='x')
        self.footer_frame.pack(side='top', fill='x')

        # layout of main area frame - layer 2
        self.figure_area_frame = ContainerFrame(self.main_area_frame)
        self.figure_area_frame.configure(width=(screen_width / 40)*39, height=int(screen_height * 0.75))
        self.parameters_button_frame = ContainerFrame(self.main_area_frame)
        self.parameters_button_frame.configure(width=screen_width / 40, height=int(screen_height * 0.75))

        # pack layer 2
        self.figure_area_frame.pack(side='left', fill='y')
        self.parameters_button_frame.pack(side='left', fill='y')

        # pack a single toggle button into the parameters button frame
        self.pop_up_button = ZButton(self.parameters_button_frame, text="<")
        self.pop_up_button.configure(font=TITLE_FONT)
        self.pop_up_button.pack(fill='both', expand=True)

        # pack title of page into title_frame
        self.title = ZLabel(self.title_frame, text=self.title_text)
        self.title.pack(side='left', fill='both', expand=False, anchor='w')
        self.title.configure(font=TITLE_FONT)

        # Page tabs across the top, beneath the header

        # under this we want a left and a right hand side

        # The right hand side will be a series of tabs also (different on each page)
        # which will pop up config banners

        # As well as a start / stop experiment button
        # an export csv of raw data, and export png of current figure buttons

        # the left hand side will be

        #