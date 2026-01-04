#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户注册功能
"""

import os
import sys
import sqlite3

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.security import initialize_access_control, add_new_user, authenticate_user


def test_register_functionality():
    """
    测试用户注册功能
    """
    print("开始测试用户注册功能...")
    
    try:
        # 初始化访问控制模块
        initialize_access_control(storage_type="sqlite")
        print("✓ 访问控制模块初始化成功")
        
        # 定义测试用户信息
        test_username = "testuser"
        test_password = "Test12345"
        
        # 尝试注册新用户
        try:
            success = add_new_user(test_username, test_password, permissions=["view", "edit"])
            if success:
                print(f"✓ 成功注册用户: {test_username}")
            else:
                print(f"✗ 注册用户失败: {test_username}")
                return False
        except Exception as e:
            print(f"✗ 注册用户时发生异常: {test_username}, 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 验证用户是否可以成功认证
        user_info = authenticate_user(test_username, test_password)
        if user_info:
            print(f"✓ 用户 {test_username} 认证成功")
            print(f"  用户权限: {user_info['permissions']}")
        else:
            print(f"✗ 用户 {test_username} 认证失败")
            return False
        
        # 直接查询SQLite数据库验证数据存储
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 查询用户表
        cursor.execute("SELECT username, password_hash, is_active FROM users WHERE username = ?", (test_username,))
        user_row = cursor.fetchone()
        if user_row:
            print(f"✓ SQLite数据库中存在用户记录: {user_row[0]}")
            print(f"  密码哈希: {user_row[1]}")
            print(f"  账户状态: {'激活' if user_row[2] else '禁用'}")
        else:
            print(f"✗ SQLite数据库中未找到用户记录: {test_username}")
            conn.close()
            return False
        
        # 查询权限表
        cursor.execute("SELECT permission FROM user_permissions WHERE username = ?", (test_username,))
        permissions = [perm[0] for perm in cursor.fetchall()]
        if permissions:
            print(f"✓ 用户权限已正确存储: {permissions}")
        else:
            print(f"✗ 未找到用户权限记录: {test_username}")
            conn.close()
            return False
        
        conn.close()
        
        print("\n🎉 所有测试都已通过！用户注册功能工作正常")
        return True
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试数据
        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_permissions WHERE username = ?", ("testuser",))
            cursor.execute("DELETE FROM users WHERE username = ?", ("testuser",))
            conn.commit()
            conn.close()
            print("\n📋 测试数据已清理")
        except:
            pass


if __name__ == "__main__":
    test_register_functionality()
