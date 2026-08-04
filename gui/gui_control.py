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

        # Add the configuration page as the first screen without a popup companion.
        self.pages.append(ConfigPage(self, 'Configuration', 0, 0))

        # Add the two main visualisation pages and their popup companions.
        self.pages.append(PageObject(self, '2D Force Visualisation per Layer', 1, 2))
        self.pages.append(PopUpObject(self, 'Options', 2, 1))
        self.pages.append(PageObject(self, '3D Force Visualisation (All Layers)', 3, 4))
        self.pages.append(PopUpObject(self, 'Options', 4, 3))

        main_pages = [page for page in self.pages if type(page) != PopUpObject]

        for page in self.pages:
            if type(page) == PopUpObject:
                page.grid(row=0, column=0, sticky='ne')
                page.pop_up_button.configure(command=partial(self.show_frame, page.pop_up_page_index))

            if type(page) == PageObject or type(page) == ConfigPage:
                page.grid(row=0, column=0, sticky='nsew')
                page.title.configure(bg=LOGO_COLOUR)

                if type(page) == ConfigPage:
                    page.pop_up_button.pack_forget()
                else:
                    page.pop_up_button.configure(command=partial(self.show_frame, page.pop_up_page_index))

                for button_index, target_page in enumerate(main_pages):
                    button = page.page_buttons[button_index]
                    button.configure(command=partial(self.show_frame, target_page.page_index))

                    if target_page.page_index == page.page_index:
                        button.configure(bg=LOGO_COLOUR)
                    else:
                        button.configure(bg='SystemButtonFace')

        self.update_idletasks()
        self.show_frame(0)

    def show_frame(self, cont):
        page = self.pages[cont]
        page.tkraise()
