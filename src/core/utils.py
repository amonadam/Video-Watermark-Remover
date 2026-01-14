"""
工具函数模块
"""
import os
import json
import sys
import torch
import numpy as np
import cv2
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, Union
import warnings
from moviepy import VideoFileClip

# 导入安全模块功能
from .security import (
    validate_video_file as secure_validate_video_file,
    calculate_file_hash as secure_calculate_file_hash,
    get_system_info as secure_get_system_info,
    secure_load_config,
    secure_save_config,
    generate_config_secret,
    authenticate_user,
    check_user_permission,
    add_new_user
)

def ensure_directory_exists(directory: str) -> bool:
    """
    确保目录存在且有写入权限
    
    Args:
        directory: 目录路径
        
    Returns:
        True如果目录存在且可写，否则False
    """
    try:
        # 创建目录（如果不存在）
        os.makedirs(directory, exist_ok=True)
        
        # 测试写入权限
        test_file = os.path.join(directory, f".write_test_{os.getpid()}.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        return True
        
    except PermissionError:
        warnings.warn(f"没有写入权限: {directory}")
        return False
    except Exception as e:
        warnings.warn(f"创建目录时出错: {directory}, 错误: {e}")
        return False

def check_gpu() -> Tuple[bool, str, Optional[str]]:
    """
    检查GPU是否可用
    
    Returns:
        (是否有GPU, 设备名称, GPU名称)
    """
    if torch.cuda.is_available():
        device = "cuda"
        try:
            gpu_name = torch.cuda.get_device_name(0)
        except:
            gpu_name = "NVIDIA GPU"
        return True, device, gpu_name
    else:
        return False, "cpu", None

def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    获取视频信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频信息字典
    """
    info = {
        "filename": os.path.basename(video_path),
        "filepath": video_path,
        "filesize": "未知",
        "resolution": "未知",
        "duration": "未知",
        "total_frames": 0,
        "fps": "未知",
        "format": "未知",
        "valid": False
    }
    
    try:
        # 获取文件大小
        if os.path.exists(video_path):
            size_bytes = os.path.getsize(video_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    info["filesize"] = f"{size_bytes:.2f} {unit}"
                    break
                size_bytes /= 1024.0
        
        # 打开视频文件
        with VideoFileClip(video_path) as clip:
            info.update({
                "resolution": f"{int(clip.w)}x{int(clip.h)}",
                "duration": f"{clip.duration:.2f}秒",
                "total_frames": int(clip.duration * clip.fps),
                "fps": f"{clip.fps:.2f}",
                "valid": True
            })
        
        # 获取格式
        ext = os.path.splitext(video_path)[1].lower()
        if ext:
            info["format"] = ext[1:].upper()
            
    except Exception as e:
        warnings.warn(f"获取视频信息失败: {video_path}, 错误: {e}")
    
    return info

def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    default_config = {
        "sample_frames": 10,
        "min_frames": 7,
        "dilation_size": 5,
        "use_gpu": True,
        "ldm_steps": 50,
        "margin": 50,
        "hd_strategy": "ORIGINAL",
        "preview_before_process": True,
        "auto_select_roi": True,
        "use_color_segmentation": False,
        "min_component_area": 100,
        "morph_open": 3,
        "morph_close": 7,
        "use_canny": True,
        "canny_low": 100,
        "canny_high": 200,
        "codec": "libx264",
        "bitrate": "5000k",
        "preset": "medium",
        "output_format": "mp4",
        "last_input_dir": "",
        "last_output_dir": "output",
        "theme": "default",
        # 用户存储配置
        "user_storage": {
            "type": "sqlite",  # 可选值: "json" 或 "sqlite"
            "file_path": "users.db"  # 根据type决定是JSON文件路径还是SQLite数据库路径
        }
    }
    
    # 使用默认密钥（实际项目中应使用更安全的密钥管理方式）
    secret_key = "default_secret_key_123"
    
    # 使用安全模块中的配置加载功能
    config = secure_load_config(config_path, secret_key)
    
    # 如果配置文件不存在或加载失败，使用默认配置并保存
    if not config:
        config = default_config.copy()
        save_config(config_path, config)
    else:
        # 合并配置（用户配置覆盖默认配置）
        merged_config = default_config.copy()
        merged_config.update(config)
        config = merged_config
    
    return config

def save_config(config_path: str, config: Dict[str, Any]) -> bool:
    """
    保存配置文件
    
    Args:
        config_path: 配置文件路径
        config: 配置字典
        
    Returns:
        True如果成功，否则False
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 使用默认密钥（实际项目中应使用更安全的密钥管理方式）
        secret_key = "default_secret_key_123"
        
        # 使用安全模块中的配置保存功能
        return secure_save_config(config, config_path, secret_key)
        
    except Exception as e:
        warnings.warn(f"保存配置文件失败: {config_path}, 错误: {e}")
        return False

def format_time(seconds: float) -> str:
    """
    格式化时间（秒 -> 时:分:秒）
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的时间字符串
    """
    if seconds < 0:
        return "00:00:00"
    
    td = timedelta(seconds=int(seconds))
    
    # 提取时、分、秒
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if td.days > 0:
        hours += td.days * 24
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def validate_video_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    验证视频文件
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        (是否有效, 错误信息)
    """
    # 使用安全模块中的视频验证功能
    return secure_validate_video_file(file_path)

def get_supported_formats() -> list:
    """
    获取支持的视频格式列表
    
    Returns:
        支持的格式列表
    """
    return [
        "MP4 (*.mp4)",
        "AVI (*.avi)",
        "MOV (*.mov)",
        "MKV (*.mkv)",
        "FLV (*.flv)",
        "WMV (*.wmv)",
        "所有视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm)",
        "所有文件 (*.*)"
    ]

def estimate_processing_time(video_info: Dict[str, Any], 
                           has_gpu: bool = False) -> str:
    """
    估算处理时间
    
    Args:
        video_info: 视频信息
        has_gpu: 是否有GPU
        
    Returns:
        估算的时间字符串
    """
    if not video_info.get("valid", False):
        return "未知"
    
    try:
        total_frames = video_info.get("total_frames", 0)
        
        # 根据帧数和设备估算时间
        if has_gpu:
            # GPU: 大约0.1秒/帧
            seconds = total_frames * 0.1
        else:
            # CPU: 大约0.5秒/帧
            seconds = total_frames * 0.5
        
        return format_time(seconds)
        
    except:
        return "未知"

# 全局变量，用于存储当前登录用户
_current_user = None


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    获取当前登录用户
    
    Returns:
        当前用户信息，如果没有用户登录则返回默认用户
    """
    global _current_user
    # 如果没有用户登录，返回一个默认用户
    if not _current_user:
        return {
            'username': 'guest',
            'permissions': ['view', 'edit', 'delete']
        }
    return _current_user


def set_current_user(user_info: Optional[Dict[str, Any]]) -> None:
    """
    设置当前登录用户
    
    Args:
        user_info: 用户信息字典，包括username和permissions等
    """
    global _current_user
    _current_user = user_info


def register_user(username: str, password: str, permissions: list = ['view', 'edit', 'delete']) -> bool:
    """
    注册新用户
    
    Args:
        username: 用户名
        password: 密码
        permissions: 用户权限列表，默认为['view', 'edit', 'delete']
    
    Returns:
        如果注册成功返回True，否则返回False
    """
    try:
        # 调用安全模块的add_new_user函数注册用户
        return add_new_user(username, password, permissions)
    except Exception:
        return False


def require_permission(permission: str):
    """
    权限检查装饰器，用于限制函数调用需要特定权限
    
    Args:
        permission: 需要的权限
    
    Returns:
        装饰后的函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = kwargs.pop('current_user', get_current_user())
            if not current_user:
                raise PermissionError("用户未登录")
            
            # 检查用户权限
            # 直接检查当前用户对象的权限，避免需要用户存在于数据库中
            if 'admin' in current_user.get('permissions', []):
                return func(*args, **kwargs)
            if permission not in current_user.get('permissions', []):
                raise PermissionError(f"用户缺少权限: {permission}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def resize_image(image: np.ndarray, max_width: int = 800, max_height: int = 600) -> np.ndarray:
    """
    调整图像大小（保持宽高比）
    
    Args:
        image: 输入图像
        max_width: 最大宽度
        max_height: 最大高度
        
    Returns:
        调整后的图像
    """
    if image is None:
        return None
    
    h, w = image.shape[:2]
    
    # 计算缩放比例
    scale = min(max_width / w, max_height / h)
    
    # 如果图像已经小于最大尺寸，不缩放
    if scale >= 1:
        return image
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    return cv2.resize(image, (new_w, new_h))

def create_preview_mosaic(original: np.ndarray, processed: np.ndarray) -> np.ndarray:
    """
    创建对比预览图（原始vs处理后）
    
    Args:
        original: 原始图像
        processed: 处理后的图像
        
    Returns:
        并排对比图
    """
    if original is None or processed is None:
        return None
    
    # 调整到相同大小
    h1, w1 = original.shape[:2]
    h2, w2 = processed.shape[:2]
    
    target_h = min(h1, h2, 400)
    
    # 调整大小
    original_resized = resize_image(original, max_height=target_h)
    processed_resized = resize_image(processed, max_height=target_h)
    
    # 确保高度一致
    h = min(original_resized.shape[0], processed_resized.shape[0])
    original_resized = original_resized[:h, :]
    processed_resized = processed_resized[:h, :]
    
    # 创建并排图像
    mosaic = np.hstack([original_resized, processed_resized])
    
    # 添加标签
    try:
        # 使用PIL绘制中文文本
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # 转换为PIL图像
        pil_image = Image.fromarray(cv2.cvtColor(mosaic, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # 尝试加载中文字体
        font_path = "C:\\Windows\\Fonts\\simhei.ttf"
        try:
            font = ImageFont.truetype(font_path, 20)
        except IOError:
            # 如果字体文件不存在，使用默认字体
            font = ImageFont.load_default()
        
        # 绘制原始图像标签
        draw.text((10, 30), "原始", font=font, fill=(255, 255, 255), stroke_width=2)
        draw.text((10, 30), "原始", font=font, fill=(0, 0, 255), stroke_width=0)
        
        # 绘制处理后图像标签
        label_x = original_resized.shape[1] + 10
        draw.text((label_x, 30), "处理后", font=font, fill=(255, 255, 255), stroke_width=2)
        draw.text((label_x, 30), "处理后", font=font, fill=(0, 255, 0), stroke_width=0)
        
        # 转换回OpenCV图像
        mosaic = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except ImportError:
        # 如果PIL不可用，回退到OpenCV绘制英文标签
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        
        # 原始图像标签
        cv2.putText(mosaic, "Original", (10, 30), font, font_scale, 
                    (255, 255, 255), thickness + 1, cv2.LINE_AA)
        cv2.putText(mosaic, "Original", (10, 30), font, font_scale, 
                    (0, 0, 255), thickness, cv2.LINE_AA)
        
        # 处理后图像标签
        label_x = original_resized.shape[1] + 10
        cv2.putText(mosaic, "Processed", (label_x, 30), font, font_scale, 
                    (255, 255, 255), thickness + 1, cv2.LINE_AA)
        cv2.putText(mosaic, "Processed", (label_x, 30), font, font_scale, 
                    (0, 255, 0), thickness, cv2.LINE_AA)
    
    # 添加分隔线
    line_x = original_resized.shape[1]
    cv2.line(mosaic, (line_x, 0), (line_x, h), (255, 255, 255), 2)
    
    return mosaic

def get_system_info() -> Dict[str, Any]:
    """
    获取系统信息
    
    Returns:
        系统信息字典
    """
    # 使用安全模块中的系统信息获取功能
    return secure_get_system_info()

def calculate_file_hash(filepath: str, algorithm: str = "md5") -> Optional[str]:
    """
    计算文件哈希值
    
    Args:
        filepath: 文件路径
        algorithm: 哈希算法 ('md5', 'sha1', 'sha256')
        
    Returns:
        哈希值字符串
    """
    # 使用安全模块中的文件哈希计算功能
    return secure_calculate_file_hash(filepath, algorithm)

def validate_output_path(output_path: str, overwrite: bool = False) -> Tuple[bool, Optional[str]]:
    """
    验证输出路径
    
    Args:
        output_path: 输出路径
        overwrite: 是否允许覆盖
        
    Returns:
        (是否有效, 错误信息)
    """
    # 检查目录是否可写
    output_dir = os.path.dirname(output_path)
    if output_dir and not ensure_directory_exists(output_dir):
        return False, f"无法创建或写入目录: {output_dir}"
    
    # 检查文件是否已存在
    if os.path.exists(output_path) and not overwrite:
        return False, "文件已存在，请选择其他路径或启用覆盖选项"
    
    # 检查文件扩展名
    ext = os.path.splitext(output_path)[1].lower()
    if ext not in ['.mp4', '.avi', '.mov', '.mkv']:
        return False, f"不支持的输出格式: {ext}"
    
    return True, None