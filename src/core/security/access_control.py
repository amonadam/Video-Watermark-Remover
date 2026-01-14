"""
访问控制模块
提供用户认证和权限管理功能
"""
import hashlib
import json
import os
import sqlite3
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Union


class UserStorageInterface(ABC):
    """
    用户存储接口，定义用户数据的存取操作
    """
    
    @abstractmethod
    def load_users(self) -> Dict[str, Dict[str, any]]:
        """
        加载所有用户数据
        
        Returns:
            用户字典，键为用户名，值为用户信息
        """
        pass
    
    @abstractmethod
    def save_users(self, users: Dict[str, Dict[str, any]]) -> bool:
        """
        保存所有用户数据
        
        Args:
            users: 用户字典
            
        Returns:
            是否保存成功
        """
        pass


class JsonUserStorage(UserStorageInterface):
    """
    JSON文件用户存储实现
    """
    
    def __init__(self, file_path: str = "users.json"):
        """
        初始化JSON用户存储
        
        Args:
            file_path: JSON文件路径
        """
        self.file_path = file_path
    
    def load_users(self) -> Dict[str, Dict[str, any]]:
        """
        从JSON文件加载用户数据
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # 返回默认用户
        return {
            "admin": {
                "password_hash": hashlib.sha256("admin123".encode('utf-8')).hexdigest(),
                "permissions": ["view", "edit", "delete", "admin"],
                "is_active": True
            },
            "user": {
                "password_hash": hashlib.sha256("user123".encode('utf-8')).hexdigest(),
                "permissions": ["view", "edit"],
                "is_active": True
            }
        }
    
    def save_users(self, users: Dict[str, Dict[str, any]]) -> bool:
        """
        将用户数据保存到JSON文件
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            # 设置严格的文件权限
            if os.name == 'posix':
                os.chmod(self.file_path, 0o600)
            
            return True
        except Exception:
            return False


class SQLiteUserStorage(UserStorageInterface):
    """
    SQLite数据库用户存储实现
    """
    
    def __init__(self, db_path: str = "users.db"):
        """
        初始化SQLite用户存储
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """
        初始化数据库表
        """
        conn = sqlite3.connect(self.db_path)
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
        
        # 创建操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                operation_time TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                operation_type TEXT NOT NULL,
                operation_result TEXT NOT NULL,
                ip_address TEXT,
                details TEXT
            )
        ''')
        
        # 添加默认用户
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, is_active)
            VALUES (?, ?, ?)
        ''', ("admin", hashlib.sha256("admin123".encode('utf-8')).hexdigest(), 1))
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, is_active)
            VALUES (?, ?, ?)
        ''', ("user", hashlib.sha256("user123".encode('utf-8')).hexdigest(), 1))
        
        # 添加默认权限
        admin_permissions = ["view", "edit", "delete", "admin"]
        user_permissions = ["view", "edit", "delete"]
        
        for perm in admin_permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO user_permissions (username, permission)
                VALUES (?, ?)
            ''', ("admin", perm))
        
        for perm in user_permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO user_permissions (username, permission)
                VALUES (?, ?)
            ''', ("user", perm))
        
        conn.commit()
        conn.close()
    
    def load_users(self) -> Dict[str, Dict[str, any]]:
        """
        从SQLite数据库加载用户数据
        """
        users = {}
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有用户
        cursor.execute('SELECT username, password_hash, is_active FROM users')
        rows = cursor.fetchall()
        
        for row in rows:
            username, password_hash, is_active = row
            
            # 获取用户权限
            cursor.execute('''
                SELECT permission FROM user_permissions WHERE username = ?
            ''', (username,))
            permissions = [perm[0] for perm in cursor.fetchall()]
            
            users[username] = {
                "password_hash": password_hash,
                "permissions": permissions,
                "is_active": bool(is_active)
            }
        
        conn.close()
        return users
    
    def save_users(self, users: Dict[str, Dict[str, any]]) -> bool:
        """
        将用户数据保存到SQLite数据库
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 开启事务
            conn.execute('BEGIN TRANSACTION')
            
            # 清空现有数据
            cursor.execute('DELETE FROM user_permissions')
            cursor.execute('DELETE FROM users')
            
            # 插入用户数据
            for username, user_info in users.items():
                cursor.execute('''
                    INSERT INTO users (username, password_hash, is_active)
                    VALUES (?, ?, ?)
                ''', (username, user_info["password_hash"], user_info["is_active"]))
                
                # 插入权限数据
                for perm in user_info["permissions"]:
                    cursor.execute('''
                        INSERT INTO user_permissions (username, permission)
                        VALUES (?, ?)
                    ''', (username, perm))
            
            # 提交事务
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            # 回滚事务
            if conn:
                conn.rollback()
                conn.close()
            return False


