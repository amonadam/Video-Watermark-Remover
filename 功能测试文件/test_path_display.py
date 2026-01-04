import os
import sys
import sqlite3
from datetime import datetime

# 连接到数据库
db_path = os.path.join(os.getcwd(), 'users.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建测试用户名
test_username = "test_user"

# 创建不同长度的路径测试数据
test_paths = [
    # 短路径
    "D:/video1.mp4",
    "E:/short.mp4",
    
    # 中等长度路径
    "D:/Videos/Movies/Action/movie1.mp4",
    "E:/Downloads/VideoFiles/2023/holiday/vacation.mp4",
    
    # 长路径
    "C:/Users/TestUser/Documents/VideoProjects/2025/December/Week3/ProjectX/Videos/SourceFiles/main_video_20251220_123456.mp4",
    
    # 非常长的路径（接近Windows路径长度限制）
    "C:/Users/TestUser/Documents/VideoProjects/2025/December/Week3/ProjectX/Videos/SourceFiles/Backup/CopyOfMainVideo_20251220_123456_WithAdditionalInformation_ForTestingPurposes_1234567890123456789012345678901234567890.mp4",
    
    # 包含中文的长路径
    "D:/用户资料/视频项目/2025年/12月/第三周/项目X/视频文件/原始素材/主要视频_20251220_123456_包含详细信息的副本_用于测试目的_1234567890.mp4",
    
    # 包含特殊字符的路径（但不包含危险字符）
    "E:/Video Files/Project_X/Test-Video_123.mp4"
]

print("开始生成测试数据...")

# 清空测试用户的历史记录
cursor.execute("DELETE FROM user_history WHERE username = ?", (test_username,))
conn.commit()

# 添加测试记录
for i, path in enumerate(test_paths):
    file_name = os.path.basename(path)
    operation_type = "import" if i % 2 == 0 else "export"
    
    try:
        cursor.execute('''
            INSERT INTO user_history (username, video_path, operation_type, file_name, operation_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (test_username, path, operation_type, file_name, datetime.now()))
        print(f"添加测试记录 {i+1}/{len(test_paths)}: {path}")
        print(f"  路径长度: {len(path)}, 文件名长度: {len(file_name)}")
    except Exception as e:
        print(f"添加测试记录失败: {e}")

conn.commit()
conn.close()

print("\n测试数据生成完成！")
print(f"共生成 {len(test_paths)} 条测试记录，用户名: {test_username}")
print("\n请使用测试用户名登录应用程序，查看历史记录表格中路径的显示效果。")
print("验证要点：")
print("1. 路径和文件名是否完整显示（或通过水平滚动可见）")
print("2. 鼠标悬停时是否显示完整路径的tooltip")
print("3. 界面布局是否正常，没有异常情况")
