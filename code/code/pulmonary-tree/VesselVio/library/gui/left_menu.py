"""
The PyQt5 code used to build the left menu for program navigation and information.
"""



import datetime

from library.gui import qt_objects as QtO, stylesheets

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LeftMenu(QFrame):
    def __init__(self, version):
        super().__init__()

        self.setFixedWidth(90)
        self.setStyleSheet(stylesheets.MenuBackground)

        menuLayout = QtO.new_layout(self, "V", no_spacing=True)

        ## Page tabs
        self.pageTabs = QListWidget()
        self.pageTabs.setStyleSheet(stylesheets.MenuSheet)
        self.pageTabs.setFrameShape(QListWidget.NoFrame)
        self.pageTabs.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pageTabs.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pageTabs.setWordWrap(True)

        # Add menu items to our list.
        menu_items = ["Analyze", "Visualize", "Annotation Processing"]
        for item in menu_items:
            item = QListWidgetItem(str(item), self.pageTabs)
            item.setSizeHint(QSize(1, 70))
            item.setTextAlignment(Qt.AlignCenter)

        infoStrip = InfoStrip(version)

        QtO.add_widgets(menuLayout, [self.pageTabs, infoStrip, 20])


class InfoStrip(QWidget):
    def __init__(self, version):
        super().__init__()
        self.version = version
        self.setStyleSheet(stylesheets.MenuBackground)
        stripLayout = QtO.new_layout(self, "V")

        # Top row
        firstRow = QtO.new_widget()
        firstRowLayout = QtO.new_layout(firstRow, no_spacing=True)

        appVersion = QLabel(version[:-2])
        appVersion.setStyleSheet("color: white; font-weight: bold;")

        infoClick = QtO.new_button("?", self.infoclick, width=20)
        infoClick.setStyleSheet(stylesheets.InfoPush)

        QtO.add_widgets(firstRowLayout, [appVersion, 7, infoClick])

        now = datetime.datetime.now()
        year = str(now.year)
        cc = "漏" + " " + year
        ccLabel = QLabel(cc)
        ccLabel.setStyleSheet("color: white; font-weight: bold;")

        QtO.add_widgets(stripLayout, [firstRow, 5, ccLabel], "Center")

    def infoclick(self):
        text = f"""<center>
                    <b>Version {self.version[2:]}</b><br><br>
                    Vasculature analysis and visualization tool.<br><br>
                    """

        msgBox = QDialog()
        msgBox.setFixedSize(500, 275)
        msgBox.setWindowModality(Qt.NonModal)
        msgLayout = QVBoxLayout()
        msgBox.setWindowTitle("About")
        msgBox.setLayout(msgLayout)

        message = QLabel(text)
        message.setWordWrap(True)
        message.setOpenExternalLinks(True)
        msgLayout.addWidget(message)

        okButton = QPushButton("OK", msgBox)
        okButton.clicked.connect(msgBox.close)

        msgLayout.addWidget(okButton, alignment=Qt.AlignRight)

        msgBox.exec_()
