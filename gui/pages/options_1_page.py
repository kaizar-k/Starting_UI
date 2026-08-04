from gui.pages.pop_up_banner import PopUpObject


class Options1Page(PopUpObject):
    """Popup page for the second main page."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)
