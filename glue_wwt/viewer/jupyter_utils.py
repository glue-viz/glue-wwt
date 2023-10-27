from ipywidgets import Checkbox, ColorPicker, FloatText

from glue.utils import color2hex
from glue_jupyter.link import dlink, link

__all__ = ['linked_checkbox', 'linked_color_picker', 'set_enabled_from_checkbox']


def opposite(value):
    return not value


def linked_checkbox(state, attr, description='', layout=None):
    widget = Checkbox(getattr(state, 'attr', False), description=description,
                      indent=False, layout=layout)
    link((state, attr), (widget, 'value'))
    return widget


def linked_color_picker(state, attr, description='', layout=None):
    widget = ColorPicker(concise=True, layout=layout, description=description)
    link((state, attr), (widget, 'value'), color2hex)
    return widget


def linked_float_text(state, attr, default=0, description=None, layout=None):
    widget = FloatText(description=description, layout=layout)
    link((state, attr), (widget, 'value'), lambda value: value or default)
    return widget


def set_enabled_from_checkbox(widget, checkbox):
    dlink((checkbox, 'value'), (widget, 'disabled'), opposite)
