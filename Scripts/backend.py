# -*- coding: utf-8 -*-
#
# File: backend.py
# Time: 2023.12.29 19:49:01
#
# Author: Sprine 
# Email: None
# Software: VSCode
# Version: 1.0
#
# Desc: The back-end implementation of Qt applications
#       is responsible for ui logic control and AI model 
#       inference
#


import os
import subprocess
import time
import sys

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QDialog, QInputDialog
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRect

from mainwindow_ui import Ui_MainWindow
from idphotosetting_ui import Ui_Form

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

## NOTE: 相对路径
cfg = os.path.join(
    current_dir, './Matting/configs/ppmattingv2/ppmattingv2-stdc1-human_512.yml')
model_path = os.path.join(
    current_dir, './Matting/pretrained_models/ppmattingv2-stdc1-human_512.pdparams')
save_dir = os.path.join(current_dir, './predict_results/')

## NOTE: 绝对路径
# cfg = 'D:/Matting/configs/ppmattingv2/ppmattingv2-stdc1-human_512.yml'
# model_path = 'D:/Matting/pretrained_models/ppmattingv2-stdc1-human_512.pdparams'
# save_dir = os.path.join(current_dir, './predict_results/')
# predict_path = 'D:/Matting/tools/predict.py'
# bg_replace_path = 'D:/Matting/tools/bg_replace.py'

trimap_path = None
fg_estimate = True
background = 'w'


class IDPhotoWindow(QDialog, Ui_Form):
    # 定义一个自定义信号
    finished = pyqtSignal(str, tuple)

    def __init__(self):
        super().__init__()
        
        self._background = None
        self._size = None
        
        self._exit = False

        self.setupUi(self)
        self.initUI()

    def initUI(self):
        # 绑定槽函数
        self.okBtn.clicked.connect(self._ok)
        self.cancelBtn.clicked.connect(self._cancel)
        
    def _setBackground(self, background):
        if background == '红色':
            self._background = 'r'
        elif background == '绿色':
            self._background = 'g'
        elif background == '蓝色':
            self._background = 'b'
        elif background == '白色':
            self._background = 'w'
        elif background == '图片':
            fileName, _ = QFileDialog.getOpenFileName(
                self, "Open file", "", "Image files (*.png *.jpg)")
            if fileName:
                self._background = fileName
            else:
                return
        
    def _setSize(self, size):
        if size == '原图':
            self._size = (0, 0)
        elif size == '1寸':
            self._size = (25, 35)  # 1寸照片尺寸为25mm x 35mm
        elif size == '2寸':
            self._size = (35, 53)  # 2寸照片尺寸为35mm x 53mm
        elif size == '3寸':
            self._size = (51, 76)  # 3寸照片尺寸为51mm x 76mm
        elif size == '5寸':
            self._size = (89, 127)  # 5寸照片尺寸为89mm x 127mm
        elif size == '6寸':
            self._size = (102, 152)  # 6寸照片尺寸为102mm x 152mm
        elif size == '7寸':
            self._size = (127, 178)  # 7寸照片尺寸为127mm x 178mm
        elif size == '8寸':
            self._size = (203, 254)  # 8寸照片尺寸为203mm x 254mm
        elif size == '10寸':
            self._size = (254, 305)  # 10寸照片尺寸为254mm x 305mm
        elif size == '12寸':
            self._size = (305, 406)  # 12寸照片尺寸为305mm x 406mm
        elif size == '护照':
            self._size = (35, 45)  # 护照照片尺寸为35mm x 45mm
        elif size == '身份证':
            self._size = (25, 35)  # 身份证照片尺寸为25mm x 35mm
        elif size == '自定义':
             # 弹出输入对话框,获取用户自定义尺寸
            width, ok1 = QInputDialog.getInt(None, "自定义尺寸", "请输入宽度(mm):")
            height, ok2 = QInputDialog.getInt(None, "自定义尺寸", "请输入高度(mm):")
            
            if ok1 and ok2:
                self._size = (width, height)  # 使用用户输入的自定义尺寸
                self._exit = False
            else:
                self._size = (0, 0)
                QMessageBox.information(None, "提示", "您取消了自定义尺寸的输入")
                self._exit = True
                
        # 将mm转换为像素
        dpi = 100  # 默认显示设备的像素密度为100 DPI
        width_pixel = int(self._size[0] * dpi / 25.4)
        height_pixel = int(self._size[1] * dpi / 25.4)
        self._size = (width_pixel, height_pixel)

    def _ok(self):
        background = self.backgroundBox.currentText()
        self._setBackground(background)
        size = self.sizeBox.currentText()
        self._setSize(size)
        if self._exit is False:
            self.close()
            # 发射自定义信号,传递选择的背景值与照片尺寸
            self.finished.emit(self._background, self._size)
        elif self._exit is True:
            return

    def _cancel(self):
        self.close()
    

