from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal

class ProgressDialog(QDialog):
    cancelled = pyqtSignal()
    
    def __init__(self, total_videos, parent=None):
        super().__init__(parent)
        self.total_videos = total_videos
        self.current_video = 0
        
        self.setWindowTitle("处理进度")
        self.setGeometry(300, 300, 400, 150)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 总体进度
        self.overall_label = QLabel(f"正在处理视频 (0/{total_videos})")
        layout.addWidget(self.overall_label)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, total_videos * 100)
        layout.addWidget(self.overall_progress)
        
        # 当前视频进度
        self.current_label = QLabel("当前视频: 等待开始...")
        layout.addWidget(self.current_label)
        
        self.current_progress = QProgressBar()
        self.current_progress.setRange(0, 100)
        layout.addWidget(self.current_progress)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel)
        layout.addWidget(self.cancel_btn)
        
        self.is_cancelled = False
    
    def update_progress(self, percent, message):
        """更新进度"""
        if not self.is_cancelled:
            # 计算总体进度
            overall_percent = self.current_video * 100 + percent
            
            self.overall_progress.setValue(overall_percent)
            self.overall_label.setText(f"正在处理视频 ({self.current_video}/{self.total_videos})")
            
            # 更新当前视频进度
            self.current_progress.setValue(percent)
            self.current_label.setText(message)
    
    def next_video(self):
        """切换到下一个视频"""
        self.current_video += 1
        self.current_progress.setValue(0)
    
    def cancel(self):
        """取消处理"""
        self.is_cancelled = True
        self.cancelled.emit()
        self.close()