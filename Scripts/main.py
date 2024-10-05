# -*- coding: utf-8 -*-
#
# File: main.py
# Time: 2023.12.29 18:15:12
#
# Author: Sprine 
# Email: None
# Software: VSCode
# Version: 1.0
#
# Desc: None
#


import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
from qt_material import apply_stylesheet


import backend

if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    MainWindow.setWindowIcon(QIcon('./icon.png'))
    apply_stylesheet(app, theme='dark_lightgreen.xml')
    eventProcress = backend.EventProcress(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())