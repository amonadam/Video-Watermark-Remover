"""
安全模块包
提供各种网络空间安全功能，包括文件安全、系统安全、隐私保护、配置安全和访问控制
"""

# 导出所有安全模块功能
from .file_security import (
    validate_video_file,
    create_secure_temp_file,
    secure_delete_file,
    calculate_file_hash
)



from .system_security import (
    safe_execute_command,
    sanitize_input,
    get_system_info,
    limit_resource_usage
)

from .privacy_protection import (
    remove_video_metadata,
    sanitize_video_filename,
    anonymize_user_data,
    secure_video_storage,
    redact_sensitive_info,
    generate_privacy_report
)

from .config_security import (
    secure_save_config,
    secure_load_config,
    validate_config,
    get_default_config,
    sanitize_config_value,
    generate_config_secret
)

from .access_control import (
    AccessController,
    authenticate_user,
    check_user_permission,
    initialize_access_control,
    add_new_user,
    update_user_permissions,
    deactivate_user
)

__all__ = [
    # file_security
    'validate_video_file',
    'create_secure_temp_file',
    'secure_delete_file',
    'calculate_file_hash',
    

    
    # system_security
    'safe_execute_command',
    'sanitize_input',
    'get_system_info',
    'limit_resource_usage',
    
    # privacy_protection
    'remove_video_metadata',
    'sanitize_video_filename',
    'anonymize_user_data',
    'secure_video_storage',
    'redact_sensitive_info',
    'generate_privacy_report',
    
    # config_security
    'secure_save_config',
    'secure_load_config',
    'validate_config',
    'get_default_config',
    'sanitize_config_value',
    'generate_config_secret',
    
    # access_control
    'AccessController',
    'authenticate_user',
    'check_user_permission',
    'initialize_access_control',
    'add_new_user',
    'update_user_permissions',
    'deactivate_user'
]
