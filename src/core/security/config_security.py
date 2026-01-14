"""
配置安全模块
提供加密配置存储和安全的配置管理功能
"""
import os
import json
import base64
from typing import Dict, Optional, Any


def _simple_encrypt(data: str, key: str) -> str:
    """
    简单的加密函数（用于演示，实际项目应使用更安全的加密算法）
    
    Args:
        data: 要加密的数据
        key: 加密密钥
        
    Returns:
        加密后的数据
    """
    # 使用简单的异或加密（仅用于演示）
    encrypted = []
    key_length = len(key)
    
    for i, char in enumerate(data):
        key_char = key[i % key_length]
        encrypted_char = chr(ord(char) ^ ord(key_char))
        encrypted.append(encrypted_char)
    
    return base64.b64encode(''.join(encrypted).encode('utf-8')).decode('utf-8')


def _simple_decrypt(encrypted_data: str, key: str) -> str:
    """
    简单的解密函数（用于演示，实际项目应使用更安全的加密算法）
    
    Args:
        encrypted_data: 加密后的数据
        key: 解密密钥
        
    Returns:
        解密后的数据
    """
    # 使用简单的异或解密（仅用于演示）
    decoded = base64.b64decode(encrypted_data).decode('utf-8')
    decrypted = []
    key_length = len(key)
    
    for i, char in enumerate(decoded):
        key_char = key[i % key_length]
        decrypted_char = chr(ord(char) ^ ord(key_char))
        decrypted.append(decrypted_char)
    
    return ''.join(decrypted)


def secure_save_config(config: Dict[str, Any], 
                       config_path: str, 
                       secret_key: str, 
                       sensitive_keys: Optional[list] = None) -> bool:
    """
    安全保存配置文件，加密敏感字段
    
    Args:
        config: 配置字典
        config_path: 配置文件路径
        secret_key: 加密密钥
        sensitive_keys: 需要加密的敏感字段列表
        
    Returns:
        是否保存成功
    """
    if not isinstance(config, dict):
        return False
    
    if sensitive_keys is None:
        sensitive_keys = ["api_key", "password", "secret", "token", "database_url"]
    
    # 创建配置副本
    secure_config = config.copy()
    
    # 加密敏感字段
    for key in sensitive_keys:
        if key in secure_config and isinstance(secure_config[key], str):
            secure_config[key] = {
                "__encrypted__": True,
                "value": _simple_encrypt(secure_config[key], secret_key)
            }
    
    try:
        # 写入配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(secure_config, f, ensure_ascii=False, indent=2)
        
        # 设置严格的文件权限
        if os.name == 'posix':
            os.chmod(config_path, 0o600)
        
        return True
        
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


def secure_load_config(config_path: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """
    安全加载配置文件，解密敏感字段
    
    Args:
        config_path: 配置文件路径
        secret_key: 解密密钥
        
    Returns:
        配置字典，如果加载失败返回None
    """
    if not os.path.exists(config_path):
        return None
    
    try:
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 解密敏感字段
        for key, value in config.items():
            if isinstance(value, dict) and value.get("__encrypted__"):
                try:
                    config[key] = _simple_decrypt(value["value"], secret_key)
                except Exception:
                    # 解密失败，保留原始值
                    pass
        
        return config
        
    except Exception as e:
        print(f"加载配置失败: {e}")
        return None


def validate_config(config: Dict[str, Any], 
                   required_keys: Optional[list] = None, 
                   validations: Optional[dict] = None) -> bool:
    """
    验证配置的有效性和安全性
    
    Args:
        config: 配置字典
        required_keys: 必需的配置键列表
        validations: 各字段的验证规则
        
    Returns:
        配置是否有效
    """
    if not isinstance(config, dict):
        return False
    
    # 检查必需的配置键
    if required_keys:
        for key in required_keys:
            if key not in config:
                print(f"缺少必需的配置项: {key}")
                return False
    
    # 验证配置值
    if validations:
        for key, validation in validations.items():
            if key in config:
                value = config[key]
                
                # 类型验证
                if "type" in validation and not isinstance(value, validation["type"]):
                    print(f"配置项 {key} 类型错误，期望 {validation['type']}，实际 {type(value)}")
                    return False
                
                # 范围验证
                if "min" in validation and value < validation["min"]:
                    print(f"配置项 {key} 值太小，最小应为 {validation['min']}")
                    return False
                
                if "max" in validation and value > validation["max"]:
                    print(f"配置项 {key} 值太大，最大应为 {validation['max']}")
                    return False
                
                # 允许值验证
                if "allowed_values" in validation and value not in validation["allowed_values"]:
                    print(f"配置项 {key} 值无效，允许值为 {validation['allowed_values']}")
                    return False
    
    return True


def get_default_config() -> Dict[str, Any]:
    """
    获取默认配置（不包含敏感信息）
    
    Returns:
        默认配置字典
    """
    return {
        "video": {
            "max_size": 10 * 1024 * 1024 * 1024,  # 10GB
            "allowed_formats": ["mp4", "avi", "mov", "mkv", "flv", "wmv"],
            "temp_dir": "temp"
        },
        "model": {
            "path": "models/big-lama.pt",
            "use_gpu": True,
            "batch_size": 1
        },
        "security": {
            "enable_file_validation": True,
            "enable_metadata_removal": True
        },
        "ui": {
            "language": "zh",
            "theme": "light"
        }
    }


def sanitize_config_value(value: Any) -> Any:
    """
    净化配置值，防止注入攻击
    
    Args:
        value: 配置值
        
    Returns:
        净化后的配置值
    """
    if isinstance(value, str):
        # 移除潜在的危险字符
        import re
        return re.sub(r'[;&|`\\<>\$\(\)\*\?\[\]\{\}]', '', value)
    
    elif isinstance(value, dict):
        # 递归净化字典
        return {k: sanitize_config_value(v) for k, v in value.items()}
    
    elif isinstance(value, list):
        # 递归净化列表
        return [sanitize_config_value(item) for item in value]
    
    return value


def generate_config_secret() -> str:
    """
    生成配置加密密钥
    
    Returns:
        加密密钥
    """
    import uuid
    return str(uuid.uuid4()).replace('-', '')[:16]