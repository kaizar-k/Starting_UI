from tkinter import font as tkFont

# Delay font creation until the first widget is built so GUI modules can be imported
# safely before a Tk root exists, such as in test scripts and standalone imports.

_FONT_CACHE = {}


def _get_font(font_name, size, weight=None):
    key = (font_name, size, weight)
    if key not in _FONT_CACHE:
        kwargs = {'family': font_name, 'size': size}
        if weight is not None:
            kwargs['weight'] = weight
        _FONT_CACHE[key] = tkFont.Font(**kwargs)
    return _FONT_CACHE[key]


def get_title_font():
    return _get_font('Segoe UI', 20, 'bold')


def get_header_font():
    return _get_font('Segoe UI', 10, 'bold')


def get_text_font():
    return _get_font('Segoe UI', 9)


# Backward-compatible names for existing calls that still use the old globals.
TITLE_FONT = None
HEADER_FONT = None
TEXT_FONT = None
