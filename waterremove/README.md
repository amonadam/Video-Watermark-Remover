# 视频去水印软件

## 1. 项目概述

视频去水印软件是一款基于人工智能技术的视频处理工具，专注于自动检测和去除视频中的水印内容。该软件采用先进的图像分析算法和深度学习模型，能够高效、精准地处理各类视频水印，同时保持视频原有质量。

### 核心功能

- 自动检测视频中的水印区域
- 基于AI模型的高质量水印去除
- 支持GPU加速，提升处理效率
- 友好的图形用户界面，操作简便
- 支持多种视频格式
- 提供处理前预览功能
- 历史记录管理

### 应用场景

- 视频编辑与制作
- 多媒体内容二次创作
- 教育视频处理
- 个人视频整理

## 2. 项目架构

### 系统架构图

```
视频去水印软件
├── 应用层（GUI界面）
│   ├── 登录模块
│   ├── 主界面模块
│   ├── 预览模块
│   └── 进度监控模块
├── 业务逻辑层
│   ├── 视频处理模块
│   ├── 水印检测模块
│   ├── 图像修复模块
│   └── 历史记录模块
├── 数据层
│   ├── 配置管理
│   ├── 用户数据存储
│   └── 历史记录存储
└── 技术支持层
    ├── 环境配置
    ├── 依赖管理
    └── 安全控制
```

### 核心模块说明

#### 2.1 应用层

- **登录模块**：负责用户身份验证和权限管理
- **主界面模块**：提供视频文件选择、参数设置、处理控制等功能
- **预览模块**：处理前预览水印检测结果
- **进度监控模块**：实时显示视频处理进度

#### 2.2 业务逻辑层

- **视频处理模块**：负责视频的加载、帧提取、处理和合成
- **水印检测模块**：自动识别视频中的水印区域
- **图像修复模块**：使用Lama模型修复水印区域
- **历史记录模块**：记录用户的处理历史

#### 2.3 数据层

- **配置管理**：管理软件的各项配置参数
- **用户数据存储**：存储用户信息和权限数据
- **历史记录存储**：存储视频处理历史

### 技术栈

| 技术/框架    | 版本      | 用途         |
| ------------ | --------- | ------------ |
| Python       | 3.9+      | 开发语言     |
| PyQt5        | 5.15.11   | GUI开发      |
| MoviePy      | 2.1.2     | 视频处理     |
| OpenCV       | 4.11.0.86 | 图像处理     |
| NumPy        | 2.2.3     | 数值计算     |
| PyTorch      | 2.2.2     | 深度学习框架 |
| Lama Cleaner | 1.2.5     | 图像修复模型 |
| FastAPI      | 0.115.0   | API服务      |
| SQLite       | -         | 数据存储     |

## 3. 功能说明

### 3.1 核心功能

#### 3.1.1 视频水印检测

- **自动检测**：通过多种图像处理算法自动识别视频中的水印区域
- **颜色分割**：基于颜色特征分离水印和背景
- **边缘检测**：使用Canny边缘检测增强水印边界
- **形态学处理**：通过开闭运算优化水印区域

#### 3.1.2 视频水印去除

- **Lama模型修复**：使用先进的深度学习模型修复水印区域
- **GPU加速**：支持CUDA加速，大幅提升处理速度
- **参数可调**：支持调整修复步骤、边缘保留等参数
- **高清策略**：提供多种高清处理策略，保持视频质量

#### 3.1.3 视频处理

- **格式支持**：支持主流视频格式（MP4、AVI、MOV等）
- **帧率保持**：保持原视频帧率和分辨率
- **编码配置**：可配置输出编码、比特率等参数
- **批量处理**：支持批量处理多个视频文件

### 3.2 辅助功能

#### 3.2.1 用户管理

- **用户认证**：支持用户名密码登录
- **用户注册**：完整的用户注册流程，包括输入验证和密码安全处理
- **权限管理**：基于角色的权限控制
- **数据存储**：支持SQLite数据库存储用户信息

##### 用户注册流程

