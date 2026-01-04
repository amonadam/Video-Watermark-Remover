#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全模块验证脚本
用于测试项目中所有安全模块的功能是否正常工作
"""

import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入安全模块
from src.core.security.file_security import (
    validate_video_file, create_secure_temp_file, 
    secure_delete_file, calculate_file_hash
)
from src.core.security.system_security import (
    sanitize_input, safe_execute_command, _is_safe_command
)
from src.core.security.config_security import (
    secure_load_config, secure_save_config, validate_config, sanitize_config_value,
    generate_config_secret
)
from src.core.security.privacy_protection import (
    remove_video_metadata, sanitize_video_filename, anonymize_user_data, redact_sensitive_info
)
from src.core.security.access_control import (
    authenticate_user, check_user_permission, add_new_user, update_user_permissions
)

class SecurityTestRunner:
    """安全测试运行器"""
    
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        self.temp_dir = tempfile.mkdtemp()
        print(f"创建临时测试目录: {self.temp_dir}")
    
    def run_test(self, test_name, test_func):
        """运行单个测试"""
        print(f"\n=== 测试: {test_name} ===")
        try:
            result = test_func()
            if result:
                print(f"✅ 通过: {test_name}")
                self.results['passed'] += 1
            else:
                print(f"❌ 失败: {test_name}")
                self.results['failed'] += 1
                self.results['errors'].append(f"测试失败: {test_name}")
        except Exception as e:
            print(f"❌ 错误: {test_name} - {str(e)}")
            self.results['failed'] += 1
            self.results['errors'].append(f"测试错误: {test_name} - {str(e)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始执行安全模块测试...")
        
        # 文件安全模块测试
        self.test_file_security()
        
        # 系统安全模块测试
        self.test_system_security()
        
        # 配置安全模块测试
        self.test_config_security()
        
        # 隐私保护模块测试
        self.test_privacy_protection()
        
        # 访问控制模块测试
        self.test_access_control()
        
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        print(f"\n\n=== 安全测试总结 ===")
        print(f"通过测试: {self.results['passed']}")
        print(f"失败测试: {self.results['failed']}")
        print(f"总测试数: {self.results['passed'] + self.results['failed']}")
        
        if self.results['errors']:
            print(f"\n错误详情:")
            for error in self.results['errors']:
                print(f"  - {error}")
    
    def cleanup(self):
        """清理临时文件"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"清理临时测试目录: {self.temp_dir}")
    
    # 文件安全模块测试
    def test_file_security(self):
        """测试文件安全模块"""
        print("\n--- 文件安全模块测试 ---")
        
        # 测试文件类型验证
        self.run_test("文件类型验证（视频文件）", self.test_validate_video_file)
        

        
        # 测试临时文件生成
        self.run_test("临时文件生成", self.test_generate_temp_file)
        
        # 测试文件哈希
        self.run_test("文件哈希计算", self.test_get_file_hash)
    
    def test_validate_video_file(self):
        """测试视频文件验证"""
        # 创建一个模拟的视频文件
        test_file = os.path.join(self.temp_dir, "test.mp4")
        with open(test_file, 'w') as f:
            f.write("mock video data")
        
        # 测试有效视频文件
        result = validate_video_file(test_file)
        return result
    

    
    def test_generate_temp_file(self):
        """测试临时文件生成"""
        temp_file = create_secure_temp_file(b"test data", suffix=".txt")
        exists = os.path.exists(temp_file)
        if exists:
            secure_delete_file(temp_file)
        return exists
    
    def test_get_file_hash(self):
        """测试文件哈希计算"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        file_hash = calculate_file_hash(test_file)
        return len(file_hash) == 64  # SHA-256哈希长度为64个字符
    
    # 系统安全模块测试
    def test_system_security(self):
        """测试系统安全模块"""
        print("\n--- 系统安全模块测试 ---")
        
        # 测试输入净化
        self.run_test("输入净化", self.test_sanitize_input)
        
        # 测试命令注入防护
        self.run_test("命令注入防护（安全命令）", self.test_safe_command)
        self.run_test("命令注入防护（危险命令）", self.test_dangerous_command)
    
    def test_sanitize_input(self):
        """测试输入净化"""
        # 测试HTML注入净化
        test_input = "<script>alert('xss')</script>"
        sanitized = sanitize_input(test_input)
        # sanitize_input函数会移除除了允许字符集之外的所有字符
        return sanitized == "scriptalertxssscript"
    
    def test_safe_command(self):
        """测试安全命令执行"""
        # 测试安全命令
        if sys.platform.startswith('win'):
            # Windows系统使用cmd.exe执行dir命令
            result = safe_execute_command(["cmd.exe", "/c", "dir"])
            return result is not None
        else:
            # Linux/macOS使用echo命令
            result = safe_execute_command(["echo", "hello world"])
            return result and "hello world" in result.stdout
    
    def test_dangerous_command(self):
        """测试危险命令防护"""
        # 测试包含命令注入的危险命令
        dangerous_cmd = ["echo", "hello; rm -rf /"]
        try:
            safe_execute_command(dangerous_cmd)
            return False  # 不应该执行成功
        except ValueError:
            return True  # 应该抛出异常
    
    # 配置安全模块测试
    def test_config_security(self):
        """测试配置安全模块"""
        print("\n--- 配置安全模块测试 ---")
        
        # 测试配置加密解密
        self.run_test("配置加密解密", self.test_config_encryption)
        
        # 测试安全配置加载保存
        self.run_test("安全配置加载保存", self.test_secure_config_io)
    
    def test_config_encryption(self):
        """测试配置加密解密"""
        test_config = {
            "api_key": "test_key_123",
            "password": "secret_password",
            "safe_key": "public_value"
        }
        
        secret_key = "test_secret_key_12345"
        config_file = os.path.join(self.temp_dir, "test_encryption.json")
        
        # 安全保存配置（加密敏感字段）
        save_result = secure_save_config(test_config, config_file, secret_key)
        if not save_result:
            return False
        
        # 安全加载配置（解密敏感字段）
        loaded_config = secure_load_config(config_file, secret_key)
        if not loaded_config:
            return False
        
        return test_config["api_key"] == loaded_config["api_key"]
    
    def test_secure_config_io(self):
        """测试安全配置加载保存"""
        test_config = {
            "api_key": "test_key_123",
            "setting": "value"
        }
        
        secret_key = "test_secret_key_12345"
        config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # 保存安全配置
        secure_save_config(test_config, config_file, secret_key)
        
        # 加载安全配置
        loaded_config = secure_load_config(config_file, secret_key)
        
        return loaded_config and "api_key" in loaded_config
    
    # 隐私保护模块测试
    def test_privacy_protection(self):
        """测试隐私保护模块"""
        print("\n--- 隐私保护模块测试 ---")
        
        # 测试文本敏感信息编辑
        self.run_test("文本敏感信息编辑", self.test_redact_sensitive_info)
        
        # 测试用户数据匿名化
        self.run_test("用户数据匿名化", self.test_anonymize_user_data)
        
        # 测试视频文件名净化
        self.run_test("视频文件名净化", self.test_sanitize_video_filename)
    
    def test_redact_sensitive_info(self):
        """测试文本敏感信息编辑"""
        text = "我的邮箱是test@example.com，手机号是13812345678"
        redacted = redact_sensitive_info(text)
        return "***@***.***" in redacted and "***-****-****" in redacted
    
    def test_anonymize_user_data(self):
        """测试用户数据匿名化"""
        data = {
            "username": "zhangsan",
            "email": "zhangsan@example.com",
            "phone": "13812345678",
            "address": "北京市朝阳区"
        }
        
        anonymized = anonymize_user_data(data)
        return anonymized["username"] != "zhangsan" and anonymized["email"] != "zhangsan@example.com"
    
    def test_sanitize_video_filename(self):
        """测试视频文件名净化"""
        filename = "张三_2023-12-17_14:30:00_video.mp4"
        sanitized = sanitize_video_filename(filename)
        return "2023-12-17" not in sanitized and "14:30:00" not in sanitized
    
    # 访问控制模块测试
    def test_access_control(self):
        """测试访问控制模块"""
        print("\n--- 访问控制模块测试 ---")
        
        # 测试用户认证
        self.run_test("用户认证", self.test_user_authentication)
        
        # 测试权限检查
        self.run_test("权限检查", self.test_user_permission)
        
        # 测试添加新用户
        self.run_test("添加新用户", self.test_add_new_user)
    
    def test_user_authentication(self):
        """测试用户认证"""
        # 使用默认用户测试认证
        result = authenticate_user("admin", "admin123")
        return result is not None and result["username"] == "admin"
    
    def test_user_permission(self):
        """测试权限检查"""
        # 测试管理员权限
        admin_has_perm = check_user_permission("admin", "admin")
        # 测试普通用户没有管理员权限
        user_no_admin_perm = not check_user_permission("user", "admin")
        return admin_has_perm and user_no_admin_perm
    
    def test_add_new_user(self):
        """测试添加新用户"""
        # 使用临时目录中的用户数据库文件来避免权限问题
        import src.core.security.access_control as access_control
        
        # 保存原始控制器实例
        original_controller = access_control._access_controller
        
        try:
            # 初始化一个新的访问控制器，使用临时文件
            temp_users_db = os.path.join(self.temp_dir, "temp_users.json")
            access_control.initialize_access_control(temp_users_db)
            
            # 添加新用户
            username = "testuser"
            password = "testpass123"
            permissions = ["view"]
            
            add_result = access_control.add_new_user(username, password, permissions)
            
            if add_result:
                # 验证新用户可以认证
                auth_result = access_control.authenticate_user(username, password)
                return auth_result is not None and auth_result["username"] == username
            return False
        finally:
            # 恢复原始控制器实例
            access_control._access_controller = original_controller
            # 清理临时文件
            if os.path.exists(os.path.join(self.temp_dir, "temp_users.json")):
                os.remove(os.path.join(self.temp_dir, "temp_users.json"))

if __name__ == "__main__":
    runner = SecurityTestRunner()
    
    try:
        runner.run_all_tests()
    finally:
        runner.cleanup()
    
    # 根据测试结果设置退出码
    if runner.results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
