#!/usr/bin/env python3
"""
更新数据库中所有用户的权限脚本
为所有用户添加edit和delete权限
"""
import sqlite3


def update_all_users_permissions(db_path: str = "users.db") -> None:
    """
    更新数据库中所有用户的权限
    
    Args:
        db_path: SQLite数据库文件路径
    """
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取所有用户
        cursor.execute('SELECT username FROM users')
        users = [row[0] for row in cursor.fetchall()]
        
        print(f"找到 {len(users)} 个用户")
        
        # 为每个用户添加edit和delete权限
        for username in users:
            print(f"处理用户: {username}")
            
            # 获取现有权限
            cursor.execute('''
                SELECT permission FROM user_permissions WHERE username = ?
            ''', (username,))
            existing_permissions = [row[0] for row in cursor.fetchall()]
            
            print(f"  现有权限: {existing_permissions}")
            
            # 需要添加的权限
            permissions_to_add = []
            if 'edit' not in existing_permissions:
                permissions_to_add.append('edit')
            if 'delete' not in existing_permissions:
                permissions_to_add.append('delete')
            
            if permissions_to_add:
                # 插入新权限
                for perm in permissions_to_add:
                    cursor.execute('''
                        INSERT OR IGNORE INTO user_permissions (username, permission)
                        VALUES (?, ?)
                    ''', (username, perm))
                
                print(f"  添加了权限: {permissions_to_add}")
            else:
                print("  已拥有所需权限，无需更改")
        
        # 提交事务
        conn.commit()
        print("\n✅ 权限更新完成")
        
        # 显示更新后的权限情况
        print("\n更新后的用户权限情况:")
        for username in users:
            cursor.execute('''
                SELECT permission FROM user_permissions WHERE username = ? ORDER BY permission
            ''', (username,))
            permissions = [row[0] for row in cursor.fetchall()]
            print(f"  {username}: {permissions}")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ 更新权限失败: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    update_all_users_permissions()
