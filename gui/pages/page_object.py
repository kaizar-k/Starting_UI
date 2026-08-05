import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont

from gui.page_features.colour_scheme import BACKGROUND, LOGO_COLOUR, HIGHLIGHT, TEXT_COLOUR
from gui.controls.label import Label
from gui.controls.button import Button
from gui.page_features.font_definitions import TITLE_FONT, HEADER_FONT
from gui.frames.container_frame import ContainerFrame


# This will be the parent class for all the pages

class PageObject(tk.Frame):
    def __init__(self, master, title_text, page_index, pop_up_index):
        tk.Frame.__init__(self, master)
        self.title_text = title_text
        screen_height = self.winfo_screenheight()
        screen_width = self.winfo_screenwidth()
        self.configure(bg=BACKGROUND)
        self.page_index = page_index
        self.pop_up_page_index = pop_up_index

        # we want this to have a header row with a logo and a title of a fixed height but varying width
        # layout - layer 1
        header_height = max(50, int(screen_height * 0.07))
        self.title_frame = ContainerFrame(self)
        self.title_frame.configure(height=header_height, bg=LOGO_COLOUR)
        self.title_frame.pack_propagate(False)
        self.menu_frame = ContainerFrame(self)
        self.menu_frame.configure(height=header_height)
        self.menu_frame.pack_propagate(False)

        self.main_scroll_container = ContainerFrame(self)
        self.main_scroll_container.configure(bg=BACKGROUND)

        self.main_canvas = tk.Canvas(self.main_scroll_container, bg=BACKGROUND, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(self.main_scroll_container, orient='vertical', command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        self.main_area_frame = ContainerFrame(self.main_canvas)
        self.main_area_frame.configure(height=int(screen_height * 0.75), bg=BACKGROUND)
        self.main_canvas.create_window((0, 0), window=self.main_area_frame, anchor='nw', tags=('main_area_window',))

        # pack layer 1
        self.title_frame.pack(side='top', fill='x')
        self.menu_frame.pack(side='top', fill='x')
        self.main_scroll_container.pack(side='top', fill='both', expand=True)
        self.main_canvas.pack(side='left', fill='both', expand=True)
        self.main_scrollbar.pack(side='right', fill='y')

        self.main_canvas.bind('<Configure>', self._on_canvas_configure)
        self.main_area_frame.bind('<Configure>', self._on_content_configure)
        self.after(50, self._on_content_configure)

        # Create only the three top navigation buttons needed for the current app flow.
        self.page_buttons = []
        button_labels = ['Config', '2D plots', '3D plots']
        for button_num, button_text in enumerate(button_labels):
            self.page_buttons.append(Button(self.menu_frame, text=button_text))
            self.page_buttons[button_num].configure(font=HEADER_FONT)
            self.page_buttons[button_num].pack(side='left', fill='both', expand=True)

        # Keep a popup toggle button in the title bar so the main pages can still open their popup views.
        self.pop_up_button = Button(self.title_frame, text='>')
        self.pop_up_button.configure(
            font=TITLE_FONT,
            bg=HIGHLIGHT,
            highlightbackground=HIGHLIGHT,
            activebackground='#D9ECFF',
            activeforeground=TEXT_COLOUR,
        )
        self.pop_up_button.pack(side='left', fill='y', expand=False, padx=(8, 8))

        # pack title of page into title_frame
        self.title = Label(self.title_frame, text=self.title_text)
        self.title.pack(side='left', fill='both', expand=True, anchor='w', padx=(8, 0))
        self.title.configure(font=TITLE_FONT)

    def _on_canvas_configure(self, event=None):
        """Keep the canvas scroll region and window size in sync with the page."""
        self._on_content_configure(event)

    def _on_content_configure(self, event=None):
        """Resize the canvas window when the content frame changes size."""
        canvas_width = self.main_canvas.winfo_width()
        canvas_height = self.main_canvas.winfo_height()

        if canvas_width > 1:
            self.main_canvas.itemconfigure('main_area_window', width=canvas_width)

        required_height = max(self.main_area_frame.winfo_reqheight(), canvas_height)
        self.main_canvas.itemconfigure('main_area_window', height=required_height)
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox('all'))