__all__ = ['enabled_if_combosel_in', 'set_enabled_from_checkbox']


def enabled_if_combosel_in(widget, combo, options):
    combo.currentTextChanged.connect(lambda text: widget.setEnabled(text in options))
    widget.setEnabled(combo.currentText() in options)


def set_enabled_from_checkbox(widget, checkbox):
    checkbox.toggled.connect(widget.setEnabled)
    widget.setEnabled(checkbox.isChecked())
