from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget, QSizePolicy

from tri_photo_date.config.config_paths import LOCALES_DIR
from tri_photo_date.utils.constants import GUI_ADVANCED, GUI_NORMAL, GUI_SIMPLIFIED

def set_global_config(lang='en', size=1, mode=GUI_ADVANCED):

    import gettext

    trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
    trad.install()

    global _
    _ = trad.gettext  # Greek


class CollapsibleFrame(QFrame):
    widget_list = []

    def __init__(self, label, *args, color="blue", parent=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName(f"myFrame_{color}")
        self.setStyleSheet(
            f"#myFrame_{color}"
            + " { padding: 15px 15px 15px 15px; border: 2px solid "
            + color
            + "}"
        )
        self.adjustSize()
        self.setContentsMargins(6, 14, 6, 6)

        self.layout = QHBoxLayout()
        self.widget = QWidget()
        self.layout.addWidget(self.widget)

        CollapsibleFrame.widget_list += [self]
        label_frame = QLabel(self)
        label_frame.setObjectName(f"myLabel_{color}")
        label_frame.setStyleSheet(f"padding: 40px 10px; color:{color}")
        label_frame.setMinimumWidth(500)
        # label_frame.adjustSize()
        label_frame.mousePressEvent = self.label_clicked
        self.label = label_frame
        self.label_txt = label
        self.label.setText("▼  " + self.label_txt)
        super().setLayout(self.layout)

    def setLayout(self, *args, **kwargs):
        self.widget.setLayout(*args, **kwargs)

    def collapse(self, is_collasped=True):
        if not is_collasped:
            self.widget.setVisible(True)
            self.label.setText("▼  " + self.label_txt)
            self.setFixedHeight(self.layout.sizeHint().height() + 15)

        else:
            self.widget.setVisible(False)
            self.label.setText("▶  " + self.label_txt)
            self.setFixedHeight(self.layout.sizeHint().height() + 15)

        self.adjustSize()
        self.setContentsMargins(6, 14, 6, 1)

    def label_clicked(self, event):
        if self.widget.isVisible():
            self.collapse(True)
        else:
            self.collapse(False)

    @classmethod
    def collapse_all(cls):
        for wdg in cls.widget_list:
            wdg.collapse(True)

    @classmethod
    def uncollapse_all(cls):
        for wdg in cls.widget_list:
            wdg.collapse(False)


class PreviewCollapsibleFrame(QFrame):
    widget_list = []

    def __init__(self, label, color, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName(f"myFrame_{color}")
        self.setStyleSheet(
            f"#myFrame_{color}" + " { padding: 15px; border: 2px solid " + color + "}"
        )
        self.setContentsMargins(6, 14, 6, 1)
        #self.setToolTip(_("Afficher l'aperçu"))

        self.layout = QHBoxLayout()
        self.widget = QWidget()
        self.layout.addWidget(self.widget)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        if label:
            CollapsibleFrame.widget_list += [self]
            label_frame = QLabel(self)
            label_frame.setObjectName(f"myLabel_{color}")
            label_frame.setStyleSheet(f"padding: 10px; color:{color}")
            label_frame.mousePressEvent = self.label_clicked
            self.label = label_frame
            self.label_txt = label
            self.label.setText("\n".join(list("◀")))
        super().setLayout(self.layout)

    def setLayout(self, *args, **kwargs):
        self.widget.setLayout(*args, **kwargs)

    def setWidget(self, widget):
        self.widget = widget
        self.layout.addWidget(self.widget)

    def collapse(self, is_collasped=True):
        if not is_collasped:
            self.widget.setVisible(True)
            self.label.setText("▶  " + self.label_txt)
            #self.setToolTip(_("Cacher l'aperçu"))
            self.setMinimumSize(400, 200)
            self.setMaximumSize(2000, 2000)
            self.parent().parent().parent().resize(1000, 790)
        else:
            self.widget.setVisible(False)
            self.label.setText("◀")
            #self.setToolTip(_("Afficher l'aperçu"))
            self.setMinimumSize(30, 200)
            self.setMaximumSize(30, 2000)
            self.parent().parent().parent().resize(400, 790)
        self.adjustSize()

        self.setContentsMargins(6, 14, 6, 1)

    def label_clicked(self, event):
        if self.widget.isVisible():
            self.collapse(True)
        else:
            self.collapse(False)

    @classmethod
    def collapse_all(cls):
        for wdg in cls.widget_list:
            wdg.collapse(True)

    @classmethod
    def uncollapse_all(cls):
        for wdg in cls.widget_list:
            wdg.collapse(False)
