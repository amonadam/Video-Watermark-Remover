import sqlite3

# 连接数据库
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# 检查user_history表结构
print('user_history表结构:')
cursor.execute('PRAGMA table_info(user_history);')
rows = cursor.fetchall()
for row in rows:
    print(row)

# 检查是否有历史记录
print('\n历史记录数量:')
cursor.execute('SELECT COUNT(*) FROM user_history;')
count = cursor.fetchone()[0]
print(count)

# 关闭连接
conn.close()