1. **界面交互**：

   - 用户名输入框：支持字母数字组合，长度不少于3个字符
   - 密码输入框：支持大小写字母和数字组合，长度不少于6个字符
   - 确认密码输入框：必须与密码一致
   - 注册/取消按钮：支持点击和回车键触发

2. **输入验证**：

   ```python
   # 用户名验证
   if len(username) < 3 or not username.isalnum():
       return False, "用户名长度不能少于3个字符且只能包含字母和数字"
   
   # 密码验证
   if len(password) < 6 or not (has_upper and has_lower and has_digit):
       return False, "密码长度不能少于6个字符且必须包含大小写字母和数字"
   
   # 密码确认验证
   if password != confirm_password:
       return False, "两次输入的密码不一致"
   ```

3. **注册逻辑**：

   - 调用`register_user`函数处理注册请求
   - 检查用户名是否已存在
   - 使用SHA-256算法对密码进行哈希处理
   - 将用户信息存储到SQLite数据库
   - 返回注册结果并显示相应消息

4. **错误处理**：

   - 用户名已存在："用户名已存在，请更换用户名"
   - 输入格式错误：返回具体错误信息
   - 系统错误："注册时发生错误: {具体错误信息}"

#### 3.2.2 历史记录

- **处理记录**：保存视频处理历史
- **结果查看**：查看历史处理结果
- **数据统计**：提供处理统计信息

#### 3.2.3 配置管理

- **参数调整**：调整水印检测和修复参数
- **保存配置**：保存用户自定义配置
- **主题切换**：支持不同界面主题

#### 3.2.4 管理员功能

管理员用户拥有系统的最高权限，可以执行普通用户无法进行的管理操作。系统默认提供一个管理员账户（用户名：admin，密码：admin123）。

##### 3.2.4.1 管理员特殊权限

- **全局权限**：拥有系统所有操作的权限（view、edit、delete、admin）
- **用户管理权限**：可以添加新用户、修改用户权限、停用用户账户
- **日志查询权限**：可以查询所有用户的操作日志
- **系统配置权限**：可以修改系统级别的配置参数

##### 3.2.4.2 用户管理功能

###### 添加新用户

管理员可以添加具有不同权限的新用户：

- **基本信息**：设置用户名和密码
- **权限分配**：为新用户分配权限（view、edit、delete）
- **状态设置**：设置用户为激活状态

###### 更新用户权限

管理员可以修改现有用户的权限：

- **权限调整**：添加或移除用户的权限
- **角色转换**：可以将普通用户提升为管理员，或降低管理员权限

###### 停用用户

管理员可以停用不再需要的用户账户：

- **账户停用**：停用后用户无法登录系统
- **数据保留**：停用用户的历史记录和数据会被保留
- **恢复账户**：可以随时恢复已停用的用户账户

##### 3.2.4.3 操作日志查询

管理员可以查询所有用户的操作日志，用于系统审计和问题排查：

- **多条件查询**：可以按用户名、时间范围、操作类型筛选日志
- **日志内容**：包含操作时间、操作类型、操作结果、IP地址和详细信息
- **分页查询**：支持分页查询大量日志记录
- **排序功能**：默认按操作时间倒序排列

##### 3.2.4.4 管理员功能使用示例

###### 添加新用户示例

```python
# 管理员添加新用户
from core.security import add_new_user

# 添加一个具有view和edit权限的普通用户
result = add_new_user(username="new_user", password="password123", permissions=["view", "edit"])
if result:
    print("用户添加成功")
else:
    print("用户添加失败")
```

###### 查询操作日志示例

```python
# 管理员查询操作日志
from core.operation_logger import get_operation_logs
from datetime import datetime, timedelta

# 获取最近7天的所有操作日志
end_time = datetime.now()
start_time = end_time - timedelta(days=7)
logs, total_count = get_operation_logs(
    start_time=start_time,
    end_time=end_time,
    page=1,
    page_size=50
)

print(f"共找到 {total_count} 条日志记录")
for log in logs:
    print(f"[{log['operation_time']}] {log['username']} 执行 {log['operation_type']} - {log['operation_result']}")
```

## 4. 环境要求

### 4.1 硬件要求

