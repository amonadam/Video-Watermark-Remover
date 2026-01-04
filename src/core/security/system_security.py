"""
系统安全模块
提供命令注入防护和安全的系统操作功能
"""
import subprocess
import re
from typing import List, Optional, Tuple


def safe_execute_command(command: List[str], 
                         capture_output: bool = True,
                         timeout: Optional[int] = None) -> Optional[subprocess.CompletedProcess]:
    """
    安全执行外部命令，防止命令注入
    
    Args:
        command: 命令列表，如 ["ffmpeg", "-i", "input.mp4", "output.mp4"]
        capture_output: 是否捕获输出
        timeout: 超时时间（秒）
        
    Returns:
        命令执行结果，如果执行失败返回None
        
    Raises:
        ValueError: 命令格式错误
        subprocess.TimeoutExpired: 命令执行超时
    """
    if not isinstance(command, list) or len(command) == 0:
        raise ValueError("命令必须是非空列表格式")
    
    # 验证命令是否安全
    if not _is_safe_command(command):
        raise ValueError("命令包含不安全的内容")
    
    try:
        return subprocess.run(
            command,
            shell=False,  # 关键：禁用shell模式防止命令注入
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=False
        )
    except subprocess.TimeoutExpired:
        raise
    except Exception as e:
        print(f"命令执行错误: {e}")
        return None


def _is_safe_command(command: List[str]) -> bool:
    """
    验证命令是否安全，防止命令注入
    
    Args:
        command: 命令列表
        
    Returns:
        命令是否安全
    """
    if not command:
        return False
    
    # 检查命令是否包含危险字符（主要针对命令注入的特殊字符）
    dangerous_patterns = [
        r'[;&|`]',  # 命令分隔符
        r'\$\(',  # 命令替换
    ]
    
    for arg in command:
        if not isinstance(arg, str):
            return False
        
        # 检查每个参数是否包含危险字符
        for pattern in dangerous_patterns:
            if re.search(pattern, arg):
                return False
    
    return True


def sanitize_input(input_str: str, allow_chars: str = "", is_path: bool = False) -> str:
    """
    净化输入字符串，移除潜在的危险字符
    
    Args:
        input_str: 输入字符串
        allow_chars: 允许的特殊字符
        is_path: 是否为文件路径，如果是则允许路径相关的字符
        
    Returns:
        净化后的字符串
    """
    if not isinstance(input_str, str):
        return str(input_str)
    
    # 基础允许的字符集：字母、数字、中文和一些常用符号
    base_chars = "a-zA-Z0-9\u4e00-\u9fa5"
    
    # 如果是文件路径，添加路径相关的字符
    if is_path:
        # 连字符放在字符类开头，避免被当作范围定义
        path_chars = "-\\/:._ "
        allowed_chars = f"{base_chars}{path_chars}{re.escape(allow_chars)}"
    else:
        allowed_chars = f"{base_chars}{re.escape(allow_chars)}"
    
    # 移除危险字符，但保留必要的字符
    dangerous_patterns = [
        r'[;&|`$()<>{}\[\]\'\"\\*?!]',  # SQL注入和命令注入的危险字符
    ]
    
    # 先移除危险字符
    sanitized = input_str
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized)
    
    # 再确保只保留允许的字符
    sanitized = re.sub(f"[^{allowed_chars}]", "", sanitized)
    
    return sanitized





def get_system_info() -> dict:
    """
    获取系统信息，用于安全审计
    
    Returns:
        系统信息字典
    """
    import platform
    import sys
    
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python_version": sys.version,
        "python_executable": sys.executable
    }


def limit_resource_usage(max_memory: Optional[int] = None, max_cpu: Optional[float] = None) -> bool:
    """
    限制进程资源使用
    
    Args:
        max_memory: 最大内存使用量（MB）
        max_cpu: 最大CPU使用率（0.0-1.0）
        
    Returns:
        是否设置成功
    """
    try:
        if max_memory:
            import resource
            resource.setrlimit(
                resource.RLIMIT_AS,
                (max_memory * 1024 * 1024, resource.RLIM_INFINITY)
            )
        
        if max_cpu:
            import os
            os.nice(10)  # 降低进程优先级
        
        return True
    except Exception as e:
        print(f"设置资源限制失败: {e}")
        return False