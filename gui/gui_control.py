import tkinter as tk

class TKinterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # these are here because tk.font cannot be imported before the main window is active
        from gui.pages.page_object import PageObject
        from gui.pages.pop_up_banner import PopUpObject

        # set up window Title and geometry
        self.title('This is a test Tkinter Window with the aim of creating a generalise gui framework for data acquisition')

        # set the position of the window to the center of the screen
        self.geometry(f'{self.winfo_screenwidth()}x{self.winfo_screenheight()}+{0}+{0}')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # in here we will add all the pages and how they are controlled
        self.pages = []
        # add main page
        self.pages.append(PageObject(self, "Generic page object")) # temp main page
        self.pages.append(PopUpObject(self, 'Generic configuration pop-up')) # example popup window
        self.show_frame(0) # makes sure main page is top page

        for page in self.pages:
            if type(page) == PopUpObject:
                page.grid(row=0, column=0, sticky="ne")
                page.pop_up_button.configure(command = lambda: self.show_frame(0))

            if type(page) == PageObject:
                page.grid(row = 0, column = 0, sticky ="nsew")
                page.pop_up_button.configure(command = lambda: self.show_frame(1))






    def show_frame(self, cont):
        page = self.pages[cont]
        page.tkraise()
