#!/usr/bin/env python3
"""
历史记录功能测试脚本
"""
import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录和src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.history_manager import (
    initialize_history_manager,
    add_history_record,
    get_history_records,
    delete_all_history_records
)

def test_history_functionality():
    """测试历史记录功能"""
    print("=== 历史记录功能测试 ===")
    
    # 初始化历史记录管理器
    try:
        # 使用项目根目录下的users.db文件
        db_path = os.path.join(os.path.dirname(__file__), '..', 'users.db')
        initialize_history_manager(db_path)
        print("✅ 历史记录管理器初始化成功")
    except Exception as e:
        print(f"❌ 历史记录管理器初始化失败: {e}")
        return False
    
    # 测试添加历史记录
    test_username = "test_user"
    test_file_path = "C:/test/video.mp4"
    test_file_name = "video.mp4"
    test_file_size = 1024 * 1024 * 10  # 10MB
    
    try:
        result = add_history_record(
            test_username,
            test_file_path,
            'import',
            test_file_name,
            test_file_size
        )
        if result:
            print("✅ 添加导入历史记录成功")
        else:
            print("❌ 添加导入历史记录失败")
            return False
    except Exception as e:
        print(f"❌ 添加历史记录时发生错误: {e}")
        return False
    
    # 测试添加导出历史记录
    test_output_path = "C:/test/output_video.mp4"
    test_output_name = "output_video.mp4"
    
    try:
        result = add_history_record(
            test_username,
            test_output_path,
            'export',
            test_output_name,
            test_file_size * 2
        )
        if result:
            print("✅ 添加导出历史记录成功")
        else:
            print("❌ 添加导出历史记录失败")
            return False
    except Exception as e:
        print(f"❌ 添加导出历史记录时发生错误: {e}")
        return False
    
    # 测试查询历史记录
    try:
        history_list, total_count = get_history_records(
            test_username,
            page=1,
            page_size=10
        )
        print(f"✅ 查询历史记录成功，共 {total_count} 条记录")
        print("\n历史记录列表:")
        for item in history_list:
            print(f"  ID: {item['id']}")
            print(f"  类型: {item['operation_type']}")
            print(f"  文件名: {item['file_name']}")
            print(f"  路径: {item['video_path']}")
            print(f"  大小: {item['file_size']} 字节")
            print(f"  时间: {item['operation_time']}")
            print("  --")
    except Exception as e:
        print(f"❌ 查询历史记录时发生错误: {e}")
        return False
    
    # 测试按操作类型筛选
    try:
        import_list, import_count = get_history_records(
            test_username,
            operation_type='import'
        )
        print(f"✅ 筛选导入记录成功，共 {import_count} 条导入记录")
        
        export_list, export_count = get_history_records(
            test_username,
            operation_type='export'
        )
        print(f"✅ 筛选导出记录成功，共 {export_count} 条导出记录")
    except Exception as e:
        print(f"❌ 筛选历史记录时发生错误: {e}")
        return False
    
    # 测试删除历史记录
    try:
        result = delete_all_history_records(test_username)
        if result:
            print("✅ 删除所有历史记录成功")
        else:
            print("❌ 删除所有历史记录失败")
    except Exception as e:
        print(f"❌ 删除历史记录时发生错误: {e}")
        return False
    
    # 验证删除结果
    try:
        history_list, total_count = get_history_records(
            test_username,
            page=1,
            page_size=10
        )
        if total_count == 0:
            print("✅ 验证删除结果成功，历史记录已清空")
        else:
            print(f"❌ 验证删除结果失败，仍有 {total_count} 条记录")
    except Exception as e:
        print(f"❌ 验证删除结果时发生错误: {e}")
        return False
    
    print("\n=== 所有测试通过！===\n")
    return True

if __name__ == "__main__":
    test_history_functionality()
