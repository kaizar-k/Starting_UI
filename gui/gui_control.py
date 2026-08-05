import tkinter as tk
from functools import partial

from gui.page_features.colour_scheme import LOGO_COLOUR


class TKinterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Import the page classes inside the constructor so Tk fonts are available
        # once the main window has been created.
        from gui.pages.page_object import PageObject
        from gui.pages.config_page import ConfigPage
        from gui.pages.two_d_visualisation_page import TwoDVisualisationPage
        from gui.pages.three_d_visualisation_page import ThreeDVisualisationPage
        from gui.pages.options_1_page import Options1Page
        from gui.pages.options_2_page import Options2Page

        # Set the window title and make the app fill the full screen.
        self.title('DZP Sensor Force Visualisation Tool')
        self.geometry(f'{self.winfo_screenwidth()}x{self.winfo_screenheight()}+{0}+{0}')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Store every page object in one list so navigation can use index-based lookup.
        self.pages = []

        # Create the configuration screen first. It is the default landing page.
        self.pages.append(ConfigPage(self, 'Configuration', 0, 0))

        # Add the main visualisation pages and their popup companions.
        self.pages.append(TwoDVisualisationPage(self, '2D Force Visualisation per Layer', 1, 2))
        self.pages.append(Options1Page(self, 'Options 1', 2, 1))
        self.pages.append(ThreeDVisualisationPage(self, '3D Force Visualisation (All Layers)', 3, 4))
        self.pages.append(Options2Page(self, 'Options 2', 4, 3))

        # Register every page as an observer of the config page so a config change
        # refreshes the rest of the app automatically, regardless of how many pages exist.
        config_page = self.pages[0]
        for page in self.pages[1:]:
            if page is not config_page:
                config_page.register_layer_change_observer(page.refresh_from_config)

        # Collect the main pages separately so the top navigation buttons can target them.
        main_pages = [page for page in self.pages if type(page) not in (Options1Page, Options2Page)]

        # Place each page in the main window and configure its navigation behaviour.
        for page in self.pages:
            # Popup pages open from the left-hand side so they do not overlap the main page scrollbar.
            if type(page) in (Options1Page, Options2Page):
                page.grid(row=0, column=0, sticky='nw')
                page.pop_up_button.configure(command=partial(self.show_frame, page.pop_up_page_index))

            # Main pages and the configuration page share the same base layout.
            if isinstance(page, PageObject):
                page.grid(row=0, column=0, sticky='nsew')
                page.title.configure(bg=LOGO_COLOUR)

                # The configuration page does not need the popup toggle button.
                if type(page) == ConfigPage:
                    page.pop_up_button.pack_forget()
                else:
                    page.pop_up_button.configure(command=partial(self.show_frame, page.pop_up_page_index))

                # Connect each top navigation button to the corresponding main page.
                for button_index, target_page in enumerate(main_pages):
                    button = page.page_buttons[button_index]
                    button.configure(command=partial(self.show_frame, target_page.page_index))

                    # Highlight the button for the page that is currently active.
                    if target_page.page_index == page.page_index:
                        button.configure(bg=LOGO_COLOUR)
                    else:
                        button.configure(bg='SystemButtonFace')

        # Ensure all widgets are sized correctly before the first frame is shown.
        self.update_idletasks()

        # Display the configuration page when the app starts.
        self.show_frame(0)

    def show_frame(self, cont):
        """Raise the page at the given index so it becomes visible."""
        page = self.pages[cont]
        page.tkraise()
