"""操作日志记录模块
提供操作日志的记录和查询功能
"""
import sqlite3
import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .security.system_security import sanitize_input
from .utils import get_current_user


class OperationLogger:
    """
    操作日志记录器类，负责记录和查询用户操作日志
    """
    
    def __init__(self, db_path: str = "users.db"):
        """
        初始化操作日志记录器
        
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
    
    def log_operation(self, username: str, operation_type: str, 
                      operation_result: str, ip_address: Optional[str] = None,
                      details: Optional[str] = None) -> bool:
        """
        记录用户操作日志
        
        Args:
            username: 用户名
            operation_type: 操作类型
            operation_result: 操作结果
            ip_address: IP地址（可选）
            details: 详细信息（可选）
            
        Returns:
            是否记录成功
        """
        try:
            # 清理输入数据，允许下划线字符
            username = sanitize_input(username, allow_chars="_")
            operation_type = sanitize_input(operation_type, allow_chars="_")
            operation_result = sanitize_input(operation_result, allow_chars="_")
            if ip_address:
                ip_address = sanitize_input(ip_address, allow_chars="._")
            if details:
                details = sanitize_input(details, allow_chars="_ ")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 使用参数化查询防止SQL注入
            cursor.execute('''
                INSERT INTO operation_logs (username, operation_type, operation_result, ip_address, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, operation_type, operation_result, ip_address, details))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"记录操作日志成功: {username} {operation_type} {operation_result}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"记录操作日志失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"记录操作日志时发生意外错误: {e}")
            return False
    
    def get_operation_logs(self, username: Optional[str] = None, 
                          start_time: Optional[datetime] = None, 
                          end_time: Optional[datetime] = None,
                          operation_type: Optional[str] = None,
                          page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, any]], int]:
        """
        查询操作日志
        
        Args:
            username: 用户名（可选，None表示所有用户）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            operation_type: 操作类型（可选）
            page: 页码（从1开始）
            page_size: 每页记录数
            
        Returns:
            操作日志列表和总记录数
        """
        try:
            # 获取当前登录用户
            current_user = get_current_user()
            is_admin = 'admin' in current_user.get('permissions', [])
            
            # 清理输入数据
            if username and not is_admin:
                username = sanitize_input(username)
            if operation_type:
                operation_type = sanitize_input(operation_type)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使用字典形式返回结果
            cursor = conn.cursor()
            
            # 构建查询条件
            where_clauses = []
            params = []
            
            # 管理员可以查看所有用户的日志，也可以指定查看特定用户的日志
            # 普通用户只能查看自己的日志
            if not is_admin:
                # 非管理员用户只能查看自己的日志，忽略传入的username参数
                current_username = current_user.get('username')
                where_clauses.append("username = ?")
                params.append(current_username)
            elif username:
                # 管理员用户可以指定查看特定用户的日志
                where_clauses.append("username = ?")
                params.append(username)
            
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
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # 查询总记录数
            total_sql = f"SELECT COUNT(*) FROM operation_logs WHERE {where_sql}"
            cursor.execute(total_sql, params)
            total_count = cursor.fetchone()[0]
            
            # 构建分页查询
            offset = (page - 1) * page_size
            query_sql = f"""
                SELECT id, username, operation_time, operation_type, operation_result, ip_address, details
                FROM operation_logs
                WHERE {where_sql}
                ORDER BY operation_time DESC
                LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            
            cursor.execute(query_sql, params)
            rows = cursor.fetchall()
            
            # 转换为字典列表
            logs_list = []
            for row in rows:
                log_item = dict(row)
                # 转换时间格式
                log_item['operation_time'] = datetime.strptime(
                    log_item['operation_time'], "%Y-%m-%d %H:%M:%S"
                )
                logs_list.append(log_item)
            
            conn.close()
            
            return logs_list, total_count
            
        except sqlite3.Error as e:
            self.logger.error(f"查询操作日志失败: {e}")
            return [], 0
        except Exception as e:
            self.logger.error(f"查询操作日志时发生意外错误: {e}")
            return [], 0


# 创建全局实例
_operation_logger = None


def initialize_operation_logger(db_path: str = "users.db") -> None:
    """
    初始化操作日志记录器
    
    Args:
        db_path: 数据库文件路径
    """
    global _operation_logger
    if _operation_logger is None:
        _operation_logger = OperationLogger(db_path)


def log_operation(username: str, operation_type: str, operation_result: str,
                  ip_address: Optional[str] = None, details: Optional[str] = None) -> bool:
    """
    记录操作日志的便捷函数
    
    Args:
        username: 用户名
        operation_type: 操作类型
        operation_result: 操作结果
        ip_address: IP地址（可选）
        details: 详细信息（可选）
    
    Returns:
        是否记录成功
    """
    global _operation_logger
    if _operation_logger is None:
        initialize_operation_logger()
    
    return _operation_logger.log_operation(username, operation_type, operation_result, ip_address, details)


def get_operation_logs(username: Optional[str] = None, 
                       start_time: Optional[datetime] = None, 
                       end_time: Optional[datetime] = None,
                       operation_type: Optional[str] = None,
                       page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, any]], int]:
    """
    查询操作日志的便捷函数
    
    Args:
        username: 用户名（可选，None表示所有用户）
        start_time: 开始时间（可选）
        end_time: 结束时间（可选）
        operation_type: 操作类型（可选）
        page: 页码（从1开始）
        page_size: 每页记录数
    
    Returns:
        操作日志列表和总记录数
    """
    global _operation_logger
    if _operation_logger is None:
        initialize_operation_logger()
    
    return _operation_logger.get_operation_logs(username, start_time, end_time, operation_type, page, page_size)