| 组件 | 最低配置         | 推荐配置         |
| ---- | ---------------- | ---------------- |
| CPU  | Intel i5 4th Gen | Intel i7 8th Gen |
| 内存 | 8 GB RAM         | 16 GB RAM        |
| 显卡 | 集成显卡         | NVIDIA GTX 1660+ |
| 存储 | 10 GB 可用空间   | 50 GB 可用空间   |

### 4.2 软件要求

| 软件     | 版本          | 说明              |
| -------- | ------------- | ----------------- |
| 操作系统 | Windows 10/11 | 仅支持Windows系统 |
| Python   | 3.9+          | 开发环境          |
| FFmpeg   | 最新版        | 视频编解码工具    |
| CUDA     | 11.7+         | GPU加速（可选）   |
| cuDNN    | 8.5+          | GPU加速（可选）   |

## 5. 下载与安装指南

### 5.1 直接下载压缩文件（推荐）

### 5.2 从源码安装

#### 5.2.1 克隆项目仓库

```bash
git clone https://github.com/your-repo/video-watermark-remover.git
cd video-watermark-remover
```

#### 5.2.2 创建虚拟环境

```bash
python -m venv venv
```

激活虚拟环境：

- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

#### 5.2.3 安装依赖

```bash
pip install -r requirements.txt
```

#### 5.2.4 安装FFmpeg

##### Windows系统

1. 访问FFmpeg官网：https://ffmpeg.org/download.html
2. 下载Windows版本的FFmpeg（推荐使用gyan.dev的构建）
3. 解压到任意目录，例如：`C:\ffmpeg`
4. 将`C:\ffmpeg\bin`添加到系统环境变量PATH中

##### macOS系统

```bash
brew install ffmpeg
```

##### Linux系统（Ubuntu/Debian）

```bash
sudo apt update
sudo apt install ffmpeg
```

## 6. 项目配置

### 6.1 配置文件位置

配置文件位于项目根目录下的`configs/settings.json`

### 6.2 主要配置项说明

| 配置项          | 类型   | 默认值     | 说明                   |
| --------------- | ------ | ---------- | ---------------------- |
| sample_frames   | int    | 10         | 用于检测水印的采样帧数 |
| use_gpu         | bool   | true       | 是否使用GPU加速        |
| ldm_steps       | int    | 26         | 修复模型的迭代步数     |
| margin          | int    | 10         | 水印区域的边缘扩展像素 |
| hd_strategy     | string | "ORIGINAL" | 高清处理策略           |
| auto_select_roi | bool   | true       | 是否自动选择水印区域   |
| codec           | string | "libx264"  | 输出视频编码           |
| bitrate         | string | "5000k"    | 输出视频比特率         |
| preset          | string | "medium"   | 编码预设               |
| output_format   | string | "mp4"      | 输出视频格式           |
| theme           | string | "default"  | 界面主题               |
| user_storage    | object | -          | 用户数据存储配置       |

### 6.3 系统安全配置

#### 6.3.1 用户认证安全

- **密码哈希**：使用SHA-256算法对用户密码进行哈希处理后存储

  ```python
  def _hash_password(self, password: str) -> str:
      return hashlib.sha256(password.encode('utf-8')).hexdigest()
  ```

- **输入验证**：对用户名和密码进行严格的格式验证，防止恶意输入

- **错误提示**：注册时提供模糊的错误提示，避免泄露系统信息

#### 6.3.2 访问控制配置

- **初始化方式**：通过`core.security.initialize_access_control`函数初始化访问控制模块

  ```python
  # 在main.py中初始化
  from core.security import initialize_access_control
  user_storage_config = config.get("user_storage", {})
  storage_type = user_storage_config.get("type", "sqlite")
  storage_path = user_storage_config.get("file_path", "users.db")
  initialize_access_control(user_db_path=storage_path, storage_type=storage_type)
  ```

- **权限管理**：支持基于角色的权限控制，默认权限包括['view', 'edit', 'delete']

- **用户状态**：支持用户激活/停用功能，增强系统安全性

#### 6.3.3 数据存储安全

