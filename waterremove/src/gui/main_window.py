import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QLineEdit,
    QGroupBox, QCheckBox, QTextEdit, QProgressBar,
    QMessageBox, QComboBox, QSpinBox, QTabWidget,
    QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor

from .preview_dialog import PreviewDialog
from .login_dialog import LoginDialog
from gui.progress_dialog import ProgressDialog
from core.watermark_detector import WatermarkDetector
from core.video_processor import VideoProcessor
from core.lama_inpainter import LamaInpainter
from core.utils import get_video_info, check_gpu, get_current_user
from core.security import check_user_permission
from core.history_manager import add_history_record, get_history_records, delete_history_record, delete_all_history_records
from . import styles

class ProcessingThread(QThread):
    """处理线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, input_paths, output_dir, detector, inpainter, config, current_user):
        super().__init__()
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.detector = detector
        self.inpainter = inpainter
        self.config = config
        self.current_user = current_user
        self._is_running = True
    
    def run(self):
        try:
            results = []
            total_videos = len(self.input_paths)
            
            for i, video_path in enumerate(self.input_paths):
                if not self._is_running:
                    break
                    
                self.progress.emit(int((i / total_videos) * 100), 
                                 f"正在处理: {os.path.basename(video_path)}")
                
                processor = VideoProcessor(video_path, self.output_dir, 
                                         self.detector, self.inpainter, self.config)
                result = processor.process()
                results.append(result)
            
            self.finished.emit({"results": results, "success": True})
            
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        self._is_running = False

class MainWindow(QMainWindow):
    def __init__(self, config, config_path):
        super().__init__()
        self.config = config
        self.config_path = config_path
        self.video_paths = []
        self.detector = None
        self.inpainter = None
        self.processing_thread = None
        
        # 用户信息
        self.current_user = None
        
        # 显示登录对话框
        self.show_login_dialog()
        
        # 获取当前用户
        self.current_user = get_current_user()
        
        self.init_ui()
        self.load_settings()
        
        # 根据用户权限更新UI
        self.update_ui_based_on_permissions()
    
    def show_login_dialog(self):
        """显示登录对话框"""
        login_dialog = LoginDialog(self)
        login_dialog.exec_()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("视频去水印软件")
        self.setGeometry(100, 100, 900, 700)
        
        # 设置样式
        self.setStyleSheet(styles.MAIN_WINDOW_STYLE)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # 视频处理标签页
        process_tab = QWidget()
        tabs.addTab(process_tab, "视频处理")
        self.setup_process_tab(process_tab)
        
        # 历史记录标签页
        history_tab = QWidget()
        tabs.addTab(history_tab, "历史记录")
        self.setup_history_tab(history_tab)
        
        # 设置标签页
        settings_tab = QWidget()
        tabs.addTab(settings_tab, "设置")
        self.setup_settings_tab(settings_tab)
        
        # 管理员功能标签页（默认隐藏，根据权限显示）
        self.admin_tab = QWidget()
        self.admin_tab_index = tabs.addTab(self.admin_tab, "管理员功能")
        self.setup_admin_tab(self.admin_tab)
        
        # 日志区域
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setMinimumHeight(40)
        button_layout.addWidget(self.process_btn)
        
        self.preview_btn = QPushButton("预览效果")
        self.preview_btn.clicked.connect(self.show_preview)
        self.preview_btn.setMinimumHeight(40)
        button_layout.addWidget(self.preview_btn)
        
        self.quit_btn = QPushButton("退出")
        self.quit_btn.clicked.connect(self.close)
        self.quit_btn.setMinimumHeight(40)
        button_layout.addWidget(self.quit_btn)
        
        main_layout.addLayout(button_layout)
    
    def setup_process_tab(self, tab):
        """设置视频处理标签页"""
        layout = QVBoxLayout(tab)
        
        # 输入文件选择
        input_group = QGroupBox("输入视频")
        input_layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("选择视频文件或目录...")
        file_layout.addWidget(self.input_path_edit)
        
        self.browse_file_btn = QPushButton("选择文件")
        self.browse_file_btn.clicked.connect(self.browse_files)
        file_layout.addWidget(self.browse_file_btn)
        
        self.browse_dir_btn = QPushButton("选择目录")
        self.browse_dir_btn.clicked.connect(self.browse_directory)
        file_layout.addWidget(self.browse_dir_btn)
        
        input_layout.addLayout(file_layout)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 输出目录选择
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        
        output_path_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setText("output")
        output_path_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton("浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        output_path_layout.addWidget(self.browse_output_btn)
        
        output_layout.addLayout(output_path_layout)
        
        # 输出格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MOV"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        output_layout.addLayout(format_layout)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 水印检测设置
        detection_group = QGroupBox("水印检测设置")
        detection_layout = QVBoxLayout()
        
        sample_layout = QHBoxLayout()
        sample_layout.addWidget(QLabel("采样帧数:"))
        self.sample_frames_spin = QSpinBox()
        self.sample_frames_spin.setRange(1, 100)
        self.sample_frames_spin.setValue(20)
        sample_layout.addWidget(self.sample_frames_spin)
        sample_layout.addStretch()
        detection_layout.addLayout(sample_layout)
        
        min_frame_layout = QHBoxLayout()
        min_frame_layout.addWidget(QLabel("最小帧数:"))
        self.min_frames_spin = QSpinBox()
        self.min_frames_spin.setRange(1, 50)
        self.min_frames_spin.setValue(10)
        min_frame_layout.addWidget(self.min_frames_spin)
        min_frame_layout.addStretch()
        detection_layout.addLayout(min_frame_layout)
        
        dilation_layout = QHBoxLayout()
        dilation_layout.addWidget(QLabel("膨胀核大小:"))
        self.dilation_spin = QSpinBox()
        self.dilation_spin.setRange(1, 20)
        self.dilation_spin.setValue(3)
        dilation_layout.addWidget(self.dilation_spin)
        dilation_layout.addStretch()
        detection_layout.addLayout(dilation_layout)
        
        color_layout = QHBoxLayout()
        self.color_segmentation_checkbox = QCheckBox("启用颜色分割(蓝色背景检测)")
        self.color_segmentation_checkbox.setChecked(True)
        color_layout.addWidget(self.color_segmentation_checkbox)
        color_layout.addStretch()
        detection_layout.addLayout(color_layout)
        
        min_comp_layout = QHBoxLayout()
        min_comp_layout.addWidget(QLabel("最小连通域面积:"))
        self.min_comp_spin = QSpinBox()
        self.min_comp_spin.setRange(1, 10000)
        self.min_comp_spin.setValue(100)
        min_comp_layout.addWidget(self.min_comp_spin)
        min_comp_layout.addStretch()
        detection_layout.addLayout(min_comp_layout)
        
        detection_group.setLayout(detection_layout)
        layout.addWidget(detection_group)
        
        # 预览选项
        preview_group = QGroupBox("预览选项")
        preview_layout = QVBoxLayout()
        self.preview_checkbox = QCheckBox("处理前预览效果")
        self.preview_checkbox.setChecked(True)
        preview_layout.addWidget(self.preview_checkbox)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        layout.addStretch()
    
    def setup_settings_tab(self, tab):
        """设置设置标签页"""
        layout = QVBoxLayout(tab)
        
        # GPU设置
        gpu_group = QGroupBox("硬件设置")
        gpu_layout = QVBoxLayout()
        
        self.gpu_checkbox = QCheckBox("使用GPU加速（如可用）")
        self.gpu_checkbox.setChecked(True)
        gpu_layout.addWidget(self.gpu_checkbox)
        
        # 检测GPU
        has_gpu, _, gpu_name = check_gpu()
        if has_gpu:
            gpu_info = QLabel(f"检测到GPU: {gpu_name}")
            gpu_info.setStyleSheet("color: green; font-weight: bold;")
        else:
            gpu_info = QLabel("未检测到GPU，将使用CPU")
            gpu_info.setStyleSheet("color: orange;")
        
        gpu_layout.addWidget(gpu_info)
        gpu_group.setLayout(gpu_layout)
        layout.addWidget(gpu_group)
        
        # 模型设置
        model_group = QGroupBox("模型设置")
        model_layout = QVBoxLayout()
        
        ldm_layout = QHBoxLayout()
        ldm_layout.addWidget(QLabel("LDM步数:"))
        self.ldm_steps_spin = QSpinBox()
        self.ldm_steps_spin.setRange(10, 200)
        self.ldm_steps_spin.setValue(50)
        ldm_layout.addWidget(self.ldm_steps_spin)
        ldm_layout.addStretch()
        model_layout.addLayout(ldm_layout)
        
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("高清策略:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["ORIGINAL", "CROP", "RESIZE"])
        strategy_layout.addWidget(self.strategy_combo)
        strategy_layout.addStretch()
        model_layout.addLayout(strategy_layout)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # 其他设置
        other_group = QGroupBox("其他设置")
        other_layout = QVBoxLayout()
        
        # ROI选择模式
        roi_mode_group = QGroupBox("水印区域选择模式")
        roi_mode_layout = QVBoxLayout()
        
        self.roi_mode_group = QButtonGroup(self)
        
        self.manual_roi_radio = QRadioButton("手动选择水印区域")
        self.manual_roi_radio.setToolTip("手动框选视频中的水印区域，提供精确控制")
        self.manual_roi_radio.clicked.connect(self.on_roi_mode_changed)
        
        self.auto_roi_radio = QRadioButton("自动检测水印区域")
        self.auto_roi_radio.setToolTip("自动检测视频中的水印区域，方便快捷")
        self.auto_roi_radio.setChecked(True)  # 默认自动选择
        self.auto_roi_radio.clicked.connect(self.on_roi_mode_changed)
        
        self.roi_mode_group.addButton(self.manual_roi_radio)
        self.roi_mode_group.addButton(self.auto_roi_radio)
        
        roi_mode_layout.addWidget(self.manual_roi_radio)
        roi_mode_layout.addWidget(self.auto_roi_radio)
        roi_mode_group.setLayout(roi_mode_layout)
        other_layout.addWidget(roi_mode_group)
        
        # ROI边距设置
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("ROI边距:"))
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 100)
        self.margin_spin.setValue(50)
        margin_layout.addWidget(self.margin_spin)
        margin_layout.addWidget(QLabel("像素"))
        margin_layout.addStretch()
        other_layout.addLayout(margin_layout)
        
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)
        
        # 保存设置按钮
        self.save_settings_btn = QPushButton("保存设置")
        self.save_settings_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_settings_btn)
        
        layout.addStretch()
    
    def browse_files(self):
        """浏览文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)"
        )
        
        if files:
            self.video_paths = files
            self.input_path_edit.setText("; ".join(files))
            self.log(f"选择了 {len(files)} 个视频文件")
            
            # 记录导入历史
            if self.current_user:
                username = self.current_user['username']
                for file_path in files:
                    file_name = os.path.basename(file_path)
                    try:
                        file_size = os.path.getsize(file_path)
                    except:
                        file_size = None
                    
                    add_history_record(username, file_path, 'import', file_name, file_size)
    
    def browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择视频目录")
        
        if directory:
            self.input_path_edit.setText(directory)
            # 稍后扫描视频文件
            self.log(f"选择了目录: {directory}")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        
        if directory:
            self.output_path_edit.setText(directory)
    
    def log(self, message):
        """添加日志"""
        self.log_text.append(f"[{self.get_current_time()}] {message}")
    
    def get_current_time(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def load_settings(self):
        """加载设置"""
        try:
            if "sample_frames" in self.config:
                self.sample_frames_spin.setValue(self.config["sample_frames"])
            if "min_frames" in self.config:
                self.min_frames_spin.setValue(self.config["min_frames"])
            if "dilation_size" in self.config:
                self.dilation_spin.setValue(self.config["dilation_size"])
            if "use_gpu" in self.config:
                self.gpu_checkbox.setChecked(self.config["use_gpu"])
            if "ldm_steps" in self.config:
                self.ldm_steps_spin.setValue(self.config["ldm_steps"])
            if "margin" in self.config:
                self.margin_spin.setValue(self.config["margin"])
            if "use_color_segmentation" in self.config:
                self.color_segmentation_checkbox.setChecked(self.config["use_color_segmentation"])
            if "min_component_area" in self.config:
                self.min_comp_spin.setValue(self.config["min_component_area"])
            if "auto_select_roi" in self.config:
                auto_select = self.config["auto_select_roi"]
                self.auto_roi_radio.setChecked(auto_select)
                self.manual_roi_radio.setChecked(not auto_select)
            
            self.log("设置加载完成")
        except Exception as e:
            self.log(f"加载设置失败: {e}")
    
    def on_roi_mode_changed(self):
        """处理ROI选择模式变化"""
        # 不需要立即保存，只在用户点击保存设置按钮时保存
        pass
    
    def update_ui_based_on_permissions(self):
        """根据用户权限更新UI"""
        if not self.current_user:
            return
        
        username = self.current_user['username']
        
        # 检查是否有编辑权限（用于处理视频和预览）
        has_edit_permission = check_user_permission(username, 'edit')
        
        # 检查是否有管理权限（用于修改设置和管理员功能）
        has_admin_permission = check_user_permission(username, 'admin')
        
        # 更新底部按钮权限
        self.process_btn.setEnabled(has_edit_permission)
        self.preview_btn.setEnabled(has_edit_permission)
        
        # 更新输入输出相关控件权限
        self.browse_file_btn.setEnabled(has_edit_permission)
        self.browse_dir_btn.setEnabled(has_edit_permission)
        self.browse_output_btn.setEnabled(has_edit_permission)
        
        # 更新水印检测设置权限
        self.sample_frames_spin.setEnabled(has_edit_permission)
        self.min_frames_spin.setEnabled(has_edit_permission)
        self.dilation_spin.setEnabled(has_edit_permission)
        self.color_segmentation_checkbox.setEnabled(has_edit_permission)
        self.min_comp_spin.setEnabled(has_edit_permission)
        
        # 控制管理员标签页的可见性
        tabs = self.centralWidget().layout().itemAt(0).widget()
        if has_admin_permission:
            tabs.setTabVisible(self.admin_tab_index, True)
        else:
            tabs.setTabVisible(self.admin_tab_index, False)
        
        self.log(f"用户 {username} 登录，权限: 编辑={has_edit_permission}, 管理={has_admin_permission}")
    
    def setup_admin_tab(self, tab):
        """设置管理员功能标签页"""
        layout = QVBoxLayout(tab)
        
        # 创建子标签页
        self.admin_subtabs = QTabWidget()
        layout.addWidget(self.admin_subtabs)
        
        # 用户管理子标签页
        user_management_tab = QWidget()
        self.admin_subtabs.addTab(user_management_tab, "用户管理")
        self.setup_user_management_tab(user_management_tab)
        
        # 操作日志子标签页
        operation_logs_tab = QWidget()
        self.admin_subtabs.addTab(operation_logs_tab, "操作日志")
        self.setup_operation_logs_tab(operation_logs_tab)
    
    def setup_user_management_tab(self, tab):
        """设置用户管理子标签页"""
        layout = QVBoxLayout(tab)
        
        # 用户列表区域
        user_list_group = QGroupBox("用户列表")
        user_list_layout = QVBoxLayout()
        
        # 用户列表表格
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["用户名", "权限", "状态", "操作"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        user_list_layout.addWidget(self.user_table)
        user_list_group.setLayout(user_list_layout)
        layout.addWidget(user_list_group)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        
        self.refresh_users_btn = QPushButton("刷新用户列表")
        self.refresh_users_btn.clicked.connect(self.refresh_user_list)
        button_layout.addWidget(self.refresh_users_btn)
        
        self.delete_user_btn = QPushButton("删除选中用户")
        self.delete_user_btn.clicked.connect(self.delete_selected_user)
        button_layout.addWidget(self.delete_user_btn)
        
        layout.addLayout(button_layout)
        
        # 添加新管理员区域
        add_admin_group = QGroupBox("添加新管理员")
        add_admin_layout = QVBoxLayout()
        
        # 用户名输入
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("用户名:"))
        self.new_admin_username = QLineEdit()
        username_layout.addWidget(self.new_admin_username)
        add_admin_layout.addLayout(username_layout)
        
        # 密码输入
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("密码:"))
        self.new_admin_password = QLineEdit()
        self.new_admin_password.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.new_admin_password)
        add_admin_layout.addLayout(password_layout)
        
        # 确认密码输入
        confirm_layout = QHBoxLayout()
        confirm_layout.addWidget(QLabel("确认密码:"))
        self.new_admin_confirm = QLineEdit()
        self.new_admin_confirm.setEchoMode(QLineEdit.Password)
        confirm_layout.addWidget(self.new_admin_confirm)
        add_admin_layout.addLayout(confirm_layout)
        
        # 添加按钮
        self.add_admin_btn = QPushButton("添加管理员")
        self.add_admin_btn.clicked.connect(self.add_new_admin)
        add_admin_layout.addWidget(self.add_admin_btn)
        
        add_admin_group.setLayout(add_admin_layout)
        layout.addWidget(add_admin_group)
        
        # 初始刷新用户列表
        self.refresh_user_list()
    
    def refresh_user_list(self):
        """刷新用户列表"""
        from core.security.access_control import _access_controller
        
        # 清空表格
        self.user_table.setRowCount(0)
        
        # 获取所有用户
        users = _access_controller.users
        
        # 添加到表格
        for row, (username, user_info) in enumerate(users.items()):
            self.user_table.insertRow(row)
            
            # 用户名
            username_item = QTableWidgetItem(username)
            self.user_table.setItem(row, 0, username_item)
            
            # 权限
            permissions = ", ".join(user_info["permissions"])
            permission_item = QTableWidgetItem(permissions)
            self.user_table.setItem(row, 1, permission_item)
            
            # 状态
            status = "启用" if user_info["is_active"] else "禁用"
            status_item = QTableWidgetItem(status)
            self.user_table.setItem(row, 2, status_item)
            
            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            # 不能删除当前登录用户
            if username != self.current_user['username']:
                delete_btn = QPushButton("删除")
                delete_btn.setFixedWidth(60)
                delete_btn.clicked.connect(lambda checked, u=username: self.delete_user(u))
                button_layout.addWidget(delete_btn)
            
            button_widget.setLayout(button_layout)
            self.user_table.setCellWidget(row, 3, button_widget)
    
    def delete_selected_user(self):
        """删除选中用户"""
        selected_items = self.user_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要删除的用户")
            return
        
        # 获取选中行的用户名
        selected_row = selected_items[0].row()
        username_item = self.user_table.item(selected_row, 0)
        if not username_item:
            QMessageBox.warning(self, "警告", "无法获取选中用户信息")
            return
        
        username = username_item.text()
        self.delete_user(username)
    
    def delete_user(self, username):
        """删除指定用户"""
        # 不能删除当前登录用户
        if username == self.current_user['username']:
            QMessageBox.warning(self, "警告", "不能删除当前登录的用户")
            return
        
        # 二次确认
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除用户 '{username}' 吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from core.security.access_control import deactivate_user
            from core.operation_logger import log_operation
            
            # 停用用户（实际是将is_active设置为False）
            if deactivate_user(username):
                QMessageBox.information(self, "成功", f"用户 '{username}' 已删除")
                
                # 记录操作日志
                if self.current_user:
                    log_operation(
                        self.current_user['username'],
                        "delete_user",
                        "success",
                        details=f"删除用户: {username}"
                    )
                
                # 刷新用户列表
                self.refresh_user_list()
            else:
                QMessageBox.error(self, "错误", f"删除用户 '{username}' 失败")
    
    def add_new_admin(self):
        """添加新管理员"""
        username = self.new_admin_username.text().strip()
        password = self.new_admin_password.text()
        confirm = self.new_admin_confirm.text()
        
        # 表单验证
        if not username:
            QMessageBox.warning(self, "警告", "请输入用户名")
            return
        
        if not password:
            QMessageBox.warning(self, "警告", "请输入密码")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "警告", "两次输入的密码不一致")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "警告", "密码长度不能少于6个字符")
            return
        
        from core.security.access_control import add_new_user
        from core.operation_logger import log_operation
        
        # 添加管理员用户，授予所有权限
        if add_new_user(username, password, ["view", "edit", "delete", "admin"]):
            QMessageBox.information(self, "成功", f"管理员 '{username}' 已添加")
            
            # 记录操作日志
            if self.current_user:
                log_operation(
                    self.current_user['username'],
                    "add_admin",
                    "success",
                    details=f"添加管理员: {username}"
                )
            
            # 清空表单
            self.new_admin_username.clear()
            self.new_admin_password.clear()
            self.new_admin_confirm.clear()
            
            # 刷新用户列表
            self.refresh_user_list()
        else:
            QMessageBox.error(self, "错误", f"添加管理员 '{username}' 失败，用户名可能已存在")
    
    def setup_operation_logs_tab(self, tab):
        """设置操作日志子标签页"""
        layout = QVBoxLayout(tab)
        
        # 筛选区域
        filter_group = QGroupBox("日志筛选")
        filter_layout = QVBoxLayout()
        
        # 用户名筛选
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("用户名:"))
        self.log_username_filter = QLineEdit()
        username_layout.addWidget(self.log_username_filter)
        filter_layout.addLayout(username_layout)
        
        # 操作类型筛选
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("操作类型:"))
        self.log_type_filter = QLineEdit()
        type_layout.addWidget(self.log_type_filter)
        filter_layout.addLayout(type_layout)
        
        # 时间筛选
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("开始时间:"))
        self.log_start_time = QLineEdit()
        self.log_start_time.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        time_layout.addWidget(self.log_start_time)
        
        time_layout.addWidget(QLabel("结束时间:"))
        self.log_end_time = QLineEdit()
        self.log_end_time.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        time_layout.addWidget(self.log_end_time)
        filter_layout.addLayout(time_layout)
        
        # 查询按钮
        query_layout = QHBoxLayout()
        self.query_logs_btn = QPushButton("查询日志")
        self.query_logs_btn.clicked.connect(self.refresh_operation_logs)
        query_layout.addWidget(self.query_logs_btn)
        
        self.clear_filters_btn = QPushButton("清空筛选")
        self.clear_filters_btn.clicked.connect(self.clear_log_filters)
        query_layout.addWidget(self.clear_filters_btn)
        filter_layout.addLayout(query_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 日志列表区域
        log_list_group = QGroupBox("操作日志")
        log_list_layout = QVBoxLayout()
        
        # 日志表格
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels(["时间", "用户名", "操作类型", "结果", "IP地址", "详细信息"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        log_list_layout.addWidget(self.log_table)
        log_list_group.setLayout(log_list_layout)
        layout.addWidget(log_list_group)
        
        # 初始刷新日志
        self.refresh_operation_logs()
    
    def refresh_operation_logs(self):
        """刷新操作日志"""
        from core.operation_logger import get_operation_logs
        from datetime import datetime
        
        # 获取筛选条件
        username = self.log_username_filter.text().strip() or None
        operation_type = self.log_type_filter.text().strip() or None
        
        # 解析时间
        start_time = None
        end_time = None
        
        if self.log_start_time.text().strip():
            try:
                start_time = datetime.strptime(self.log_start_time.text().strip(), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                QMessageBox.warning(self, "警告", "开始时间格式错误，请使用YYYY-MM-DD HH:MM:SS格式")
                return
        
        if self.log_end_time.text().strip():
            try:
                end_time = datetime.strptime(self.log_end_time.text().strip(), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                QMessageBox.warning(self, "警告", "结束时间格式错误，请使用YYYY-MM-DD HH:MM:SS格式")
                return
        
        # 查询日志
        logs, total_count = get_operation_logs(
            username=username,
            operation_type=operation_type,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=1000  # 显示最近1000条
        )
        
        # 清空表格
        self.log_table.setRowCount(0)
        
        # 添加到表格
        for row, log in enumerate(logs):
            self.log_table.insertRow(row)
            
            # 时间
            time_str = log['operation_time'].strftime("%Y-%m-%d %H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            self.log_table.setItem(row, 0, time_item)
            
            # 用户名
            username_item = QTableWidgetItem(log['username'])
            self.log_table.setItem(row, 1, username_item)
            
            # 操作类型
            type_item = QTableWidgetItem(log['operation_type'])
            self.log_table.setItem(row, 2, type_item)
            
            # 结果
            result_item = QTableWidgetItem(log['operation_result'])
            self.log_table.setItem(row, 3, result_item)
            
            # IP地址
            ip_item = QTableWidgetItem(log['ip_address'] or "-")
            self.log_table.setItem(row, 4, ip_item)
            
            # 详细信息
            details_item = QTableWidgetItem(log['details'] or "-")
            self.log_table.setItem(row, 5, details_item)
    
    def clear_log_filters(self):
        """清空筛选条件"""
        self.log_username_filter.clear()
        self.log_type_filter.clear()
        self.log_start_time.clear()
        self.log_end_time.clear()
        self.refresh_operation_logs()
    
    def save_settings(self):
        """保存设置"""
        try:
            self.config.update({
                "sample_frames": self.sample_frames_spin.value(),
                "min_frames": self.min_frames_spin.value(),
                "dilation_size": self.dilation_spin.value(),
                "use_gpu": self.gpu_checkbox.isChecked(),
                "ldm_steps": self.ldm_steps_spin.value(),
                "margin": self.margin_spin.value(),
                "use_color_segmentation": self.color_segmentation_checkbox.isChecked(),
                "min_component_area": self.min_comp_spin.value(),
                "morph_open": self.config.get('morph_open', 3),
                "morph_close": self.config.get('morph_close', 7),
                "use_canny": self.config.get('use_canny', True),
                "canny_low": self.config.get('canny_low', 100),
                "canny_high": self.config.get('canny_high', 200),
                "hd_strategy": self.strategy_combo.currentText(),
                "preview_before_process": self.preview_checkbox.isChecked(),
                "auto_select_roi": self.auto_roi_radio.isChecked()  # 保存ROI选择模式
            })
            
            import json
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", "设置已保存")
            self.log("设置已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {e}")
    
    def validate_inputs(self):
        """验证输入"""
        if not self.input_path_edit.text():
            QMessageBox.warning(self, "警告", "请选择输入文件或目录")
            return False
        
        if not self.output_path_edit.text():
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return False
        
        import os
        output_dir = self.output_path_edit.text()
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建输出目录: {e}")
            return False
        
        return True
    
    def initialize_models(self):
        """初始化模型"""
        try:
            use_gpu = self.gpu_checkbox.isChecked()
            
            # 初始化水印检测器
            self.detector = WatermarkDetector(
                num_sample_frames=self.sample_frames_spin.value(),
                min_frame_count=self.min_frames_spin.value(),
                dilation_kernel_size=self.dilation_spin.value(),
                use_color_segmentation=self.color_segmentation_checkbox.isChecked(),
                min_component_area=self.min_comp_spin.value(),
                morph_open=self.config.get('morph_open', 3),
                morph_close=self.config.get('morph_close', 7),
                use_canny=self.config.get('use_canny', True),
                canny_low=self.config.get('canny_low', 100),
                canny_high=self.config.get('canny_high', 200)
            )
            
            # 初始化Lama修复器
            self.inpainter = LamaInpainter()
            # 如果 Lama 不可用，则启用 cv2 回退
            if not self.inpainter.is_available():
                self.inpainter.use_cv2_fallback = True
                self.log("警告: Lama模型不可用，将使用OpenCV回退修复")
            else:
                try:
                    self.inpainter.initialize(
                        device="cuda" if use_gpu and check_gpu()[0] else "cpu",
                        ldm_steps=self.ldm_steps_spin.value(),
                        hd_strategy=self.strategy_combo.currentText()
                    )
                except Exception as e:
                    self.log(f"Lama初始化失败，启用cv2回退: {e}")
                    self.inpainter.use_cv2_fallback = True
            
            self.log("模型初始化完成")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"模型初始化失败: {e}")
            self.log(f"模型初始化失败: {e}")
            return False
    
    def show_preview(self):
        """显示预览"""
        if not self.validate_inputs():
            return
        
        input_path = self.input_path_edit.text()
        
        # 如果是目录，选择第一个视频文件
        if os.path.isdir(input_path):
            import glob
            videos = glob.glob(os.path.join(input_path, "*"))
            if not videos:
                QMessageBox.warning(self, "警告", "目录中没有视频文件")
                return
            video_path = videos[0]
        else:
            video_path = input_path.split(";")[0].strip()
        
        # 初始化模型
        if not self.initialize_models():
            return
        
        # 显示预览对话框
        try:
            from moviepy import VideoFileClip
            video_clip = VideoFileClip(video_path)
            
            # 根据设置中的ROI选择模式来配置detector
            auto_select_roi = self.auto_roi_radio.isChecked()
            
            # 创建预览对话框
            preview_dialog = PreviewDialog(video_clip, self.detector, 
                                         self.inpainter, self.config, self)
            
            # 如果是自动选择模式，自动检测ROI
            if auto_select_roi:
                preview_dialog.auto_detect_roi()
            
            if preview_dialog.exec_():
                self.log("预览完成，可以开始处理")
            else:
                self.log("预览取消")
                
            video_clip.close()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"预览失败: {e}")
            self.log(f"预览失败: {e}")
    
    def start_processing(self):
        """开始处理"""
        if not self.validate_inputs():
            return
        
        # 获取输入路径
        input_path = self.input_path_edit.text()
        
        # 如果是目录，扫描所有视频文件
        if os.path.isdir(input_path):
            import glob
            self.video_paths = []
            for ext in ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.flv", "*.wmv"]:
                self.video_paths.extend(glob.glob(os.path.join(input_path, ext)))
        else:
            self.video_paths = [path.strip() for path in input_path.split(";")]
        
        if not self.video_paths:
            QMessageBox.warning(self, "警告", "没有找到视频文件")
            return
        
        # 初始化模型
        if not self.initialize_models():
            return
        
        # 创建进度对话框
        self.progress_dialog = ProgressDialog(len(self.video_paths), self)
        
        # 创建处理线程
        # 确保配置中包含ROI选择模式
        self.config["auto_select_roi"] = self.auto_roi_radio.isChecked()
        
        self.processing_thread = ProcessingThread(
            self.video_paths,
            self.output_path_edit.text(),
            self.detector,
            self.inpainter,
            self.config,
            self.current_user
        )
        
        # 连接信号
        self.processing_thread.progress.connect(self.progress_dialog.update_progress)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        
        # 启动线程
        self.processing_thread.start()
        self.progress_dialog.exec_()
    
    def on_processing_finished(self, result):
        """处理完成"""
        self.progress_dialog.close()
        
        if result.get("success"):
            results = result.get("results", [])
            success_count = sum(1 for r in results if r.get("success"))
            
            QMessageBox.information(
                self, "完成", 
                f"处理完成！\n成功: {success_count}/{len(results)} 个视频"
            )
            
            # 记录导出历史
            if self.current_user:
                username = self.current_user['username']
                for r in results:
                    if r.get("success"):
                        output_path = r.get("output_path")
                        file_name = os.path.basename(output_path)
                        try:
                            file_size = os.path.getsize(output_path)
                        except:
                            file_size = None
                        
                        add_history_record(username, output_path, 'export', file_name, file_size)
            
            for r in results:
                if r.get("success"):
                    self.log(f"已处理: {r.get('video_name')}")
                    self.log(f"  保存到: {r.get('output_path')}")
                    self.log(f"  耗时: {r.get('processing_time')}")
        else:
            QMessageBox.warning(self, "完成", "处理完成但部分视频失败")
    
    def setup_history_tab(self, tab):
        """设置历史记录标签页"""
        layout = QVBoxLayout(tab)
        
        # 筛选和控制区域
        control_layout = QHBoxLayout()
        
        # 操作类型筛选
        self.operation_type_combo = QComboBox()
        self.operation_type_combo.addItem("所有操作", None)
        self.operation_type_combo.addItem("导入", "import")
        self.operation_type_combo.addItem("导出", "export")
        control_layout.addWidget(QLabel("操作类型:"))
        control_layout.addWidget(self.operation_type_combo)
        
        # 刷新按钮
        self.refresh_history_btn = QPushButton("刷新")
        self.refresh_history_btn.clicked.connect(self.refresh_history)
        control_layout.addWidget(self.refresh_history_btn)
        
        # 清空历史记录按钮
        self.clear_history_btn = QPushButton("清空历史")
        self.clear_history_btn.clicked.connect(self.clear_history)
        control_layout.addWidget(self.clear_history_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "操作类型", "文件名", "视频路径", "文件大小", "操作时间"
        ])
        # 设置列宽策略
        # ID列固定宽度
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # 操作类型列固定宽度
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        # 文件名和视频路径列根据内容自动调整宽度
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        # 文件大小和操作时间列固定宽度
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        # 禁止编辑
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 允许选择行
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        # 设置单元格文本不自动换行
        self.history_table.setWordWrap(False)
        # 启用水平滚动
        self.history_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.history_table)
        
        # 分页控制
        pagination_layout = QHBoxLayout()
        
        self.page_label = QLabel("第 1 页，共 1 页")
        pagination_layout.addWidget(self.page_label)
        
        pagination_layout.addStretch()
        
        self.prev_page_btn = QPushButton("上一页")
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.prev_page_btn.setEnabled(False)
        pagination_layout.addWidget(self.prev_page_btn)
        
        self.next_page_btn = QPushButton("下一页")
        self.next_page_btn.clicked.connect(self.next_page)
        self.next_page_btn.setEnabled(False)
        pagination_layout.addWidget(self.next_page_btn)
        
        layout.addLayout(pagination_layout)
        
        # 空状态提示
        self.empty_state_label = QLabel("暂无历史记录")
        self.empty_state_label.setAlignment(Qt.AlignCenter)
        self.empty_state_label.setStyleSheet("font-size: 16px; color: #999;")
        self.empty_state_label.hide()
        layout.addWidget(self.empty_state_label)
        
        # 历史记录数据
        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        self.total_records = 0
        
        # 加载历史记录
        self.refresh_history()
    
    def refresh_history(self):
        """刷新历史记录"""
        if not self.current_user:
            return
        
        username = self.current_user['username']
        operation_type = self.operation_type_combo.currentData()
        
        # 获取历史记录
        history_list, total_count = get_history_records(
            username,
            page=self.current_page,
            page_size=self.page_size,
            operation_type=operation_type
        )
        
        self.total_records = total_count
        self.total_pages = (total_count + self.page_size - 1) // self.page_size
        
        # 更新表格
        self.history_table.setRowCount(0)
        
        for item in history_list:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(item['id']))
            self.history_table.setItem(row, 0, id_item)
            
            # 操作类型
            type_item = QTableWidgetItem("导入" if item['operation_type'] == 'import' else "导出")
            self.history_table.setItem(row, 1, type_item)
            
            # 文件名 - 添加tooltip显示完整名称
            filename_item = QTableWidgetItem(item['file_name'])
            filename_item.setToolTip(item['file_name'])
            self.history_table.setItem(row, 2, filename_item)
            
            # 视频路径 - 添加tooltip显示完整路径
            path_item = QTableWidgetItem(item['video_path'])
            path_item.setToolTip(item['video_path'])
            self.history_table.setItem(row, 3, path_item)
            
            # 文件大小
            size_item = QTableWidgetItem(self.format_file_size(item['file_size']))
            self.history_table.setItem(row, 4, size_item)
            
            # 操作时间
            time_item = QTableWidgetItem(item['operation_time'].strftime("%Y-%m-%d %H:%M:%S"))
            self.history_table.setItem(row, 5, time_item)
        
        # 更新分页信息
        self.page_label.setText(f"第 {self.current_page} 页，共 {self.total_pages} 页")
        
        # 更新分页按钮状态
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)
        
        # 显示/隐藏空状态
        if total_count == 0:
            self.history_table.hide()
            self.empty_state_label.show()
        else:
            self.history_table.show()
            self.empty_state_label.hide()
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes is None:
            return "未知"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_history()
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_history()
    
    def clear_history(self):
        """清空历史记录"""
        if not self.current_user:
            return
        
        reply = QMessageBox.question(
            self, "确认", 
            "确定要清空所有历史记录吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            username = self.current_user['username']
            if delete_all_history_records(username):
                QMessageBox.information(self, "成功", "历史记录已清空")
                self.refresh_history()
            else:
                QMessageBox.warning(self, "失败", "清空历史记录失败")
    
    def on_processing_error(self, error_msg):
        """处理错误"""
        self.progress_dialog.close()
        QMessageBox.critical(self, "错误", f"处理失败: {error_msg}")
        self.log(f"处理失败: {error_msg}")
    
    def setup_admin_tab(self, tab):
        """设置管理员功能标签页"""
        layout = QVBoxLayout(tab)
        
        # 创建子标签页
        admin_tabs = QTabWidget()
        layout.addWidget(admin_tabs)
        
        # 用户管理子标签页
        user_management_tab = QWidget()
        admin_tabs.addTab(user_management_tab, "用户管理")
        self.setup_user_management_tab(user_management_tab)
        
        # 操作日志子标签页
        operation_logs_tab = QWidget()
        admin_tabs.addTab(operation_logs_tab, "操作日志")
        self.setup_operation_logs_tab(operation_logs_tab)
    
    def setup_user_management_tab(self, tab):
        """设置用户管理子标签页"""
        layout = QVBoxLayout(tab)
        
        # 用户列表区域
        user_list_group = QGroupBox("用户列表")
        user_list_layout = QVBoxLayout()
        
        # 用户表格
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(3)
        self.user_table.setHorizontalHeaderLabels(["用户名", "权限级别", "状态"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        user_list_layout.addWidget(self.user_table)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新用户列表")
        refresh_btn.clicked.connect(self.refresh_user_list)
        user_list_layout.addWidget(refresh_btn)
        
        user_list_group.setLayout(user_list_layout)
        layout.addWidget(user_list_group)
        
        # 用户管理操作区域
        user_operations_group = QGroupBox("用户操作")
        user_operations_layout = QVBoxLayout()
        
        # 删除用户按钮
        delete_btn = QPushButton("删除选中用户")
        delete_btn.clicked.connect(self.delete_selected_user)
        user_operations_layout.addWidget(delete_btn)
        
        # 添加管理员区域
        add_admin_group = QGroupBox("添加新管理员")
        add_admin_layout = QVBoxLayout()
        
        # 用户名输入
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("用户名:"))
        self.new_admin_username = QLineEdit()
        username_layout.addWidget(self.new_admin_username)
        add_admin_layout.addLayout(username_layout)
        
        # 密码输入
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("密码:"))
        self.new_admin_password = QLineEdit()
        self.new_admin_password.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.new_admin_password)
        add_admin_layout.addLayout(password_layout)
        
        # 确认密码输入
        confirm_password_layout = QHBoxLayout()
        confirm_password_layout.addWidget(QLabel("确认密码:"))
        self.new_admin_confirm_password = QLineEdit()
        self.new_admin_confirm_password.setEchoMode(QLineEdit.Password)
        confirm_password_layout.addWidget(self.new_admin_confirm_password)
        add_admin_layout.addLayout(confirm_password_layout)
        
        # 添加按钮
        add_btn = QPushButton("添加管理员")
        add_btn.clicked.connect(self.add_new_admin)
        add_admin_layout.addWidget(add_btn)
        
        add_admin_group.setLayout(add_admin_layout)
        user_operations_layout.addWidget(add_admin_group)
        
        user_operations_group.setLayout(user_operations_layout)
        layout.addWidget(user_operations_group)
        
        # 加载用户列表
        self.refresh_user_list()
    
    def setup_operation_logs_tab(self, tab):
        """设置操作日志子标签页"""
        layout = QVBoxLayout(tab)
        
        # 筛选区域
        filter_group = QGroupBox("日志筛选")
        filter_layout = QHBoxLayout()
        
        # 用户名筛选
        filter_layout.addWidget(QLabel("用户名:"))
        self.log_username_filter = QLineEdit()
        self.log_username_filter.setPlaceholderText("输入用户名筛选")
        filter_layout.addWidget(self.log_username_filter)
        
        # 操作类型筛选
        filter_layout.addWidget(QLabel("操作类型:"))
        self.log_operation_type_filter = QLineEdit()
        self.log_operation_type_filter.setPlaceholderText("输入操作类型筛选")
        filter_layout.addWidget(self.log_operation_type_filter)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新日志")
        refresh_btn.clicked.connect(self.refresh_operation_logs)
        filter_layout.addWidget(refresh_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 日志表格
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["操作时间", "用户名", "操作类型", "操作结果", "详细信息"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.verticalHeader().setDefaultSectionSize(60)  # 设置行高以显示详细信息
        layout.addWidget(self.log_table)
        
        # 加载操作日志
        self.refresh_operation_logs()
    
    def refresh_user_list(self):
        """刷新用户列表"""
        from core.security.access_control import _access_controller
        if _access_controller is None:
            from core.security.access_control import initialize_access_control
            initialize_access_control()
        
        # 获取所有用户
        users = _access_controller.users
        
        # 清空表格
        self.user_table.setRowCount(0)
        
        # 添加用户到表格
        for username, user_info in users.items():
            row = self.user_table.rowCount()
            self.user_table.insertRow(row)
            
            # 用户名
            username_item = QTableWidgetItem(username)
            self.user_table.setItem(row, 0, username_item)
            
            # 权限级别
            if "admin" in user_info["permissions"]:
                permission_item = QTableWidgetItem("管理员")
            else:
                permission_item = QTableWidgetItem("普通用户")
            self.user_table.setItem(row, 1, permission_item)
            
            # 状态
            status_item = QTableWidgetItem("激活" if user_info["is_active"] else "停用")
            self.user_table.setItem(row, 2, status_item)
    
    def delete_selected_user(self):
        """删除选中的用户"""
        selected_row = self.user_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的用户")
            return
        
        username = self.user_table.item(selected_row, 0).text()
        
        # 不能删除自己
        if username == self.current_user['username']:
            QMessageBox.warning(self, "警告", "不能删除当前登录的用户")
            return
        
        # 二次确认
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除用户 '{username}' 吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from core.security.access_control import _access_controller
            if _access_controller is None:
                from core.security.access_control import initialize_access_control
                initialize_access_control()
            
            # 从字典中删除用户
            if username in _access_controller.users:
                del _access_controller.users[username]
                if _access_controller._save_users():
                    QMessageBox.information(self, "成功", f"用户 '{username}' 已删除")
                    # 记录操作日志
                    from core.operation_logger import log_operation
                    log_operation(
                        self.current_user['username'],
                        'delete_user',
                        'success',
                        details=f"删除了用户: {username}"
                    )
                    # 刷新用户列表
                    self.refresh_user_list()
                else:
                    QMessageBox.error(self, "错误", "删除用户失败")
    
    def add_new_admin(self):
        """添加新管理员用户"""
        username = self.new_admin_username.text().strip()
        password = self.new_admin_password.text()
        confirm_password = self.new_admin_confirm_password.text()
        
        # 表单验证
        if not username:
            QMessageBox.warning(self, "警告", "请输入用户名")
            return
        
        if not password:
            QMessageBox.warning(self, "警告", "请输入密码")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "警告", "两次输入的密码不一致")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "警告", "密码长度不能少于6个字符")
            return
        
        from core.security.access_control import _access_controller
        if _access_controller is None:
            from core.security.access_control import initialize_access_control
            initialize_access_control()
        
        # 检查用户名是否已存在
        if username in _access_controller.users:
            QMessageBox.warning(self, "警告", "用户名已存在")
            return
        
        # 添加新管理员
        if _access_controller.add_user(username, password, ["view", "edit", "delete", "admin"]):
            QMessageBox.information(self, "成功", f"管理员用户 '{username}' 已添加")
            # 记录操作日志
            from core.operation_logger import log_operation
            log_operation(
                self.current_user['username'],
                'add_admin',
                'success',
                details=f"添加了管理员用户: {username}"
            )
            # 清空表单
            self.new_admin_username.clear()
            self.new_admin_password.clear()
            self.new_admin_confirm_password.clear()
            # 刷新用户列表
            self.refresh_user_list()
        else:
            QMessageBox.error(self, "错误", "添加管理员失败")
    
    def refresh_operation_logs(self):
        """刷新操作日志"""
        from core.operation_logger import get_operation_logs
        from datetime import datetime
        
        # 获取筛选条件
        username = self.log_username_filter.text().strip() or None
        operation_type = self.log_operation_type_filter.text().strip() or None
        
        # 获取所有日志（不分页，因为日志量不会太大）
        logs, _ = get_operation_logs(
            username=username,
            operation_type=operation_type,
            page=1,
            page_size=1000
        )
        
        # 清空表格
        self.log_table.setRowCount(0)
        
        # 添加日志到表格
        for log in logs:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            
            # 操作时间
            time_item = QTableWidgetItem(log['operation_time'].strftime("%Y-%m-%d %H:%M:%S"))
            self.log_table.setItem(row, 0, time_item)
            
            # 用户名
            username_item = QTableWidgetItem(log['username'])
            self.log_table.setItem(row, 1, username_item)
            
            # 操作类型
            operation_type_item = QTableWidgetItem(log['operation_type'])
            self.log_table.setItem(row, 2, operation_type_item)
            
            # 操作结果
            result_item = QTableWidgetItem(log['operation_result'])
            self.log_table.setItem(row, 3, result_item)
            
            # 详细信息
            details = log.get('details', '')
            details_item = QTableWidgetItem(details)
            details_item.setToolTip(details)  # 添加tooltip显示完整详细信息
            self.log_table.setItem(row, 4, details_item)
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认", 
                "处理正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.processing_thread.stop()
                self.processing_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()