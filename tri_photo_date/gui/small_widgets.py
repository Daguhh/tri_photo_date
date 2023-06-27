from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QPushButton, QCheckBox, QRadioButton, QCheckBox, QHBoxLayout, QLabel, QListWidgetItem, QComboBox

from tri_photo_date.config.config_paths import LOCALES_DIR

def set_global_config(lang='en', size=1, mode=None):

    import gettext

    trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
    trad.install()

    global _
    _ = trad.gettext  # Greek

class ComboBox(QComboBox):
    def __init__(self, callback):
        super().__init__()

        def combo_changed():
            callback(self.currentText())

        model = self.model()

        # Add items to the QComboBox and set the foreground color
        options = (_("toutes"), _("en commun"), _("utiles"))
        for option in options:
            entry = QStandardItem(option)
            model.appendRow(entry)

        self.setCurrentIndex(2)

        # Connect QComboBox signal to combo_changed() slot
        self.currentIndexChanged.connect(combo_changed)

def OptionBool(QHBoxLayout):
    def __init__(self, label, tooltip):
        super().__init__()

        self.addWidget(QLabel(f"{label}:"))

        self.checkbox = QCheckBox()
        self.checkbox.setToolTip(tooltip)
        self.addWidget(self.checkbox)

class ItemWidget(QListWidgetItem):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(text)


class simplePushButton(QPushButton):
    def __init__(
        self, layout, callback="to remove", label="", tooltip="", color="darkGreen"
    ):
        super().__init__()

        self.setText(label)
        self.setToolTip(tooltip)
        layout.addWidget(self)


class simpleStopButton(QPushButton):
    def __init__(self, layout, callback):
        super().__init__()

        self.setText(_("Interrompre"))
        layout.addWidget(self)
        self.clicked.connect(callback)
        self.setHidden(True)


class simpleCheckBox(QCheckBox):
    def __init__(self, parent_layout=None, label="", tooltip=""):
        super().__init__()
        self.setText(label)
        self.setToolTip(tooltip)
        if parent_layout is not None:
            parent_layout.addWidget(self)


class MyRadioButton(QRadioButton):
    def __init__(self, parent, label="", tooltip=""):
        super().__init__(parent)
        self.setText(label)
        self.setToolTip(tooltip)
