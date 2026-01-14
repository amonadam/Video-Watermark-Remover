#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查admin用户是否已存在
"""

import sqlite3

def check_admin_user():
    """
    检查数据库中是否已有admin用户
    """
    try:
        # 连接到SQLite数据库
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 查询admin用户
        cursor.execute("SELECT username, is_active FROM users WHERE username = ?", ("admin",))
        user_row = cursor.fetchone()
        
        if user_row:
            print(f"✓ 数据库中已存在admin用户: {user_row[0]}")
            print(f"  账户状态: {'激活' if user_row[1] else '禁用'}")
            
            # 查询权限
            cursor.execute("SELECT permission FROM user_permissions WHERE username = ?", ("admin",))
            permissions = [perm[0] for perm in cursor.fetchall()]
            print(f"  用户权限: {permissions}")
        else:
            print(f"✗ 数据库中不存在admin用户")
            
        # 查询所有用户
        cursor.execute("SELECT username, is_active FROM users")
        all_users = cursor.fetchall()
        if all_users:
            print(f"\n📋 数据库中所有用户:")
            for user in all_users:
                print(f"  - {user[0]} (状态: {'激活' if user[1] else '禁用'})")
                
        conn.close()
        return user_row is not None
        
    except Exception as e:
        print(f"✗ 检查用户时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_admin_user()
