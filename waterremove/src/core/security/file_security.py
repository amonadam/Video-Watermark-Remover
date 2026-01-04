"""
文件安全模块
提供文件验证、安全存储、安全删除等功能
"""

import os
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Union, Optional

ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
MAX_VIDEO_SIZE = 10 * 1024 * 1024 * 1024  # 10GB 最大视频文件大小

def validate_video_file(file_path: str) -> bool:
    """
    验证视频文件格式是否安全
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 如果是有效的视频文件返回True，否则返回False
    """
    try:
        # 检查文件扩展名（不要求文件实际存在，用于前端验证）
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
            return False
            
        # 如果文件存在，检查文件大小
        if os.path.exists(file_path):
            if os.path.getsize(file_path) > MAX_VIDEO_SIZE:
                return False
                
        return True
    except Exception:
        return False

def create_secure_temp_file(data: bytes, suffix: str = '', prefix: str = 'watermark_') -> str:
    """
    创建安全的临时文件
    
    Args:
        data: 要写入临时文件的数据
        suffix: 文件后缀
        prefix: 文件前缀
        
    Returns:
        str: 临时文件路径
    """
    try:
        # 创建临时文件，设置delete=False以便后续手动删除
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=suffix, 
            prefix=prefix,
            mode='wb'
        ) as f:
            f.write(data)
            temp_path = f.name
            
        # 设置文件权限（仅所有者可读写）
        os.chmod(temp_path, 0o600)
        
        return temp_path
    except Exception as e:
        raise IOError(f"创建临时文件失败: {str(e)}")

def secure_delete_file(file_path: str) -> bool:
    """
    安全删除文件（覆写后删除）
    
    Args:
        file_path: 要删除的文件路径
        
    Returns:
        bool: 删除成功返回True，否则返回False
    """
    try:
        if not os.path.exists(file_path):
            return True
            
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 覆写文件内容
        with open(file_path, 'wb') as f:
            # 用随机数据覆写三次
            for _ in range(3):
                f.seek(0)
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        
        # 删除文件
        os.unlink(file_path)
        
        return True
    except Exception:
        return False

def calculate_file_hash(file_path: str, hash_algorithm: str = 'sha256') -> str:
    """
    计算文件的哈希值
    
    Args:
        file_path: 文件路径
        hash_algorithm: 哈希算法，默认为'sha256'
        
    Returns:
        str: 文件的哈希值
    """
    try:
        hash_func = hashlib.new(hash_algorithm)
        
        with open(file_path, 'rb') as f:
            # 分块读取文件以处理大文件
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    except Exception as e:
        raise IOError(f"计算文件哈希值失败: {str(e)}")


