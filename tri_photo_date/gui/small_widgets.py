from PyQt5.QtWidgets import QPushButton, QCheckBox, QRadioButton


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
