import sqlite3
import os

# 连接到数据库
db_path = os.path.join(os.getcwd(), 'users.db')
if not os.path.exists(db_path):
    db_path = os.path.join(os.getcwd(), 'data', 'users.db')
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        exit(1)

print(f"连接到数据库: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看user_history表结构
print("\n--- 表结构信息 ---")
cursor.execute("PRAGMA table_info(user_history)")
columns = cursor.fetchall()
for col in columns:
    print(f"列名: {col[1]}, 类型: {col[2]}, 约束: {col[3]}")

# 查询最新的历史记录
print("\n--- 最新历史记录 ---")
cursor.execute('SELECT id, username, video_path, operation_type, file_name, operation_time FROM user_history ORDER BY id DESC LIMIT 10;')
rows = cursor.fetchall()

for row in rows:
    id, username, video_path, operation_type, file_name, operation_time = row
    print(f'ID: {id}')
    print(f'用户名: {username}')
    print(f'视频路径: {video_path}')  # 验证路径完整性
    print(f'操作类型: {operation_type}')
    print(f'文件名: {file_name}')     # 验证文件名完整性
    print(f'操作时间: {operation_time}')
    print(f'路径长度: {len(video_path)}, 文件名长度: {len(file_name)}')
    print('-' * 50)

conn.close()