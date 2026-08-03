import tkinter as tk
from functools import partial
from gui.colour_scheme import BACKGROUND, LOGO_COLOUR

class TKinterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # these are here because tk.font cannot be imported before the main window is active
        from gui.pages.page_object import PageObject
        from gui.pages.pop_up_banner import PopUpObject
        from gui.pages.main_page import MainPage

        # set up window Title and geometry
        self.title('This is a test Tkinter Window with the aim of creating a generalise gui framework for data acquisition')

        # set the position of the window to the center of the screen
        self.geometry(f'{self.winfo_screenwidth()}x{self.winfo_screenheight()}+{0}+{0}')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # in here we will add all the pages and how they are controlled
        self.pages = []
        page_index = 0

        # add main page (page 0)
        self.pages.append(MainPage(self, "Main Page", page_index, page_index+1)) # temp main page
        self.pages.append(PopUpObject(self, 'Main page popup', page_index, page_index+1)) # temp popup window

        # add page 1
        page_index += 2
        self.pages.append(PageObject(self, "Page 1", page_index, page_index+1)) # temp page
        self.pages.append(PopUpObject(self, 'Page 1 popup', page_index, page_index+1)) # temp popup window

        # add page 2
        page_index += 2
        self.pages.append(PageObject(self, "Page 2", page_index, page_index+1)) # temp page
        self.pages.append(PopUpObject(self, 'Page 2 popup', page_index, page_index+1)) # temp popup window

        # add page 3
        page_index += 2
        self.pages.append(PageObject(self, "Page 3", page_index, page_index+1)) # temp page
        self.pages.append(PopUpObject(self, 'Page 3 popup', page_index, page_index+1)) # temp popup window

        # add page 4
        page_index += 2
        self.pages.append(PageObject(self, "Page 4", page_index, page_index+1)) # temp page
        self.pages.append(PopUpObject(self, 'Page 4 popup', page_index, page_index+1)) # temp popup window

        self.show_frame(0) # makes sure main page is top page

        print(f'number of pages: {len(self.pages)}')

        for page in self.pages:
            if type(page) == PopUpObject:
                page.grid(row=0, column=0, sticky="ne")
                page.pop_up_button.configure(command=partial(self.show_frame, page.page_index))

            if type(page) == PageObject or type(page) == MainPage:
                page.grid(row = 0, column = 0, sticky ="nsew")
                page.title.configure(bg=LOGO_COLOUR)
                page.pop_up_button.configure(command=partial(self.show_frame, page.pop_up_page_index))

                button_index = 0
                associated_page_index = 0
                for button in page.page_buttons:
                    button.configure(command=partial(self.show_frame, self.pages[associated_page_index].page_index))
                    if button_index == 0 and page.page_index == 0 or button_index == page.page_index / 2:
                        button.configure(bg=LOGO_COLOUR)
                    button_index += 1
                    associated_page_index += 2


    def show_frame(self, cont):
        page = self.pages[cont]
        page.tkraise()
