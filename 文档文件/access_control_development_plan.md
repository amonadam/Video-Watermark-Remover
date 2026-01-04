# 访问控制模块开发计划

## 一、需求分析

根据项目文档和安全需求，需要在core和gui文件夹下实现访问控制模块功能，确保系统资源和功能的安全访问。

### 1. 功能需求
- **用户认证**：验证用户身份，确保只有合法用户可以访问系统
- **权限管理**：基于角色的权限控制，限制用户对特定功能的访问
- **安全日志**：记录用户登录、权限验证等安全相关操作
- **用户管理**：管理员可以添加、删除、修改用户和权限

### 2. 技术需求
- 与现有安全模块集成，使用现有的`access_control.py`实现
- 支持多种权限级别：view（查看）、edit（编辑）、delete（删除）、admin（管理）
- 界面上根据权限动态显示/隐藏功能

## 二、实现设计

### 1. Core模块访问控制实现

#### 1.1 核心功能模块集成
- **video_processor.py**：在视频处理前添加用户认证和权限检查
- **watermark_detector.py**：在水印检测前添加权限检查
- **lama_inpainter.py**：在图像修复前添加权限检查
- **utils.py**：添加访问控制相关的工具函数

#### 1.2 权限验证逻辑
```python
# 在core模块中添加权限检查装饰器
def require_permission(permission):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 从参数中获取当前用户信息
            current_user = kwargs.get('current_user')
            if not current_user:
                raise PermissionError("用户未登录")
            
            # 检查用户权限
            if not check_user_permission(current_user['username'], permission):
                raise PermissionError(f"用户缺少权限: {permission}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

#### 1.3 接口定义
```python
# 在video_processor.py中
def process(self, current_user=None):
    """处理视频，需要edit权限"""
    if not check_user_permission(current_user['username'], 'edit'):
        raise PermissionError("缺少编辑权限")
    # 现有处理逻辑

# 在watermark_detector.py中
def generate_mask(self, video_clip, auto_select_roi=True, current_user=None):
    """生成水印掩膜，需要edit权限"""
    if not check_user_permission(current_user['username'], 'edit'):
        raise PermissionError("缺少编辑权限")
    # 现有生成逻辑
```

### 2. GUI模块访问控制实现

#### 2.1 登录界面
- 创建一个登录对话框，用于用户输入用户名和密码
- 验证用户身份后，显示主界面

#### 2.2 主界面权限控制
- 在main_window.py中添加权限检查逻辑
- 根据用户权限显示/隐藏功能按钮
- 禁止无权限用户访问特定功能

#### 2.3 用户管理界面
- 添加用户管理界面，允许管理员添加、删除、修改用户和权限

## 三、实现步骤

### 1. Core模块实现（30%）
- **步骤1**：在utils.py中添加访问控制工具函数
- **步骤2**：在video_processor.py中添加权限检查
- **步骤3**：在watermark_detector.py中添加权限检查
- **步骤4**：在lama_inpainter.py中添加权限检查

### 2. GUI模块实现（50%）
- **步骤1**：创建登录对话框
- **步骤2**：修改main_window.py，添加权限控制
- **步骤3**：实现用户管理界面
- **步骤4**：根据用户权限动态显示/隐藏功能

### 3. 测试和调试（20%）
- **步骤1**：测试用户认证功能
- **步骤2**：测试权限控制功能
- **步骤3**：测试界面上的权限控制
- **步骤4**：修复发现的问题

## 四、技术实现细节

### 1. 用户权限级别
- **view**：查看系统功能，不能进行修改操作
- **edit**：可以编辑配置和处理视频
- **delete**：可以删除文件和数据
- **admin**：可以管理用户和系统设置

### 2. 安全考虑
- 密码使用SHA-256哈希存储
- 敏感操作记录安全日志
- 权限验证失败时抛出适当的异常

### 3. 界面交互
- 登录失败时显示错误信息
- 无权限访问功能时显示提示
- 管理员用户可以访问所有功能

## 五、预期成果

1. **Core模块**：所有核心功能都添加了访问控制
2. **GUI模块**：
   - 登录界面正常工作
   - 主界面根据权限动态显示功能
   - 用户管理界面可以管理用户和权限
3. **测试**：所有访问控制功能通过测试

## 六、风险分析

1. **兼容性风险**：与现有系统的兼容性问题
   - 缓解措施：逐步集成，确保不影响现有功能

2. **性能风险**：权限检查可能影响系统性能
   - 缓解措施：优化权限检查逻辑，减少不必要的检查

3. **用户体验风险**：过于严格的权限控制可能影响用户体验
   - 缓解措施：合理设计权限级别，确保用户可以正常使用核心功能

## 七、验收标准

1. 只有合法用户可以登录系统
2. 用户只能访问其权限范围内的功能
3. 管理员可以管理用户和权限
4. 权限验证失败时显示适当的错误信息
5. 不影响系统的核心功能和性能