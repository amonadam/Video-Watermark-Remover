"""
预览对话框模块
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPen
import cv2
import numpy as np

class PreviewDialog(QDialog):
    """预览对话框类"""
    
    def __init__(self, video_clip, detector, inpainter, config, parent=None):
        super().__init__(parent)
        self.video_clip = video_clip
        self.detector = detector
        self.inpainter = inpainter
        self.config = config
        
        self.roi = None  # 存储选中的ROI
        self.frame = None  # 存储当前预览帧
        
        self.init_ui()
        self.load_preview_frame()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("预览效果")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout(self)
        
        # 创建标签显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        # ROI选择按钮布局
        roi_button_layout = QHBoxLayout()
        
        self.select_roi_button = QPushButton("手动选择水印区域")
        self.select_roi_button.setToolTip("在视频中手动框选水印区域")
        self.select_roi_button.clicked.connect(self.select_roi)
        roi_button_layout.addWidget(self.select_roi_button)
        
        self.auto_detect_button = QPushButton("自动检测水印区域")
        self.auto_detect_button.setToolTip("自动检测视频中的水印区域")
        self.auto_detect_button.clicked.connect(self.auto_detect_roi)
        roi_button_layout.addWidget(self.auto_detect_button)
        
        self.clear_roi_button = QPushButton("清除选择")
        self.clear_roi_button.setToolTip("清除当前选中的水印区域")
        self.clear_roi_button.clicked.connect(self.clear_roi)
        roi_button_layout.addWidget(self.clear_roi_button)
        
        layout.addLayout(roi_button_layout)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_preview_frame(self):
        """加载预览帧"""
        if not self.video_clip:
            QMessageBox.warning(self, "警告", "无法加载视频帧")
            return
        
        try:
            # 获取第一帧作为预览
            self.frame = self.video_clip.get_frame(0)
            # 将RGB转换为BGR用于OpenCV处理
            self.frame_bgr = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)
            self.update_preview()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载预览帧失败: {str(e)}")
    
    def update_preview(self):
        """更新预览图像，显示ROI标记"""
        if self.frame is None:
            return
        
        # 创建带ROI标记的图像副本
        display_frame = self.frame_bgr.copy()
        
        # 如果有ROI，绘制矩形标记
        if self.roi is not None:
            x, y, w, h = self.roi
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # 添加ROI坐标文本
            cv2.putText(display_frame, f"ROI: ({x}, {y}, {w}, {h})", 
                       (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 转换为QImage并显示
        qimage = self.numpy_to_qimage(display_frame)
        pixmap = QPixmap.fromImage(qimage)
        
        # 调整图像大小以适应标签
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
    
    def select_roi(self):
        """手动选择水印区域"""
        if self.frame is None:
            QMessageBox.warning(self, "警告", "请先加载视频帧")
            return
        
        try:
            # 使用OpenCV的selectROI功能
            display_frame = self.frame_bgr.copy()
            
            # 添加操作说明
            instructions = [
                "选择水印区域:",
                "1. 用鼠标拖拽选择矩形区域",
                "2. 按SPACE或ENTER确认选择",
                "3. 按ESC取消选择"
            ]
            
            # 尝试加载中文字体
            try:
                from PIL import Image, ImageDraw, ImageFont
                import numpy as np
                
                # 转换为PIL图像
                pil_image = Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_image)
                
                # 尝试加载中文字体
                font_path = "C:\\Windows\\Fonts\\simhei.ttf"
                try:
                    font = ImageFont.truetype(font_path, 20)
                except IOError:
                    # 如果字体文件不存在，使用默认字体
                    font = ImageFont.load_default()
                
                # 绘制文本
                for i, line in enumerate(instructions):
                    # 绘制白色背景
                    draw.text((10, 30 + i * 30), line, font=font, fill=(255, 255, 255), stroke_width=2)
                    # 绘制红色文字
                    draw.text((10, 30 + i * 30), line, font=font, fill=(255, 0, 0), stroke_width=0)
                
                # 转换回OpenCV图像
                display_frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            except ImportError:
                # 如果PIL不可用，回退到OpenCV绘制英文文本
                font = cv2.FONT_HERSHEY_SIMPLEX
                # 使用英文指令作为fallback
                english_instructions = [
                    "Select Watermark Area:",
                    "1. Drag to select rectangle area",
                    "2. Press SPACE or ENTER to confirm",
                    "3. Press ESC to cancel"
                ]
                for i, line in enumerate(english_instructions):
                    cv2.putText(display_frame, line, (10, 30 + i * 30), 
                               font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(display_frame, line, (10, 30 + i * 30), 
                               font, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
            
            # 调整显示大小
            display_height = 720
            scale_factor = display_height / display_frame.shape[0]
            display_width = int(display_frame.shape[1] * scale_factor)
            scaled_frame = cv2.resize(display_frame, (display_width, display_height))
            
            # 选择ROI
            r = cv2.selectROI("Select Watermark Area", scaled_frame, False, False)
            cv2.destroyAllWindows()
            
            # 如果用户按ESC，r为(0, 0, 0, 0)
            if r[2] == 0 or r[3] == 0:
                return
            
            # 将ROI坐标转换回原始尺寸
            self.roi = (
                int(r[0] / scale_factor),      # x
                int(r[1] / scale_factor),      # y
                int(r[2] / scale_factor),      # width
                int(r[3] / scale_factor)       # height
            )
            
            # 更新detector的ROI
            self.detector.roi = self.roi
            
            # 更新预览
            self.update_preview()
            
            QMessageBox.information(self, "提示", "水印区域选择成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"选择水印区域失败: {str(e)}")
    
    def auto_detect_roi(self):
        """自动检测水印区域"""
        if self.frame is None:
            QMessageBox.warning(self, "警告", "请先加载视频帧")
            return
        
        try:
            # 使用detector的自动检测功能
            self.detector.roi = None  # 确保之前的ROI被清除
            
            # 调用generate_mask会触发自动ROI选择
            mask = self.detector.generate_mask(self.video_clip, auto_select_roi=True)
            
            # 获取自动检测到的ROI
            self.roi = self.detector.roi
            
            if self.roi is not None:
                # 更新预览
                self.update_preview()
                QMessageBox.information(self, "提示", "水印区域自动检测成功")
            else:
                QMessageBox.warning(self, "警告", "无法自动检测水印区域，请尝试手动选择")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"自动检测水印区域失败: {str(e)}")
    
    def clear_roi(self):
        """清除当前选中的水印区域"""
        self.roi = None
        self.detector.roi = None
        self.update_preview()
        QMessageBox.information(self, "提示", "已清除水印区域选择")
    
    def resizeEvent(self, event):
        """窗口大小改变时更新预览图像"""
        super().resizeEvent(event)
        self.update_preview()
    
    def numpy_to_qimage(self, image):
        """将numpy数组转换为QImage"""
        if image is None:
            return QImage()
            
        if len(image.shape) == 2:
            # 灰度图像
            h, w = image.shape
            bytes_per_line = w
            return QImage(image.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        else:
            # 彩色图像
            h, w, ch = image.shape
            bytes_per_line = ch * w
            
            # 确保是RGB格式
            if ch == 3:
                # BGR转RGB
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            elif ch == 4:
                # BGRA转RGBA
                rgba_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                return QImage(rgba_image.data, w, h, bytes_per_line, QImage.Format_RGBA8888)
            else:
                # 其他格式转为RGB
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

# 确保导出的类名正确
__all__ = ['PreviewDialog']