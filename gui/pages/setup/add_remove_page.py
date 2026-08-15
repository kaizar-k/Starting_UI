import tkinter as tk
from tkinter import ttk

from backend.dropdown_backend import DropdownData
from gui.pages.setup.add_config_section import AddConfigSection
from gui.pages.setup.add_curve import AddCalibrationCurveSection
from gui.pages.setup.add_options_section import AddOptionsSection
from gui.pages.objects.page_object import PageObject
from gui.pages.setup.remove_config_section import RemoveConfigSection
from gui.pages.setup.remove_curve import RemoveCalibrationCurveSection
from gui.pages.setup.remove_options_section import RemoveOptionsSection


class AddRemovePage(PageObject):
    """Main page for managing add/remove configuration presets."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

        dropdown_data = DropdownData()
        self.category_names = dropdown_data.get_category_names()
        self.category_options = dropdown_data.get_options_by_category()

        self.form_frame = ttk.Frame(self.main_area_frame, padding=20)
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.form_frame.configure(borderwidth=1, relief="solid")

        self.add_config_section = AddConfigSection(self.form_frame, self.category_options, self._refresh_sections)
        self.remove_config_section = RemoveConfigSection(self.form_frame, self.category_options)
        self.add_calibration_curve_section = AddCalibrationCurveSection(self.form_frame, self._refresh_sections)
        self.remove_calibration_curve_section = RemoveCalibrationCurveSection(self.form_frame, self._refresh_sections)
        self.add_options_section = AddOptionsSection(self.form_frame, self.category_options, self._refresh_sections)
        self.remove_options_section = RemoveOptionsSection(self.form_frame, self.category_options, self._refresh_sections)

        self._schedule_scroll_region_update()

    def _refresh_sections(self):
        self.add_config_section.refresh()
        self.remove_config_section.refresh()
        self.add_calibration_curve_section.refresh()
        self.remove_calibration_curve_section.refresh()
        self.remove_options_section.refresh()

        app = self.winfo_toplevel()
        if hasattr(app, "pages") and app.pages:
            config_page = app.pages[0]
            if hasattr(config_page, "refresh_from_config"):
                config_page.refresh_from_config()