- **数据库类型**：默认使用SQLite数据库存储用户信息
- **数据库路径**：可通过配置文件中的`user_storage.file_path`指定
- **存储结构**：用户信息以哈希密码形式存储，不保存明文密码

#### 6.3.4 安全最佳实践

- 定期更新数据库文件权限，限制访问
- 避免在日志中记录敏感信息
- 建议定期备份用户数据库
- 对于生产环境，建议使用更安全的数据库加密方案

### 6.4 修改配置

1. 直接编辑`configs/settings.json`文件
2. 通过软件界面的"设置"菜单修改（推荐）

## 7. 使用方法

### 7.1 启动软件



```bash
cd video-watermark-remover
python run.py
```

### 7.2 基本操作流程

1. **登录**：输入用户名和密码登录软件
2. **选择视频**：点击"选择视频"按钮，浏览并选择要处理的视频文件
3. **设置输出**：点击"输出目录"按钮，选择处理结果的保存位置
4. **调整参数**：根据需要调整水印检测和修复参数
5. **预览**：点击"预览"按钮，查看水印检测结果
6. **处理**：点击"开始处理"按钮，开始视频去水印过程
7. **查看结果**：处理完成后，可直接打开输出目录查看结果视频

### 7.3 功能演示

#### 7.3.1 水印检测

1. 选择视频文件后，软件会自动检测水印区域
2. 在预览窗口中可以查看检测到的水印位置
3. 可以手动调整水印区域（如果自动检测不准确）

#### 7.3.2 参数调整

- **检测参数**：调整采样帧数、颜色分割阈值等
- **修复参数**：调整修复步数、边缘保留等
- **输出参数**：调整输出格式、编码等

#### 7.3.3 批量处理

1. 点击"批量处理"按钮
2. 选择多个视频文件
3. 设置统一的输出目录和参数
4. 点击"开始批量处理"按钮

## 8. 常见问题及解决方案

### 8.1 启动问题

#### 8.1.1 软件无法启动

**问题描述**：双击可执行文件后，软件无响应或弹出错误提示

**解决方案**：

- 检查是否安装了所有必要的依赖
- 确保安装了正确版本的Python和FFmpeg
- 尝试以管理员身份运行软件
- 查看错误日志文件获取详细信息

#### 8.1.2 缺少依赖包

**问题描述**：启动时提示缺少某个Python包

**解决方案**：

```bash
pip install 缺少的包名
```

### 8.2 处理问题

#### 8.2.1 水印检测不准确

**问题描述**：软件未能正确检测到视频中的水印

**解决方案**：

- 调整"采样帧数"参数，增加采样数量
- 启用"颜色分割"选项
- 调整"边缘检测"阈值
- 手动调整水印区域

#### 8.2.2 修复质量不佳

**问题描述**：水印去除后留有明显痕迹

**解决方案**：

- 增加"ldm_steps"参数值
- 调整"margin"参数，增加修复区域
- 尝试不同的"hd_strategy"选项
- 确保启用了GPU加速

#### 8.2.3 处理速度太慢

**问题描述**：视频处理过程耗时过长

**解决方案**：

- 启用GPU加速（需配置CUDA）
- 降低"ldm_steps"参数值
- 选择较低的"bitrate"参数
- 关闭"预览前处理"选项

### 8.3 其他问题

#### 8.3.1 中文路径问题

**问题描述**：软件无法处理包含中文字符的文件路径

**解决方案**：

- 确保使用的是最新版本的软件
- 检查FFmpeg是否支持中文路径
- 尝试将视频文件移动到不包含中文字符的目录

#### 8.3.2 权限错误

**问题描述**：无法保存处理结果或访问配置文件

**解决方案**：

- 检查文件和目录的权限设置
- 以管理员身份运行软件
- 确保输出目录存在且可写

## 9. 项目目录结构

