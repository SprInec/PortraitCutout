# -*- coding: utf-8 -*-
#
# File: main.py
# Time: 2023.12.29 18:15:12
#
# Author: Sprine 
# Email: None
# Software: VSCode
# Version: 1.1 2024.10.06
#
# Desc: None
#


import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore

# TODO:主题包, 若使用请先安装: pip install qt-material
from qt_material import apply_stylesheet # 若使用默认样式请注释该行


import backend

if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    MainWindow.setWindowIcon(QIcon('./icon.png'))
    
    """主题包, 可选
        dark_blue.xml, dark_cyan.xml, dark_lightgreen.xml, dark_pink.xml, 
        dark_purple.xml, dark_red.xml, dark_teal.xml, 
        light_blue.xml, light_cyan.xml, light_green.xml, light_pink.xml, 
        light_purple.xml, light_red.xml, light_teal.xml
    """
    apply_stylesheet(app, theme='dark_lightgreen.xml') # 若使用默认样式则注释该行
    
    eventProcress = backend.EventProcress(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())