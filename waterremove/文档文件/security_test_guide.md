# 视频去水印项目安全性验证指南

## 一、文件安全模块验证

### 1. 文件类型验证
**测试目标**：验证`validate_video_file`函数能正确识别视频文件
**测试步骤**：
```python
from src.core.security.file_security import validate_video_file

# 测试有效视频文件
print("测试有效视频文件:")
print("MP4文件:", validate_video_file("test_video.mp4"))
print("AVI文件:", validate_video_file("test_video.avi"))

# 测试无效文件
print("\n测试无效文件:")
print("文本文件:", validate_video_file("test.txt"))
print("EXE文件:", validate_video_file("test.exe"))
```



### 3. 临时文件管理
**测试目标**：验证`create_secure_temp_file`和`secure_delete_file`功能
**测试步骤**：
```python
from src.core.security.file_security import create_secure_temp_file, secure_delete_file
import os

# 创建临时文件
temp_path = create_secure_temp_file(b"test data", ".txt")
print(f"创建临时文件: {temp_path}")
print(f"文件存在: {os.path.exists(temp_path)}")

# 安全删除临时文件
secure_delete_file(temp_path)
print(f"删除后文件存在: {os.path.exists(temp_path)}")
```

## 二、系统安全模块验证

### 1. 命令注入防护
**测试目标**：验证`safe_execute_command`函数能防止命令注入
**测试步骤**：
```python
from src.core.security.system_security import safe_execute_command

# 测试正常命令
print("正常命令:")
safe_execute_command(["echo", "Hello World"])

# 测试命令注入
print("\n命令注入测试:")
try:
    # 尝试注入恶意命令
    safe_execute_command(["echo", "Hello"; "rm -rf /"])
    print("⚠️  注意：如果命令执行成功，说明存在命令注入风险")
except Exception as e:
    print("✅  成功拦截命令注入:", e)
```

### 2. 输入净化
**测试目标**：验证`sanitize_input`函数能净化用户输入
**测试步骤**：
```python
from src.core.security.system_security import sanitize_input

# 测试恶意输入
test_inputs = [
    "<script>alert('XSS')</script>",
    "../../../etc/passwd",
    "command; rm -rf /"
]

print("输入净化测试:")
for input_str in test_inputs:
    sanitized = sanitize_input(input_str)
    print(f"原始: {input_str}")
    print(f"净化后: {sanitized}")
    print("---")
```

## 三、配置安全模块验证

### 1. 配置加密存储
**测试目标**：验证配置文件是否被加密存储
**测试步骤**：
```python
from src.core.security.config_security import secure_save_config, secure_load_config, generate_config_secret
import json

# 生成密钥
secret_key = generate_config_secret()
print(f"生成的密钥: {secret_key}")

# 测试配置
config = {
    "sample_frames": 10,
    "use_gpu": True,
    "theme": "dark"
}

# 保存加密配置
secure_save_config(config, "test_config.json", secret_key)
print("\n配置文件内容（加密后）:")
with open("test_config.json", "rb") as f:
    print(f.read())

# 加载解密配置
loaded_config = secure_load_config("test_config.json", secret_key)
print("\n解密后的配置:", loaded_config)
print("配置是否一致:", config == loaded_config)
```

## 四、隐私保护模块验证

### 1. 元数据移除
**测试目标**：验证`remove_video_metadata`函数能移除视频元数据
**测试步骤**：
```python
from src.core.security.privacy_protection import remove_video_metadata
import os

# 需要准备一个包含元数据的视频文件
source_video = "test_with_metadata.mp4"
dest_video = "test_without_metadata.mp4"

if os.path.exists(source_video):
    print(f"移除元数据前文件大小: {os.path.getsize(source_video)} bytes")
    
    # 移除元数据
    success = remove_video_metadata(source_video, dest_video)
    print(f"移除元数据成功: {success}")
    
    if success and os.path.exists(dest_video):
        print(f"移除元数据后文件大小: {os.path.getsize(dest_video)} bytes")
        print("✅  元数据移除功能测试完成")
```

