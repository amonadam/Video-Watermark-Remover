#!/usr/bin/env python3
import sys
import os

# 检查是否在PyInstaller打包后的环境中运行
if hasattr(sys, '_MEIPASS'):
    current_dir = sys._MEIPASS
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加src目录到Python路径
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'src'))

try:
    from PyQt5.QtWidgets import QApplication
    from src.gui.login_dialog import LoginDialog
    
    print("创建QApplication...")
    app = QApplication(sys.argv)
    
    print("创建LoginDialog...")
    login_dialog = LoginDialog()
    
    print("显示LoginDialog...")
    result = login_dialog.exec_()
    
    print(f"对话框返回结果: {result}")
    
except Exception as e:
    print(f"测试过程中发生错误: {e}")
    import traceback
    traceback.print_exc()