class AccessController:
    """
    访问控制器类，管理用户认证和权限
    """
    def __init__(self, storage: Optional[UserStorageInterface] = None, 
                 user_db_path: str = "users.db"):
        """
        初始化访问控制器
        
        Args:
            storage: 用户存储适配器实例，默认为None（使用SQLite数据库存储）
            user_db_path: 用户数据库文件路径，当使用默认存储时有效
        """
        # 如果没有提供存储适配器，使用SQLite数据库存储
        if storage is None:
            self.storage = SQLiteUserStorage(user_db_path)
        else:
            self.storage = storage
        
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, Dict[str, any]]:
        """
        加载用户数据库
        
        Returns:
            用户字典
        """
        return self.storage.load_users()
    
    def _save_users(self) -> bool:
        """
        保存用户数据库
        
        Returns:
            是否保存成功
        """
        return self.storage.save_users(self.users)
    
    def _hash_password(self, password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 原始密码
            
        Returns:
            哈希后的密码
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def add_user(self, username: str, password: str, permissions: List[str]) -> bool:
        """
        添加新用户
        
        Args:
            username: 用户名
            password: 密码
            permissions: 权限列表
            
        Returns:
            是否添加成功
        """
        if username in self.users:
            return False
        
        self.users[username] = {
            "password_hash": self._hash_password(password),
            "permissions": permissions,
            "is_active": True
        }
        
        return self._save_users()
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, any]]:
        """
        认证用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户信息，如果认证失败返回None
        """
        if username not in self.users or not self.users[username]["is_active"]:
            return None
        
        user = self.users[username]
        if user["password_hash"] == self._hash_password(password):
            return {
                "username": username,
                "permissions": user["permissions"]
            }
        
        return None
    
    def check_permission(self, username: str, permission: str) -> bool:
        """
        检查用户权限
        
        Args:
            username: 用户名
            permission: 要检查的权限
            
        Returns:
            是否有该权限
        """
        if username not in self.users or not self.users[username]["is_active"]:
            return False
        
        user = self.users[username]
        
        # "admin"权限拥有所有权限
        if "admin" in user["permissions"]:
            return True
        
        return permission in user["permissions"]
    
    def update_user_permissions(self, username: str, permissions: List[str]) -> bool:
        """
        更新用户权限
        
        Args:
            username: 用户名
            permissions: 新的权限列表
            
        Returns:
            是否更新成功
        """
        if username not in self.users:
            return False
        
        self.users[username]["permissions"] = permissions
        return self._save_users()
    
    def deactivate_user(self, username: str) -> bool:
        """
        停用用户
        
        Args:
            username: 用户名
            
        Returns:
            是否停用成功
        """
        if username not in self.users:
            return False
        
        self.users[username]["is_active"] = False
        return self._save_users()


# 全局访问控制器实例
_access_controller = None


def initialize_access_control(user_db_path: str = "users.db", storage_type: str = "sqlite") -> None:
    """
    初始化访问控制模块
    
    Args:
        user_db_path: 用户数据库文件路径
        storage_type: 存储类型，可选值: "json" 或 "sqlite"（默认使用sqlite）
    """
    global _access_controller
    
    # 根据存储类型创建对应的存储适配器
    if storage_type == "sqlite":
        storage = SQLiteUserStorage(user_db_path)
    else:  # 默认使用json
        storage = JsonUserStorage(user_db_path)
    
    _access_controller = AccessController(storage)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, any]]:
    """
    认证用户
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        用户信息，如果认证失败返回None
    """
    if _access_controller is None:
        initialize_access_control()
    
    return _access_controller.authenticate(username, password)


def check_user_permission(username: str, permission: str) -> bool:
    """
    检查用户权限
    
    Args:
        username: 用户名
        permission: 要检查的权限
        
    Returns:
        是否有该权限
    """
    if _access_controller is None:
        initialize_access_control()
    
    return _access_controller.check_permission(username, permission)


def add_new_user(username: str, password: str, permissions: List[str]) -> bool:
    """
    添加新用户
    
    Args:
        username: 用户名
        password: 密码
        permissions: 权限列表
        
    Returns:
        是否添加成功
    """
    if _access_controller is None:
        initialize_access_control()
    
    return _access_controller.add_user(username, password, permissions)


def update_user_permissions(username: str, permissions: List[str]) -> bool:
    """
    更新用户权限
    
    Args:
        username: 用户名
        permissions: 新的权限列表
        
    Returns:
        是否更新成功
    """
    if _access_controller is None:
        initialize_access_control()
    
    return _access_controller.update_user_permissions(username, permissions)


def deactivate_user(username: str) -> bool:
    """
    停用用户
    
    Args:
        username: 用户名
        
    Returns:
        是否停用成功
    """
    if _access_controller is None:
        initialize_access_control()
    
    return _access_controller.deactivate_user(username)
