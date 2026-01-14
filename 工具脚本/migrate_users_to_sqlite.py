#!/usr/bin/env python3
"""
用户数据迁移脚本
将JSON格式的用户数据迁移到SQLite数据库
"""
import os
import sys
import json
import sqlite3
import hashlib
from typing import Dict, Any, Optional


def load_json_users(json_path: str) -> Dict[str, Dict[str, Any]]:
    """
    从JSON文件加载用户数据
    
    Args:
        json_path: JSON文件路径
        
    Returns:
        用户字典
    """
    if not os.path.exists(json_path):
        print(f"错误: JSON文件 {json_path} 不存在")
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        print(f"成功从 {json_path} 加载 {len(users)} 个用户")
        return users
    except json.JSONDecodeError as e:
        print(f"错误: JSON文件格式无效 - {e}")
        return {}
    except Exception as e:
        print(f"错误: 加载JSON文件失败 - {e}")
        return {}


def create_sqlite_tables(conn: sqlite3.Connection) -> None:
    """
    创建SQLite表结构
    
    Args:
        conn: SQLite数据库连接
    """
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    ''')
    
    # 创建权限表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_permissions (
            username TEXT NOT NULL,
            permission TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
            PRIMARY KEY (username, permission)
        )
    ''')
    
    conn.commit()
    print("成功创建SQLite表结构")


def migrate_users(users: Dict[str, Dict[str, Any]], conn: sqlite3.Connection) -> None:
    """
    将用户数据迁移到SQLite数据库
    
    Args:
        users: 用户字典
        conn: SQLite数据库连接
    """
    cursor = conn.cursor()
    
    # 开启事务
    conn.execute('BEGIN TRANSACTION')
    
    try:
        for username, user_info in users.items():
            # 插入用户数据
            password_hash = user_info.get('password_hash', '')
            is_active = 1 if user_info.get('is_active', True) else 0
            
            cursor.execute('''
                INSERT OR REPLACE INTO users (username, password_hash, is_active)
                VALUES (?, ?, ?)
            ''', (username, password_hash, is_active))
            
            # 插入权限数据
            permissions = user_info.get('permissions', [])
            for perm in permissions:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_permissions (username, permission)
                    VALUES (?, ?)
                ''', (username, perm))
            
            print(f"成功迁移用户: {username}")
        
        # 提交事务
        conn.commit()
        print(f"成功迁移 {len(users)} 个用户到SQLite数据库")
        
    except Exception as e:
        # 回滚事务
        conn.rollback()
        print(f"错误: 迁移用户失败 - {e}")
        raise


def verify_migration(users: Dict[str, Dict[str, Any]], conn: sqlite3.Connection) -> None:
    """
    验证迁移结果
    
    Args:
        users: 原始用户字典
        conn: SQLite数据库连接
    """
    cursor = conn.cursor()
    
    # 获取迁移后的用户数量
    cursor.execute('SELECT COUNT(*) FROM users')
    db_user_count = cursor.fetchone()[0]
    
    # 获取迁移后的权限数量
    cursor.execute('SELECT COUNT(*) FROM user_permissions')
    db_permission_count = cursor.fetchone()[0]
    
    expected_user_count = len(users)
    expected_permission_count = sum(len(user.get('permissions', [])) for user in users.values())
    
    print("\n迁移验证:")
    print(f"原始用户数: {expected_user_count}, 数据库用户数: {db_user_count}")
    print(f"原始权限数: {expected_permission_count}, 数据库权限数: {db_permission_count}")
    
    if expected_user_count == db_user_count and expected_permission_count == db_permission_count:
        print("✅ 迁移验证通过")
    else:
        print("❌ 迁移验证失败，数据不一致")


def main() -> None:
    """
    主函数
    """
    # 命令行参数处理
    import argparse
    
    parser = argparse.ArgumentParser(description='将JSON用户数据迁移到SQLite数据库')
    parser.add_argument('--input', '-i', default='users.json', help='JSON输入文件路径 (默认: users.json)')
    parser.add_argument('--output', '-o', default='users.db', help='SQLite输出文件路径 (默认: users.db)')
    parser.add_argument('--overwrite', '-w', action='store_true', help='覆盖已存在的SQLite数据库')
    
    args = parser.parse_args()
    
    # 检查输出文件是否存在
    if os.path.exists(args.output) and not args.overwrite:
        print(f"错误: SQLite文件 {args.output} 已存在，请使用 --overwrite 参数覆盖")
        sys.exit(1)
    
    # 加载JSON用户数据
    users = load_json_users(args.input)
    if not users:
        print("没有用户数据需要迁移")
        sys.exit(1)
    
    # 创建SQLite数据库连接
    try:
        conn = sqlite3.connect(args.output)
        
        # 创建表结构
        create_sqlite_tables(conn)
        
        # 迁移用户数据
        migrate_users(users, conn)
        
        # 验证迁移结果
        verify_migration(users, conn)
        
        # 显示迁移后的数据库信息
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(users)')
        users_schema = cursor.fetchall()
        
        cursor.execute('PRAGMA table_info(user_permissions)')
        permissions_schema = cursor.fetchall()
        
        print("\n数据库模式:")
        print("users表结构:")
        for col in users_schema:
            print(f"  {col[1]} ({col[2]})")
        
        print("\nuser_permissions表结构:")
        for col in permissions_schema:
            print(f"  {col[1]} ({col[2]})")
        
        print(f"\n迁移完成! 数据已保存到 {args.output}")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