```
video-watermark-remover/
├── src/                       # 源代码目录
│   ├── gui/                   # GUI界面模块
│   │   ├── __init__.py
│   │   ├── login_dialog.py    # 登录对话框
│   │   ├── main_window.py     # 主窗口
│   │   ├── preview_dialog.py  # 预览对话框
│   │   ├── progress_dialog.py # 进度对话框
│   │   ├── register_dialog.py # 注册对话框
│   │   └── styles.py          # 样式定义
│   ├── core/                  # 核心功能模块
│   │   ├── __init__.py
│   │   ├── security/          # 安全模块
│   │   ├── history_manager.py # 历史记录管理
│   │   ├── lama_inpainter.py  # Lama模型修复
│   │   ├── utils.py           # 工具函数
│   │   ├── video_processor.py # 视频处理器
│   │   └── watermark_detector.py # 水印检测器
│   ├── __init__.py
│   └── main.py                # 主程序入口
├── configs/                   # 配置文件目录
│   └── settings.json          # 主要配置文件
├── venv/                      # 虚拟环境目录
├── output/                    # 默认输出目录
├── README.md                  # 项目说明文档
├── requirements.txt           # 依赖列表
├── run.py                     # 启动脚本
├── run.spec                   # PyInstaller打包配置
├── users.db                   # 用户数据库
└── ...                        # 其他辅助文件
```

### 9.1 主要文件说明

| 文件/目录        | 功能说明        |
| ---------------- | --------------- |
| src/             | 项目核心源代码  |
| src/gui/         | GUI界面相关代码 |
| src/core/        | 核心功能实现    |
| configs/         | 配置文件目录    |
| output/          | 默认输出目录    |
| run.py           | 项目启动脚本    |
| requirements.txt | 项目依赖列表    |
| users.db         | 用户数据存储    |

## 10. 数据库架构

### 10.1 数据库类型

本项目使用SQLite数据库进行数据存储，具有以下特点：

- 轻量级：无需单独安装数据库服务器，数据存储在本地文件中
- 零配置：无需复杂的数据库配置
- 跨平台：支持Windows、macOS和Linux系统
- 高性能：对于中小规模应用具有良好的性能表现
- 安全性：通过文件系统权限控制访问

数据库文件位于项目根目录下的`users.db`，包含用户信息、权限和历史记录数据。

### 10.2 主要表结构

#### 10.2.1 users表（用户信息）

| 字段名        | 类型    | 约束               | 说明                         |
| ------------- | ------- | ------------------ | ---------------------------- |
| username      | TEXT    | PRIMARY KEY        | 用户名（唯一标识）           |
| password_hash | TEXT    | NOT NULL           | 哈希后的密码（SHA-256算法）  |
| is_active     | INTEGER | NOT NULL DEFAULT 1 | 用户状态（1: 激活, 0: 停用） |

#### 10.2.2 user_permissions表（用户权限）

| 字段名      | 类型                   | 约束                  | 说明                                    |
| ----------- | ---------------------- | --------------------- | --------------------------------------- |
| username    | TEXT                   | NOT NULL, FOREIGN KEY | 关联的用户名（引用users表）             |
| permission  | TEXT                   | NOT NULL              | 权限名称（如view, edit, delete, admin） |
| PRIMARY KEY | (username, permission) | -                     | 复合主键，确保权限唯一性                |

#### 10.2.3 user_history表（用户操作历史）

| 字段名         | 类型     | 约束                      | 说明                                   |
| -------------- | -------- | ------------------------- | -------------------------------------- |
| id             | INTEGER  | PRIMARY KEY AUTOINCREMENT | 记录ID（自增长）                       |
| username       | TEXT     | NOT NULL                  | 关联的用户名                           |
| video_path     | TEXT     | NOT NULL                  | 视频文件路径                           |
| operation_type | TEXT     | NOT NULL                  | 操作类型（import: 导入, export: 导出） |
| operation_time | DATETIME | DEFAULT CURRENT_TIMESTAMP | 操作时间                               |
| file_name      | TEXT     | NOT NULL                  | 文件名                                 |
| file_size      | INTEGER  | -                         | 文件大小（字节）                       |

### 10.3 表关系

