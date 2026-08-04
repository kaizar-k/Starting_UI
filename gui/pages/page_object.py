import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont

from gui.colour_scheme import LOGO_COLOUR
from gui.controls.z_Label import ZLabel
from gui.controls.z_button import ZButton
from gui.font_definitions import TITLE_FONT, HEADER_FONT
from gui.frames.container_frame import ContainerFrame


# This will be the parent class for all the pages

class PageObject(tk.Frame):
    def __init__(self, master, title_text, page_index, pop_up_index):
        tk.Frame.__init__(self, master)
        self.title_text = title_text
        screen_height = self.winfo_screenheight()
        screen_width = self.winfo_screenwidth()
        self.configure(bg='green')
        self.page_index = page_index
        self.pop_up_page_index = pop_up_index

        # we want this to have a header row with a logo and a title of a fixed height but varying width
        # layout - layer 1
        self.title_frame = ContainerFrame(self)
        self.title_frame.configure(height=int(screen_height * 0.1), bg=LOGO_COLOUR)
        self.menu_frame = ContainerFrame(self)
        self.menu_frame.configure(height=int(screen_height * 0.1))
        self.main_area_frame = ContainerFrame(self)
        self.main_area_frame.configure(height=int(screen_height * 0.65), bg='blue')
        self.footer_frame = ContainerFrame(self)
        self.footer_frame.configure(height=int(screen_height * 0.1))

        # pack layer 1
        self.title_frame.pack(side='top', fill='x')
        self.menu_frame.pack(side='top', fill='x')
        self.main_area_frame.pack(side='top', fill='x')
        self.footer_frame.pack(side='top', fill='x')

        # Create only the three top navigation buttons needed for the current app flow.
        self.page_buttons = []
        for button_num in range(3):
            self.page_buttons.append(ZButton(self.menu_frame, text=str(button_num)))
            self.page_buttons[button_num].configure(font=HEADER_FONT)
            self.page_buttons[button_num].pack(side='left', fill='both', expand=True)

        # Keep a popup toggle button in the title bar so the main pages can still open their popup views.
        self.pop_up_button = ZButton(self.title_frame, text='<')
        self.pop_up_button.configure(font=TITLE_FONT)
        self.pop_up_button.pack(side='right', fill='y', expand=False, padx=(0, 10))

        # pack title of page into title_frame
        self.title = ZLabel(self.title_frame, text=self.title_text)
        self.title.pack(side='left', fill='both', expand=False, anchor='w')
        self.title.configure(font=TITLE_FONT)