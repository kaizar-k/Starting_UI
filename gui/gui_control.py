import tkinter as tk
from functools import partial

from gui.colour_scheme import LOGO_COLOUR


class TKinterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # These imports are done here so Tk fonts are available after the main window exists.
        from gui.pages.page_object import PageObject
        from gui.pages.pop_up_banner import PopUpObject
        from gui.pages.config_page import ConfigPage

        self.title('DZP Sensor Force Visualisation Tool')
        self.geometry(f'{self.winfo_screenwidth()}x{self.winfo_screenheight()}+{0}+{0}')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.pages = []
        page_index = 0

        # Add the configuration page as the first screen.
        self.pages.append(ConfigPage(self, 'Configuration', page_index, page_index + 1))
        self.pages.append(PopUpObject(self, 'Configuration popup', page_index, page_index + 1))

        # Add a couple of generic pages as placeholders.
        #we increment the page index by 2 to account for the pop-up page that is added alongside each main page
        page_index += 2 
        self.pages.append(PageObject(self, '2D Force Visualisation per Layer', page_index, page_index + 1))
        self.pages.append(PopUpObject(self, 'Options', page_index, page_index + 1))

        page_index += 2
        self.pages.append(PageObject(self, '3D Force Visualisation (All Layers)', page_index, page_index + 1))
        self.pages.append(PopUpObject(self, 'Options', page_index, page_index + 1))

        for page in self.pages:
            if type(page) == PopUpObject:
                page.grid(row=0, column=0, sticky='ne')
                page.pop_up_button.configure(command=partial(self.show_frame, page.page_index))

            if type(page) == PageObject or type(page) == ConfigPage:
                page.grid(row=0, column=0, sticky='nsew')
                page.title.configure(bg=LOGO_COLOUR)
                page.pop_up_button.configure(command=partial(self.show_frame, page.pop_up_page_index))

                button_index = 0
                associated_page_index = 0
                for button in page.page_buttons:
                    if associated_page_index < len(self.pages):
                        target_page = self.pages[associated_page_index]
                        button.configure(command=partial(self.show_frame, target_page.page_index))
                    else:
                        button.configure(command=lambda: None)

                    if button_index == 0 and page.page_index == 0 or button_index == page.page_index / 2:
                        button.configure(bg=LOGO_COLOUR)

                    button_index += 1
                    associated_page_index += 2

        self.update_idletasks()
        self.show_frame(0)

    def show_frame(self, cont):
        page = self.pages[cont]
        page.tkraise()
