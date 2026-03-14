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
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout, QMainWindow,
    QMenu, QMenuBar, QPushButton, QScrollBar,
    QSizePolicy, QSpacerItem, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        self.actionbone = QAction(MainWindow)
        self.actionbone.setObjectName(u"actionbone")
        self.actionlung = QAction(MainWindow)
        self.actionlung.setObjectName(u"actionlung")
        self.actionliver = QAction(MainWindow)
        self.actionliver.setObjectName(u"actionliver")
        self.actionbrain = QAction(MainWindow)
        self.actionbrain.setObjectName(u"actionbrain")
        self.actionstl = QAction(MainWindow)
        self.actionstl.setObjectName(u"actionstl")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
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

        self.combo_lobe = QComboBox(self.widget_2)
        self.combo_lobe.setObjectName(u"combo_lobe")
        self.combo_lobe.setGeometry(QRect(50, 250, 151, 31))
        self.combo_lobe.setFont(font)

        self.btn_watershed = QPushButton(self.widget_2)
        self.btn_watershed.setObjectName(u"btn_watershed")
        self.btn_watershed.setGeometry(QRect(50, 300, 151, 41))
        self.btn_watershed.setFont(font)

        self.horizontalLayout_5.addWidget(self.widget_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.win1 = QWidget(self.centralwidget)
        self.win1.setObjectName(u"win1")

        self.horizontalLayout.addWidget(self.win1)

        self.Bar1 = QScrollBar(self.centralwidget)
        self.Bar1.setObjectName(u"Bar1")
        self.Bar1.setOrientation(Qt.Orientation.Vertical)

        self.horizontalLayout.addWidget(self.Bar1)

        self.horizontalLayout.setStretch(0, 8)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.win2 = QWidget(self.centralwidget)
        self.win2.setObjectName(u"win2")

        self.horizontalLayout_2.addWidget(self.win2)

        self.Bar2 = QScrollBar(self.centralwidget)
        self.Bar2.setObjectName(u"Bar2")
        self.Bar2.setOrientation(Qt.Orientation.Vertical)

        self.horizontalLayout_2.addWidget(self.Bar2)

        self.horizontalLayout_2.setStretch(0, 8)
        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.win3 = QWidget(self.centralwidget)
        self.win3.setObjectName(u"win3")

        self.horizontalLayout_3.addWidget(self.win3)

        self.Bar3 = QScrollBar(self.centralwidget)
        self.Bar3.setObjectName(u"Bar3")
        self.Bar3.setOrientation(Qt.Orientation.Vertical)

        self.horizontalLayout_3.addWidget(self.Bar3)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)


        self.horizontalLayout_4.addLayout(self.verticalLayout_2)

        self.win4 = QWidget(self.centralwidget)
        self.win4.setObjectName(u"win4")

        self.horizontalLayout_4.addWidget(self.win4)

        self.horizontalLayout_4.setStretch(0, 2)
        self.horizontalLayout_4.setStretch(1, 5)

        self.horizontalLayout_5.addLayout(self.horizontalLayout_4)

        self.label_plate = QWidget(self.centralwidget)
        self.label_plate.setObjectName(u"label_plate")
        self.label_menu = QWidget(self.label_plate)
        self.label_menu.setObjectName(u"label_menu")
        self.label_menu.setGeometry(QRect(20, 20, 221, 951))
        self.verticalLayout = QVBoxLayout(self.label_menu)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout_5.addWidget(self.label_plate)

        self.horizontalLayout_5.setStretch(0, 1)
        self.horizontalLayout_5.setStretch(1, 6)
        self.horizontalLayout_5.setStretch(2, 1)

        self.gridLayout.addLayout(self.horizontalLayout_5, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1920, 33))
        self.menu = QMenu(self.menubar)
        self.menu.setObjectName(u"menu")
        self.menu_2 = QMenu(self.menubar)
        self.menu_2.setObjectName(u"menu_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.menu.addAction(self.actionbone)
        self.menu.addAction(self.actionlung)
        self.menu.addAction(self.actionliver)
        self.menu.addAction(self.actionbrain)
        self.menu_2.addAction(self.actionstl)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionbone.setText(QCoreApplication.translate("MainWindow", u"\u9aa8\u7a97", None))
        self.actionlung.setText(QCoreApplication.translate("MainWindow", u"\u80ba\u7a97", None))
        self.actionliver.setText(QCoreApplication.translate("MainWindow", u"\u7eb5\u8188\u7a97", None))
        self.actionbrain.setText(QCoreApplication.translate("MainWindow", u"\u8111\u7a97", None))
        self.actionstl.setText(QCoreApplication.translate("MainWindow", u"\u5bfc\u51fa.stl\u6587\u4ef6", None))
        self.btn_input_data.setText(QCoreApplication.translate("MainWindow", u"\u8f93\u5165\u6570\u636e", None))
        self.btn_autorec.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52a8\u91cd\u5efa", None))
        self.combo_lobe.clear()
        self.combo_lobe.addItem(QCoreApplication.translate("MainWindow", u"\u53f3\u4e0a\u80ba\u53f6", None))  # 右上肺叶
        self.combo_lobe.addItem(QCoreApplication.translate("MainWindow", u"\u53f3\u4e2d\u80ba\u53f6", None))  # 右中肺叶
        self.combo_lobe.addItem(QCoreApplication.translate("MainWindow", u"\u53f3\u4e0b\u80ba\u53f6", None))  # 右下肺叶
        self.combo_lobe.addItem(QCoreApplication.translate("MainWindow", u"\u5de6\u4e0a\u80ba\u53f6", None))  # 左上肺叶
        self.combo_lobe.addItem(QCoreApplication.translate("MainWindow", u"\u5de6\u4e0b\u80ba\u53f6", None))  # 左下肺叶
        self.btn_watershed.setText(QCoreApplication.translate("MainWindow", u"\u6d41\u57df\u5206\u6790", None))
        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"\u7a97\u5bbd\u7a97\u4f4d", None))
        self.menu_2.setTitle(QCoreApplication.translate("MainWindow", u"\u5bfc\u51fa", None))
    # retranslateUi

