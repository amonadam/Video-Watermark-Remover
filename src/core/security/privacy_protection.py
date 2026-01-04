"""
隐私保护模块
提供视频元数据移除和敏感信息保护功能
"""
import os
import json
import tempfile
from typing import Optional


def remove_video_metadata(input_path: str, output_path: str) -> bool:
    """
    移除视频文件中的元数据
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        
    Returns:
        是否成功移除元数据
    """
    try:
        # 使用ffmpeg移除元数据
        from .system_security import safe_execute_command
        
        command = [
            "ffmpeg",
            "-i", input_path,
            "-map_metadata", "-1",  # 移除所有元数据
            "-c", "copy",  # 直接复制音视频流，不重新编码
            output_path
        ]
        
        result = safe_execute_command(command, timeout=60)
        
        if result and result.returncode == 0:
            return True
        else:
            print(f"移除元数据失败: {result.stderr if result else '未知错误'}")
            return False
            
    except Exception as e:
        print(f"移除元数据出错: {e}")
        return False


def sanitize_video_filename(filename: str) -> str:
    """
    净化视频文件名，移除可能包含的敏感信息
    
    Args:
        filename: 原始文件名
        
    Returns:
        净化后的文件名
    """
    import re
    
    # 移除可能包含的日期、时间、个人信息等
    sanitized = re.sub(r'\d{4}-\d{2}-\d{2}', '', filename)
    sanitized = re.sub(r'\d{2}:\d{2}:\d{2}', '', sanitized)
    sanitized = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', '', sanitized)
    sanitized = re.sub(r'\b(?:\+?86)?1[3-9]\d{9}\b', '', sanitized)
    
    # 移除多余的特殊字符
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', sanitized)
    
    # 移除多余的下划线
    sanitized = re.sub(r'_+', '_', sanitized)
    
    return sanitized.strip('_')


def anonymize_user_data(data: dict) -> dict:
    """
    匿名化用户数据，替换或移除敏感信息
    
    Args:
        data: 包含用户数据的字典
        
    Returns:
        匿名化后的用户数据
    """
    if not isinstance(data, dict):
        return data
    
    anonymized = data.copy()
    
    # 需要匿名化的字段列表
    sensitive_fields = [
        "username", "user_id", "email", "phone", "address",
        "ip_address", "mac_address", "location", "device_id"
    ]
    
    for field in sensitive_fields:
        if field in anonymized:
            # 替换为哈希值或占位符
            anonymized[field] = f"{field}_anon_{hash(str(anonymized[field])) % 1000000}"
    
    return anonymized


def secure_video_storage(video_path: str, secure_dir: str) -> Optional[str]:
    """
    安全存储视频文件，包括权限设置和路径随机化
    
    Args:
        video_path: 原始视频路径
        secure_dir: 安全存储目录
        
    Returns:
        安全存储后的视频路径，如果失败返回None
    """
    try:
        import shutil
        import uuid
        
        # 确保安全目录存在
        os.makedirs(secure_dir, exist_ok=True)
        
        # 生成随机文件名
        _, ext = os.path.splitext(video_path)
        random_name = f"{uuid.uuid4()}{ext}"
        secure_path = os.path.join(secure_dir, random_name)
        
        # 复制文件
        shutil.copy2(video_path, secure_path)
        
        # 设置严格的文件权限（仅所有者可读写）
        if os.name == 'posix':
            os.chmod(secure_path, 0o600)
        
        return secure_path
        
    except Exception as e:
        print(f"安全存储视频失败: {e}")
        return None


def redact_sensitive_info(text: str) -> str:
    """
    编辑文本中的敏感信息（如手机号、邮箱等）
    
    Args:
        text: 原始文本
        
    Returns:
        编辑后的文本
    """
    import re
    
    # 简化正则表达式，使用更直接的匹配方式
    # 先匹配特殊格式（邮箱、IP），再匹配纯数字格式（身份证、手机号）
    
    # 邮箱地址 - 匹配包含@和.的邮箱格式
    text = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '***@***.***', text)
    
    # IP地址 - 匹配XXX.XXX.XXX.XXX格式
    text = re.sub(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', '***.***.***.***', text)
    
    # 身份证号码 - 18位数字或字母X/x
    text = re.sub(r'\d{17}[\dXx]', '**********', text)
    
    # 手机号码 - 11位数字，以1[3-9]开头
    text = re.sub(r'1[3-9]\d{9}', '***-****-****', text)
    
    return text


def generate_privacy_report(file_path: str) -> dict:
    """
    生成隐私报告，包含文件隐私相关信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        隐私报告字典
    """
    report = {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "has_metadata": True,  # 默认假设包含元数据
        "privacy_status": "pending",
        "sanitized_filename": sanitize_video_filename(os.path.basename(file_path))
    }
    
    try:
        # 检查文件是否包含元数据
        from .system_security import safe_execute_command
        
        command = ["ffprobe", "-v", "error", "-show_format", file_path]
        result = safe_execute_command(command, timeout=10)
        
        if result and result.returncode == 0:
            # 检查是否有元数据
            report["has_metadata"] = "metadata" in result.stdout.lower()
    except Exception:
        pass
    
    return report