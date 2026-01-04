#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建初始用户脚本
用于生成系统的初始管理员用户
"""

import os
import sys

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.security import initialize_access_control, add_new_user

def create_initial_user():
    """
    创建初始管理员用户
    """
    print("创建系统初始用户...")
    
    try:
        # 初始化访问控制模块
        initialize_access_control(storage_type="sqlite")
        print("✓ 访问控制模块初始化成功")
        
        # 定义初始用户信息
        admin_username = "admin"
        admin_password = "Admin12345"
        
        # 创建初始管理员用户
        try:
            success = add_new_user(admin_username, admin_password, permissions=["view", "edit", "admin"])
            if success:
                print(f"✓ 成功创建初始管理员用户")
                print(f"  用户名: {admin_username}")
                print(f"  密码: {admin_password}")
                print(f"  权限: ['view', 'edit', 'admin']")
                print("\n📋 注意:")
                print("1. 请妥善保存初始管理员凭据")
                print("2. 首次登录后建议修改密码")
                print("3. 可以通过注册功能创建普通用户")
                return True
            else:
                print(f"✗ 创建初始管理员用户失败")
                return False
        except Exception as e:
            print(f"✗ 创建初始管理员用户时发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"✗ 创建初始用户时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_initial_user()