### 2. 文件名安全处理
**测试目标**：验证`sanitize_video_filename`函数能处理不安全的文件名
**测试步骤**：
```python
from src.core.security.privacy_protection import sanitize_video_filename

# 测试不安全的文件名
unsafe_filenames = [
    "../../../secret/video.mp4",
    "<script>malicious</script>.mp4",
    "video;rm -rf.mp4",
    "video"\".mp4"
]

print("文件名安全处理测试:")
for filename in unsafe_filenames:
    sanitized = sanitize_video_filename(filename)
    print(f"原始: {filename}")
    print(f"安全: {sanitized}")
    print("---")
```

## 五、访问控制模块验证

### 1. 用户认证测试
**测试目标**：验证`AccessController`类的用户认证功能
**测试步骤**：
```python
from src.core.security.access_control import AccessController, SQLiteUserStorage
import tempfile
import os

# 创建临时用户数据库
with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
    db_path = tmp.name

# 初始化访问控制器
controller = AccessController(SQLiteUserStorage(db_path))

# 添加测试用户
controller.storage.add_user("testuser", "password123", ["process_video"])
controller.storage.add_user("admin", "adminpass", ["admin"])

# 测试认证
print("用户认证测试:")
print("正确密码:", controller.authenticate("testuser", "password123"))
print("错误密码:", controller.authenticate("testuser", "wrongpass"))
print("不存在用户:", controller.authenticate("nonexist", "password"))

# 清理临时文件
os.unlink(db_path)
```

### 2. 权限管理测试
**测试目标**：验证权限检查功能
**测试步骤**：
```python
from src.core.security.access_control import AccessController, SQLiteUserStorage
import tempfile
import os

# 创建临时用户数据库
with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
    db_path = tmp.name

# 初始化访问控制器
controller = AccessController(SQLiteUserStorage(db_path))

# 添加测试用户
controller.storage.add_user("user1", "pass1", ["process_video"])
controller.storage.add_user("admin", "pass2", ["admin"])

# 测试权限检查
print("权限检查测试:")
print("普通用户有处理视频权限:", controller.check_permission("user1", "process_video"))
print("普通用户有管理权限:", controller.check_permission("user1", "admin"))
print("管理员有处理视频权限:", controller.check_permission("admin", "process_video"))
print("管理员有管理权限:", controller.check_permission("admin", "admin"))

# 清理临时文件
os.unlink(db_path)
```

## 六、核心业务逻辑安全验证



### 2. Utils模块安全功能
**测试目标**：验证`utils.py`中的安全功能是否正常工作
**测试步骤**：
```python
import os
import json
from src.core import utils

# 测试配置加载/保存（加密）
config_path = "test_utils_config.json"
config = {"test_key": "test_value"}

# 保存配置
utils.save_config(config_path, config)
print(f"配置文件已创建: {os.path.exists(config_path)}")

# 加载配置
loaded_config = utils.load_config(config_path)
print(f"配置加载成功: {loaded_config}")
print(f"配置一致: {config == loaded_config}")

# 测试文件哈希计算
if os.path.exists(config_path):
    hash_value = utils.calculate_file_hash(config_path)
    print(f"文件哈希值: {hash_value}")
```

## 六、整体应用安全测试

### 1. 应用启动测试
**测试目标**：验证应用能正常启动且安全功能不影响核心业务
**测试步骤**：
```bash
# 启动应用
python run.py
```

**预期结果**：
- 应用正常启动，无安全相关错误
- GUI界面正常显示
- 模型加载正常

### 2. 完整视频处理流程测试
**测试目标**：验证完整的视频去水印流程能正常工作
**测试步骤**：
1. 通过GUI选择一个视频文件
2. 选择水印区域
3. 执行去水印操作
4. 验证输出视频正常生成

**预期结果**：
- 视频处理完成，无错误
- 输出视频质量正常
- 水印被有效去除
- 没有安全相关异常

## 七、安全测试注意事项

1. **测试环境**：建议在隔离的测试环境中进行安全测试，避免影响生产环境
2. **测试数据**：使用测试数据，不要使用真实的用户数据或敏感文件
3. **权限控制**：确保测试用户只有必要的权限，避免测试过程中意外修改系统文件
4. **安全更新**：定期检查安全模块是否需要更新，以应对新的安全威胁
5. **日志记录**：关注应用的日志输出，及时发现潜在的安全问题

## 八、总结

通过上述测试，可以全面验证视频去水印项目的安全性。建议定期进行安全测试和审计，确保应用始终保持在安全状态。如果发现任何安全问题，请及时修复并更新安全模块。