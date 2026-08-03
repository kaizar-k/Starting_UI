from gui.pages.page_object import PageObject
from gui.controls.z_button import ZButton

class MainPage(PageObject):
    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        self.export_csv_button = ZButton(self.footer_frame, text="Export CSV")
        self.export_csv_button.pack(side='left', fill='both', expand=True)
        self.export_png_button = ZButton(self.footer_frame, text="Export PNG")
        self.export_png_button.pack(side='left', fill='both', expand=True)
        self.export_start_button = ZButton(self.footer_frame, text="Start / stop experiment")
        self.export_start_button.pack(side='left', fill='both', expand=True)
