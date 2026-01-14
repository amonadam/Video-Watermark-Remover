import sys
import os
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

# 检查是否在PyInstaller打包后的环境中运行
if hasattr(sys, '_MEIPASS'):
    # 打包后的环境，使用临时目录
    current_dir = sys._MEIPASS
else:
    # 开发环境，使用原始路径
    current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加src目录到Python路径
sys.path.append(current_dir)

from gui.main_window import MainWindow
from core.utils import ensure_directory_exists, load_config, save_config

def main():
    # 设置应用程序信息
    QCoreApplication.setApplicationName("视频去水印软件")
    QCoreApplication.setApplicationVersion("1.0.0")
    
    app = QApplication(sys.argv)
    
    # 加载配置文件
    config_dir = os.path.join(os.path.dirname(current_dir), "configs")
    ensure_directory_exists(config_dir)
    
    config_path = os.path.join(config_dir, "settings.json")
    config = load_config(config_path)
    
    # 初始化访问控制模块，使用配置文件中的存储设置
    from core.security import initialize_access_control
    user_storage_config = config.get("user_storage", {})
    storage_type = user_storage_config.get("type", "sqlite")
    storage_path = user_storage_config.get("file_path", "users.db")
    initialize_access_control(user_db_path=storage_path, storage_type=storage_type)
    
    # 创建主窗口
    window = MainWindow(config, config_path)
    
    # 设置窗口图标
    icon_path = os.path.join(current_dir, "assets", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()