import sys
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QFrame, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.security import authenticate_user
from core.utils import set_current_user
from . import styles
from .register_dialog import RegisterDialog

class LoginDialog(QDialog):
    """登录对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户登录")
        self.setFixedSize(400, 350)
        self.setStyleSheet(styles.LOGIN_DIALOG_STYLE)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化登录界面"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        

        
        # 表单布局
        form_group = QGroupBox()
        form_group.setStyleSheet("border: none;")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(15)
        
        # 用户名输入
        self.username_edit = QLineEdit()
        self.username_edit.setFont(QFont("Microsoft YaHei", 12))
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setStyleSheet(styles.LINE_EDIT_STYLE)
        self.username_edit.returnPressed.connect(self.on_login)
        form_layout.addRow("用户名:", self.username_edit)
        
        # 密码输入
        self.password_edit = QLineEdit()
        self.password_edit.setFont(QFont("Microsoft YaHei", 12))
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet(styles.LINE_EDIT_STYLE)
        self.password_edit.returnPressed.connect(self.on_login)
        form_layout.addRow("密码:", self.password_edit)
        
        main_layout.addWidget(form_group)
        
        # 登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setFont(QFont("Microsoft YaHei", 12))
        self.login_button.setFixedHeight(40)
        self.login_button.setStyleSheet(styles.BUTTON_STYLE)
        self.login_button.clicked.connect(self.on_login)
        main_layout.addWidget(self.login_button)
        
        # 注册入口
        register_layout = QHBoxLayout()
        register_layout.setSpacing(10)  # 添加间距
        register_layout.setAlignment(Qt.AlignCenter)
        
        register_label = QLabel("没有账号?")
        register_label.setFont(QFont("Microsoft YaHei", 9))
        register_label.setStyleSheet("color: #666666;")
        
        self.register_button = QPushButton("立即注册")
        self.register_button.setFont(QFont("Microsoft YaHei", 9))
        self.register_button.setFlat(True)
        self.register_button.setStyleSheet(styles.BUTTON_STYLE_FLAT)  # 使用新添加的扁平按钮样式
        self.register_button.clicked.connect(self.on_register)
        
        register_layout.addWidget(register_label)
        register_layout.addWidget(self.register_button)
        main_layout.addLayout(register_layout)
        
        self.setLayout(main_layout)
    
    def on_login(self):
        """处理登录事件"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码")
            return
        
        try:
            # 验证用户
            user_info = authenticate_user(username, password)
            if user_info:
                # 设置当前用户
                set_current_user(user_info)
                QMessageBox.information(self, "登录成功", f"欢迎，{username}!")
                self.accept()
            else:
                QMessageBox.warning(self, "登录失败", "用户名或密码错误")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录时发生错误: {str(e)}")

    def on_register(self):
        """打开注册对话框"""
        dialog = RegisterDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 注册成功后可以选择保持登录对话框打开或关闭
            # 这里选择显示提示信息
            QMessageBox.information(self, "注册成功", "用户注册成功，请使用新账号登录")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 如果用户关闭登录窗口，退出应用
        sys.exit()
