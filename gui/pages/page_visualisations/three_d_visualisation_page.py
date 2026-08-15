from gui.pages.objects.page_object import PageObject


class ThreeDVisualisationPage(PageObject):
    """Minimal placeholder page for the 3D force visualisation view."""

    def __init__(self, master, title_text, page_index, pop_up_index):
        super().__init__(master, title_text, page_index, pop_up_index)

    def refresh_from_config(self):
        """Hook for config updates; this page currently has no dynamic content to refresh."""
        pass