```
┌──────────────┐      ┌────────────────────┐
│   users      │      │ user_permissions   │
├──────────────┤      ├────────────────────┤
│ username (PK)│──────│ username (FK)      │
│ password_hash│      │ permission         │
│ is_active    │      └────────────────────┘
└──────────────┘              ▲
        │                     │
        │                     │
        ▼                     │
┌──────────────┐              │
│ user_history │              │
├──────────────┤              │
│ id (PK)      │              │
│ username     │──────────────┘
│ video_path   │
│ operation_type│
│ operation_time│
│ file_name    │
│ file_size    │
└──────────────┘
```

### 10.4 索引设计

| 表名             | 索引字段               | 索引类型    | 说明                           |
| ---------------- | ---------------------- | ----------- | ------------------------------ |
| users            | username               | PRIMARY KEY | 唯一标识用户，加速用户查询     |
| user_permissions | (username, permission) | PRIMARY KEY | 复合主键，确保权限唯一性       |
| user_history     | id                     | PRIMARY KEY | 唯一标识历史记录，加速记录查询 |
| user_history     | username               | INDEX       | 加速按用户名查询历史记录       |
| user_history     | operation_time         | INDEX       | 加速按时间排序和查询历史记录   |

### 10.5 数据存储策略

1. **本地存储**：数据库文件存储在应用程序本地，便于访问和管理
2. **安全性措施**：
   - 密码使用SHA-256算法进行哈希处理，不存储明文密码
   - 数据库文件权限设置为仅允许应用程序访问
   - 输入数据进行严格验证和清理，防止SQL注入攻击
3. **数据备份**：建议定期备份`users.db`文件，防止数据丢失
4. **性能优化**：
   - 使用索引加速查询操作
   - 历史记录采用分页查询，避免一次性加载过多数据
   - 定期清理过期历史记录，保持数据库大小合理

## 11. 开发与贡献

### 11.1 开发环境搭建

1. **克隆仓库**

   ```bash
   git clone https://github.com/your-repo/video-watermark-remover.git
   cd video-watermark-remover
   ```

2. **创建虚拟环境**

   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**

   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

### 10.2 代码规范

- 遵循PEP 8代码风格
- 使用类型注解
- 编写清晰的文档字符串
- 使用描述性的变量和函数名

### 10.3 测试

#### 10.3.1 单元测试

```bash
python -m pytest tests/unit/
```

#### 10.3.2 集成测试

```bash
python -m pytest tests/integration/
```

#### 10.3.3 功能测试

```bash
python test_gui.py
python test_process.py
```

### 10.4 代码提交流程

1. **创建分支**

   ```bash
   git checkout -b feature/your-feature
   ```

2. **编写代码**

3. **运行测试**

   ```bash
   python -m pytest
   ```

4. **提交代码**

   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

5. **推送分支**

   ```bash
   git push origin feature/your-feature
   ```

6. **创建Pull Request**

### 10.5 贡献指南

- 遵循项目的代码规范
- 提供详细的代码注释
- 编写测试用例
- 更新文档
- 提交清晰的Pull Request

## 12. 版权信息

### 12.1 开源协议

本项目采用MIT开源协议，详见LICENSE文件

### 12.2 版权声明

Copyright © 2025 视频去水印软件开发团队

保留所有权利

### 12.3 第三方库声明

本项目使用了以下第三方库：

- PyQt5: https://riverbankcomputing.com/software/pyqt/intro
- MoviePy: https://zulko.github.io/moviepy/
- OpenCV: https://opencv.org/
- PyTorch: https://pytorch.org/
- Lama Cleaner: https://github.com/Sanster/lama-cleaner
- FastAPI: https://fastapi.tiangolo.com/

---

**版本历史**:

- v1.0.6 (2025-12-23): 版本发布，包含基本的视频去水印功能

**更新日志**:

- 2025-12-23: 修复中文路径问题
- 2025-12-8: 优化水印检测算法
- 2025-11-10: 添加批量处理功能
- 2025-10-28: 集成Lama修复模型
- 2025-10-19: 完成GUI界面开发
- 2025-9-23: 项目初始化

---

**免责声明**:
本软件仅用于学习和研究目的，请勿用于商业用途或非法用途。使用本软件处理的视频应遵守相关法律法规和版权协议。