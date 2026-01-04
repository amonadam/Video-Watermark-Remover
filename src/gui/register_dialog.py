import sys
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.utils import register_user
from . import styles


class RegisterDialog(QDialog):
    """
    用户注册对话框
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户注册")
        self.setFixedSize(400, 350)
        self.setStyleSheet(styles.LOGIN_DIALOG_STYLE)
        
        self.init_ui()
        
    def init_ui(self):
        """
        初始化注册界面
        """
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 20)
        main_layout.setSpacing(20)
        
        # 标题
        title_label = QLabel()
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #333333;")
        main_layout.addWidget(title_label)
        
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
        self.username_edit.returnPressed.connect(self.on_register)
        form_layout.addRow("用户名:", self.username_edit)
        
        # 密码输入
        self.password_edit = QLineEdit()
        self.password_edit.setFont(QFont("Microsoft YaHei", 12))
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet(styles.LINE_EDIT_STYLE)
        self.password_edit.returnPressed.connect(self.on_register)
        form_layout.addRow("密码:", self.password_edit)
        
        # 确认密码输入
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setFont(QFont("Microsoft YaHei", 12))
        self.confirm_password_edit.setPlaceholderText("请再次输入密码")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setStyleSheet(styles.LINE_EDIT_STYLE)
        self.confirm_password_edit.returnPressed.connect(self.on_register)
        form_layout.addRow("确认密码:", self.confirm_password_edit)
        
        main_layout.addWidget(form_group)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFont(QFont("Microsoft YaHei", 12))
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.setStyleSheet(styles.BUTTON_STYLE_CANCEL)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # 注册按钮
        self.register_button = QPushButton("注册")
        self.register_button.setFont(QFont("Microsoft YaHei", 12))
        self.register_button.setFixedHeight(40)
        self.register_button.setStyleSheet(styles.BUTTON_STYLE)
        self.register_button.clicked.connect(self.on_register)
        button_layout.addWidget(self.register_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def validate_input(self):
        """
        验证输入数据
        
        Returns:
            tuple: (是否通过验证, 错误信息)
        """
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        confirm_password = self.confirm_password_edit.text().strip()
        
        # 检查用户名
        if not username:
            return False, "请输入用户名"
        
        if len(username) < 3:
            return False, "用户名长度不能少于3个字符"
        
        if not username.isalnum():
            return False, "用户名只能包含字母和数字"
        
        # 检查密码
        if not password:
            return False, "请输入密码"
        
        if len(password) < 6:
            return False, "密码长度不能少于6个字符"
        
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "密码必须包含大小写字母和数字"
        
        # 检查确认密码
        if password != confirm_password:
            return False, "两次输入的密码不一致"
        
        return True, ""
    
    def on_register(self):
        """
        处理注册事件
        """
        # 验证输入
        is_valid, error_msg = self.validate_input()
        if not is_valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        try:
            # 调用注册函数
            success = register_user(username, password)
            if success:
                QMessageBox.information(self, "注册成功", "用户注册成功！")
                self.accept()
            else:
                QMessageBox.warning(self, "注册失败", "用户名已存在，请更换用户名")
        except Exception as e:
            QMessageBox.critical(self, "注册错误", f"注册时发生错误: {str(e)}")
