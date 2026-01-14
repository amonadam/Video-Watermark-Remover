"""
GUI模块
提供图形用户界面相关的类和函数
"""

# 导入主窗口类
from .main_window import MainWindow

# 导入对话框类
from .preview_dialog import PreviewDialog
from .progress_dialog import ProgressDialog

# 导入样式
from .styles import MAIN_WINDOW_STYLE, PREVIEW_DIALOG_STYLE, PROGRESS_DIALOG_STYLE

# 定义导出的公共接口
__all__ = [
    'MainWindow',
    'PreviewDialog', 
    'ProgressDialog',
    'MAIN_WINDOW_STYLE',
    'PREVIEW_DIALOG_STYLE',
    'PROGRESS_DIALOG_STYLE'
]

# 版本信息
__version__ = '1.0.6'