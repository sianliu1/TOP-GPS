# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QMainWindow,
    QMenuBar, QPushButton, QScrollBar, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.widget_2 = QWidget(self.centralwidget)
        self.widget_2.setObjectName(u"widget_2")
        self.btn_input_data = QPushButton(self.widget_2)
        self.btn_input_data.setObjectName(u"btn_input_data")
        self.btn_input_data.setGeometry(QRect(50, 50, 151, 41))
        font = QFont()
        font.setPointSize(12)
        self.btn_input_data.setFont(font)
        self.btn_autorec = QPushButton(self.widget_2)
        self.btn_autorec.setObjectName(u"btn_autorec")
        self.btn_autorec.setGeometry(QRect(50, 150, 151, 41))
        self.btn_autorec.setFont(font)

        self.horizontalLayout_4.addWidget(self.widget_2)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.win1 = QWidget(self.centralwidget)
        self.win1.setObjectName(u"win1")

        self.horizontalLayout.addWidget(self.win1)

        self.Bar1 = QScrollBar(self.centralwidget)
        self.Bar1.setObjectName(u"Bar1")
        self.Bar1.setOrientation(Qt.Orientation.Vertical)

        self.horizontalLayout.addWidget(self.Bar1)


        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.win2 = QWidget(self.centralwidget)
        self.win2.setObjectName(u"win2")

        self.horizontalLayout_2.addWidget(self.win2)

        self.Bar2 = QScrollBar(self.centralwidget)
        self.Bar2.setObjectName(u"Bar2")
        self.Bar2.setOrientation(Qt.Orientation.Vertical)

        self.horizontalLayout_2.addWidget(self.Bar2)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 1, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.win3 = QWidget(self.centralwidget)
        self.win3.setObjectName(u"win3")

        self.horizontalLayout_3.addWidget(self.win3)

        self.Bar3 = QScrollBar(self.centralwidget)
        self.Bar3.setObjectName(u"Bar3")
        self.Bar3.setOrientation(Qt.Orientation.Vertical)

        self.horizontalLayout_3.addWidget(self.Bar3)


        self.gridLayout.addLayout(self.horizontalLayout_3, 1, 0, 1, 1)

        self.win4 = QWidget(self.centralwidget)
        self.win4.setObjectName(u"win4")

        self.gridLayout.addWidget(self.win4, 1, 1, 1, 1)


        self.horizontalLayout_4.addLayout(self.gridLayout)

        self.label_plate = QWidget(self.centralwidget)
        self.label_plate.setObjectName(u"label_plate")
        self.label_menu = QWidget(self.label_plate)
        self.label_menu.setObjectName(u"label_menu")
        self.label_menu.setGeometry(QRect(20, 20, 221, 471))
        self.verticalLayout = QVBoxLayout(self.label_menu)
        self.verticalLayout.setObjectName(u"verticalLayout")

        self.horizontalLayout_4.addWidget(self.label_plate)

        self.horizontalLayout_4.setStretch(0, 2)
        self.horizontalLayout_4.setStretch(1, 10)
        self.horizontalLayout_4.setStretch(2, 2)

        self.gridLayout_2.addLayout(self.horizontalLayout_4, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1920, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.btn_input_data.setText(QCoreApplication.translate("MainWindow", u"\u8f93\u5165\u6570\u636e", None))
        self.btn_autorec.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52a8\u91cd\u5efa", None))
    # retranslateUi

