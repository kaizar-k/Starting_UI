import tkinter as tk
import math
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
        self.main_area_frame.configure(bg=BACKGROUND)
        self.main_canvas.create_window((0, 0), window=self.main_area_frame, anchor='nw', tags=('main_area_window',))

        self.title_frame.pack(side='top', fill='x')
        self.menu_frame.pack(side='top', fill='x')
        self.main_scroll_container.pack(side='top', fill='both', expand=True)
        self.main_canvas.pack(side='left', fill='both', expand=True)
        self.main_scrollbar.pack(side='right', fill='y')

        self.main_canvas.bind('<Configure>', self._on_content_configure)
        self.main_area_frame.bind('<Configure>', self._on_content_configure)
        self.after(100, self._on_content_configure)

        # Create the top navigation buttons needed for the current app flow.
        self.page_buttons = []
        button_labels = ['Config', 'Device', '2D plots', '3D plots', 'Add/remove']
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

        self.force_reading_var = tk.StringVar(value="")
        self.force_reading_label = tk.Label(
            self.title_frame,
            textvariable=self.force_reading_var,
            bg=LOGO_COLOUR,
            fg=TEXT_COLOUR,
            font=HEADER_FONT,
            width=60,
            anchor="w",
        )
        # Keep this slot present even when stopped so force text length cannot shift the page title.
        self.force_reading_label.pack(side='left', fill='y', padx=(8, 8))

        # pack title of page into title_frame
        self.title = Label(self.title_frame, text=self.title_text)
        self.title.pack(side='left', fill='both', expand=True, anchor='w', padx=(0, 0))
        self.title.configure(font=TITLE_FONT, anchor='w')
        self.after(100, self._update_force_reading)

    def refresh_from_config(self):
        """Hook for pages that need to update when the config page changes."""
        self._schedule_scroll_region_update() #also changes the scroll region to fit the new content size

    def _schedule_scroll_region_update(self):
        """Recalculate the scroll region after the layout settles."""
        self.after_idle(self._on_content_configure)
        self.after(50, self._on_content_configure)

    def _on_content_configure(self, event=None):
        """Update the canvas scroll region from the current content size."""
        self.update_idletasks()
        self.main_canvas.update_idletasks()
        self.main_area_frame.update_idletasks()

        canvas_width = max(self.main_canvas.winfo_width(), self.main_area_frame.winfo_width(), 1)
        canvas_height = max(self.main_canvas.winfo_height(), 1)

        content_width = max(self.main_area_frame.winfo_reqwidth(), self.main_area_frame.winfo_width(), canvas_width)
        content_height = max(self.main_area_frame.winfo_reqheight(), self.main_area_frame.winfo_height(), canvas_height)

        self.main_canvas.itemconfigure('main_area_window', width=canvas_width)
        self.main_canvas.itemconfigure('main_area_window', height=content_height)
        self.main_canvas.configure(scrollregion=(0, 0, content_width, content_height))

    def _update_force_reading(self):
        """Show live force and derived applicator pressure from physical channel 1 while running."""
        device = getattr(self.master, "active_device", None)
        if device is None or not device.running or len(device.channel_collection) <= 1:
            self.force_reading_var.set("")
        else:
            samples = device.channel_collection[1].return_raw_data()
            if samples:
                try:
                    force_grams = float(samples[-1])
                    applicator_area = float(
                        self.master.pages[0].config_values.get("force_gauge_applicator_area", "0")
                    )
                    if not math.isfinite(applicator_area) or applicator_area <= 0:
                        raise ValueError

                    # Convert grams-force per square millimetre to Pascals for the header readout.
                    pressure_pa = (force_grams / applicator_area) * 9806.65
                    self.force_reading_var.set(
                        f"Force: {force_grams:.2f} g    Pressure: {pressure_pa:.2f} Pa"
                    )
                except (TypeError, ValueError):
                    self.force_reading_var.set("Force: -- g    Pressure: -- Pa")
            else:
                self.force_reading_var.set("Force: -- g    Pressure: -- Pa")

        self.after(100, self._update_force_reading)