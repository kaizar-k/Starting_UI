from gui.pages.pop_up_banner import PopUpObject


class Options2Page(PopUpObject):
    """Popup page for the third main page."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

    def refresh_from_config(self):
        """Hook for config updates; this page currently has no dynamic content to refresh."""
        pass