class EventProcress(QMainWindow, Ui_MainWindow):

    def __init__(self, mainWindow) -> None:
        super().__init__()
        
        self.cfg = cfg
        self.model_path = model_path
        self.trimap_path = trimap_path
        self.save_dir = save_dir
        self.fg_estimate = fg_estimate
        self.background = background
        self.size = None

        self.image_path = None

        self.idphoto_window = None

        self.setupUi(mainWindow)
        self.initUI()

    def initUI(self):

        self.setWindowTitle('Portrait Cutout')

        # 绑定槽函数
        self.selectImageBtn.clicked.connect(self._selectImage)
        self.mattingBtn.clicked.connect(self._matting)
        self.makeidphotoBtn.clicked.connect(self._settingIDPhoto)
        self.saveBtn.clicked.connect(self._save)
        self.imageOpen.triggered.connect(self._selectImage)
        self.imageClose.triggered.connect(self._closeImage)

        # 控件设置
        self.matteImageDisplayEdit.setScaledContents(True)
        self.imageDisplayEdit.setScaledContents(True)

    def _createIdPthotoWindow(self):
        if self.idphoto_window is None:
            self.idphoto_window = IDPhotoWindow()
            self.idphoto_window.finished.connect(self._setPhotoParameters)
        self.idphoto_window.show()
    
    ## FIXME: 此处size不为(0,0)时尺寸设置与显示有问题
    def _displayImageOnLabel(self, image_path, label, size=(0,0)):
        pixmap = QPixmap(image_path)
        if size == (0,0):
            target_size = label.size()
        else:
            target_size = QSize(size[0], size[1])

        scaled_pixmap = pixmap.scaled(
            target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.SmoothTransformation)

        # 创建一个新的QPixmap对象,尺寸与目标控件相同,并设置为透明色
        transparent_pixmap = QPixmap(target_size)
        transparent_pixmap.fill(Qt.transparent)

        # 计算图像在控件中的位置和大小
        x = (target_size.width() - scaled_pixmap.width()) // 2
        y = (target_size.height() - scaled_pixmap.height()) // 2
        target_rect = QRect(x, y, scaled_pixmap.width(), scaled_pixmap.height())

        # 在透明的QPixmap上绘制缩放后的图像,保留原始比例并填充透明部分
        painter = QPainter(transparent_pixmap)
        painter.drawPixmap(target_rect, scaled_pixmap)
        painter.end()

        label.setPixmap(transparent_pixmap)

    def _selectImage(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Open file", "", "Image files (*.png *.jpg)")
        if fileName:
            # self.imagePathLineEdit.setText(fileName) # 显示所选图片路径
            self.image_path = fileName
            self._displayImageOnLabel(self.image_path, self.imageDisplayEdit)

    def _closeImage(self):
        self.image_path = None
        self.imageDisplayEdit.clear()
        self.matteImageDisplayEdit.clear()
        
    def _setPhotoParameters(self, background, size):
        self.background = background
        self.size = size
        
        self._makeIDPhoto()

    def _settingIDPhoto(self):
        imagePath = self.image_path
        if not imagePath:
            QMessageBox.warning(self, "Warning", "Please select an image!")
            return

        # 打开设置窗口
        self._createIdPthotoWindow()

    def _matting(self):
        imagePath = self.image_path
        if not imagePath:
            QMessageBox.warning(self, "Warning", "Please select an image!")
            return

        ## NOTE: 相对路径
        cmd = f"{sys.executable} {os.path.join(current_dir, './Matting/tools/predict.py')} \
                    --config {self.cfg}                      \
                    --model_path {self.model_path}           \
                    --image_path {imagePath}                 \
                    --save_dir {self.save_dir}               \
                    --fg_estimate {self.fg_estimate}"
        subprocess.run(cmd, shell=True)
        
        ## NOTE: 绝对路径
        # cmd = f"python {predict_path} \
        #             --config {self.cfg}                         \
        #             --model_path {self.model_path}              \
        #             --image_path {imagePath}                    \
        #             --save_dir {self.save_dir}                  \
        #             --fg_estimate {self.fg_estimate}"
        # subprocess.run(cmd, shell=True)

        # 动态延时,等待图片出现
        image_name = os.path.splitext(os.path.basename(imagePath))[0]
        image_path = os.path.join(self.save_dir, f"{image_name}_rgba.png")
        timeout = 5  # 设置超时时间为5秒
        start_time = time.time()
        while not os.path.exists(image_path):
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                QMessageBox.warning(
                    self, "Warning", "Timeout: Failed to load matte image!")
                return
            time.sleep(0.1)  # 每隔0.1秒检查一次

        # 加载并展示图片
        self._displayImageOnLabel(image_path,self.matteImageDisplayEdit)

    def _makeIDPhoto(self):

        # NOTE: 相对路径
        cmd = f"{sys.executable} {os.path.join(current_dir, './Matting/tools/bg_replace.py')} \
                    --config {self.cfg}                         \
                    --model_path {self.model_path}              \
                    --image_path {self.image_path}              \
                    --background {self.background}              \
                    --save_dir {self.save_dir}                  \
                    --fg_estimate {self.fg_estimate}"
        subprocess.run(cmd, shell=True)
        
        # NOTE: 绝对路径
        # cmd = f"python {bg_replace_path} \
        #             --config {self.cfg}                            \
        #             --model_path {self.model_path}                 \
        #             --image_path {self.image_path}                 \
        #             --background {self.background}                 \
        #             --save_dir {self.save_dir}                     \
        #             --fg_estimate {self.fg_estimate}"
        # subprocess.run(cmd, shell=True)

        # 动态延时,等待图片出现
        image_name = os.path.splitext(os.path.basename(self.image_path))[0]
        image_path = os.path.join(self.save_dir, f"{image_name}.jpg")
        timeout = 5  # 设置超时时间为5秒
        start_time = time.time()
        while not os.path.exists(image_path):
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                QMessageBox.warning(
                    self, "Warning", "Timeout: Failed to load matte image!")
                return
            time.sleep(0.1)  # 每隔0.1秒检查一次

        # 加载并展示图片
        self._displayImageOnLabel(image_path, self.matteImageDisplayEdit, self.size)
            

    def _save(self):    
        if self.matteImageDisplayEdit.pixmap() is None:
            QMessageBox.warning(self, "Warning", "No image to save!")
            return

        # 打开文件对话框,选择保存路径
        savePath, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "Images (*.png *.jpg)")

        if savePath:
            # 获取标签控件的图像
            pixmap = self.matteImageDisplayEdit.pixmap()

            # 保存图片到指定路径
            pixmap.save(savePath)
