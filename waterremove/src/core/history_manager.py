"""
历史记录管理模块
提供用户历史记录的添加、查询、删除等功能
"""
import sqlite3
import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .security.system_security import sanitize_input


class HistoryManager:
    """
    历史记录管理器类，负责用户历史记录的管理
    """
    
    def __init__(self, db_path: str = "users.db"):
        """
        初始化历史记录管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """
        确保数据库文件存在
        """
        if not os.path.exists(self.db_path):
            self.logger.error(f"数据库文件不存在: {self.db_path}")
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
    
    def add_history(self, username: str, video_path: str, operation_type: str, 
                    file_name: str, file_size: Optional[int] = None) -> bool:
        """
        添加历史记录
        
        Args:
            username: 用户名
            video_path: 视频路径
            operation_type: 操作类型 ('import' 或 'export')
            file_name: 文件名
            file_size: 文件大小（字节）
            
        Returns:
            是否添加成功
        """
        try:
            # 验证操作类型
            if operation_type not in ['import', 'export']:
                self.logger.error(f"无效的操作类型: {operation_type}")
                return False
            
            # 清理输入数据
            username = sanitize_input(username)
            video_path = sanitize_input(video_path, is_path=True)
            file_name = sanitize_input(file_name, is_path=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 使用参数化查询防止SQL注入
            cursor.execute('''
                INSERT INTO user_history (username, video_path, operation_type, file_name, file_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, video_path, operation_type, file_name, file_size))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"为用户 {username} 添加历史记录成功: {operation_type} {file_name}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"添加历史记录失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"添加历史记录时发生意外错误: {e}")
            return False
    
    def get_history(self, username: str, page: int = 1, page_size: int = 20, 
                    operation_type: Optional[str] = None, 
                    start_time: Optional[datetime] = None, 
                    end_time: Optional[datetime] = None) -> Tuple[List[Dict[str, any]], int]:
        """
        查询用户历史记录
        
        Args:
            username: 用户名
            page: 页码（从1开始）
            page_size: 每页记录数
            operation_type: 操作类型筛选（可选）
            start_time: 开始时间筛选（可选）
            end_time: 结束时间筛选（可选）
            
        Returns:
            历史记录列表和总记录数
        """
        try:
            # 清理输入数据
            username = sanitize_input(username)
            if operation_type:
                operation_type = sanitize_input(operation_type)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使用字典形式返回结果
            cursor = conn.cursor()
            
            # 构建查询条件
            where_clauses = ["username = ?"]
            params = [username]
            
            if operation_type:
                where_clauses.append("operation_type = ?")
                params.append(operation_type)
            
            if start_time:
                where_clauses.append("operation_time >= ?")
                params.append(start_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            if end_time:
                where_clauses.append("operation_time <= ?")
                params.append(end_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            # 构建WHERE子句
            where_sql = " AND ".join(where_clauses)
            
            # 查询总记录数
            total_sql = f"SELECT COUNT(*) FROM user_history WHERE {where_sql}"
            cursor.execute(total_sql, params)
            total_count = cursor.fetchone()[0]
            
            # 构建分页查询
            offset = (page - 1) * page_size
            query_sql = f"""
                SELECT id, username, video_path, operation_type, operation_time, file_name, file_size
                FROM user_history
                WHERE {where_sql}
                ORDER BY operation_time DESC
                LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            
            # 转换为字典列表
            history_list = []
            for row in rows:
                history_item = dict(row)
                # 转换时间格式
                history_item['operation_time'] = datetime.strptime(
                    history_item['operation_time'], "%Y-%m-%d %H:%M:%S"
                )
                history_list.append(history_item)
            
            conn.close()
            
            return history_list, total_count
            
        except sqlite3.Error as e:
            self.logger.error(f"查询历史记录失败: {e}")
            return [], 0
        except Exception as e:
            self.logger.error(f"查询历史记录时发生意外错误: {e}")
            return [], 0
    
    def delete_history(self, username: str, history_id: int) -> bool:
        """
        删除指定的历史记录
        
        Args:
            username: 用户名
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
        """
        try:
            # 清理输入数据
            username = sanitize_input(username)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 验证历史记录属于该用户
            cursor.execute('''
                SELECT COUNT(*) FROM user_history 
                WHERE id = ? AND username = ?
            ''', (history_id, username))
            
            if cursor.fetchone()[0] == 0:
                self.logger.error(f"用户 {username} 无权删除ID为 {history_id} 的历史记录")
                conn.close()
                return False
            
            # 删除历史记录
            cursor.execute('DELETE FROM user_history WHERE id = ?', (history_id,))
            conn.commit()
            conn.close()
            
            self.logger.info(f"用户 {username} 删除历史记录成功: ID {history_id}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"删除历史记录失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"删除历史记录时发生意外错误: {e}")
            return False
    
    def delete_all_history(self, username: str) -> bool:
        """
        删除用户的所有历史记录
        
        Args:
            username: 用户名
            
        Returns:
            是否删除成功
        """
        try:
            # 清理输入数据
            username = sanitize_input(username)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM user_history WHERE username = ?', (username,))
            conn.commit()
            conn.close()
            
            self.logger.info(f"用户 {username} 删除所有历史记录成功")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"删除所有历史记录失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"删除所有历史记录时发生意外错误: {e}")
            return False
    
    def get_history_by_id(self, username: str, history_id: int) -> Optional[Dict[str, any]]:
        """
        根据ID获取历史记录
        
        Args:
            username: 用户名
            history_id: 历史记录ID
            
        Returns:
            历史记录信息，如果不存在则返回None
        """
        try:
            # 清理输入数据
            username = sanitize_input(username)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, video_path, operation_type, operation_time, file_name, file_size
                FROM user_history
                WHERE id = ? AND username = ?
            ''', (history_id, username))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                history_item = dict(row)
                history_item['operation_time'] = datetime.strptime(
                    history_item['operation_time'], "%Y-%m-%d %H:%M:%S"
                )
                return history_item
            else:
                return None
                
        except sqlite3.Error as e:
            self.logger.error(f"获取历史记录失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取历史记录时发生意外错误: {e}")
            return None


# 全局历史记录管理器实例
_history_manager = None


def initialize_history_manager(db_path: str = "users.db") -> None:
    """
    初始化历史记录管理器
    
    Args:
        db_path: 数据库文件路径
    """
    global _history_manager
    _history_manager = HistoryManager(db_path)


def add_history_record(username: str, video_path: str, operation_type: str, 
                      file_name: str, file_size: Optional[int] = None) -> bool:
    """
    添加历史记录
    
    Args:
        username: 用户名
        video_path: 视频路径
        operation_type: 操作类型 ('import' 或 'export')
        file_name: 文件名
        file_size: 文件大小（字节）
        
    Returns:
        是否添加成功
    """
    if _history_manager is None:
        initialize_history_manager()
    
    return _history_manager.add_history(username, video_path, operation_type, file_name, file_size)


def get_history_records(username: str, page: int = 1, page_size: int = 20, 
                        operation_type: Optional[str] = None, 
                        start_time: Optional[datetime] = None, 
                        end_time: Optional[datetime] = None) -> Tuple[List[Dict[str, any]], int]:
    """
    查询历史记录
    
    Args:
        username: 用户名
        page: 页码（从1开始）
        page_size: 每页记录数
        operation_type: 操作类型筛选（可选）
        start_time: 开始时间筛选（可选）
        end_time: 结束时间筛选（可选）
        
    Returns:
        历史记录列表和总记录数
    """
    if _history_manager is None:
        initialize_history_manager()
    
    return _history_manager.get_history(username, page, page_size, operation_type, start_time, end_time)


def delete_history_record(username: str, history_id: int) -> bool:
    """
    删除指定的历史记录
    
    Args:
        username: 用户名
        history_id: 历史记录ID
        
    Returns:
        是否删除成功
    """
    if _history_manager is None:
        initialize_history_manager()
    
    return _history_manager.delete_history(username, history_id)


def delete_all_history_records(username: str) -> bool:
    """
    删除用户的所有历史记录
    
    Args:
        username: 用户名
        
    Returns:
        是否删除成功
    """
    if _history_manager is None:
        initialize_history_manager()
    
    return _history_manager.delete_all_history(username)


def get_history_record_by_id(username: str, history_id: int) -> Optional[Dict[str, any]]:
    """
    根据ID获取历史记录
    
    Args:
        username: 用户名
        history_id: 历史记录ID
        
    Returns:
        历史记录信息，如果不存在则返回None
    """
    if _history_manager is None:
        initialize_history_manager()
    
    return _history_manager.get_history_by_id(username, history_id)


__all__ = [
    'HistoryManager',
    'initialize_history_manager',
    'add_history_record',
    'get_history_records',
    'delete_history_record',
    'delete_all_history_records',
    'get_history_record_by_id'
]