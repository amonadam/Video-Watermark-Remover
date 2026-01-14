#!/usr/bin/env python3
"""
历史记录功能安全性和完整性测试
"""
import os
import sys
import sqlite3
import time
from typing import List, Dict, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入相关模块
from core.history_manager import (
    add_history_record, get_history_records, delete_all_history_records,
    initialize_history_manager
)
from core.security.access_control import (
    authenticate_user, check_user_permission, initialize_access_control
)
from core.security.system_security import sanitize_input


def test_permission_control():
    """
    测试权限控制：确保用户只能访问自己的历史记录
    """
    print("\n=== 权限控制测试 ===")
    
    # 初始化组件
    initialize_access_control()
    # 使用项目根目录下的users.db文件
    db_path = os.path.join(os.path.dirname(__file__), '..', 'users.db')
    initialize_history_manager(db_path)
    
    # 清理测试数据
    delete_all_history_records("user1")
    delete_all_history_records("user2")
    
    # 用户1添加历史记录
    success1 = add_history_record("user1", "C:/test/video1.mp4", "import", "video1.mp4", 1024)
    if success1:
        print("✅ 用户1添加历史记录成功")
    else:
        print("❌ 用户1添加历史记录失败")
        return False
    
    # 用户2添加历史记录
    success2 = add_history_record("user2", "C:/test/video2.mp4", "import", "video2.mp4", 2048)
    if success2:
        print("✅ 用户2添加历史记录成功")
    else:
        print("❌ 用户2添加历史记录失败")
        return False
    
    # 用户1查询历史记录（应该只看到自己的）
    history1, count1 = get_history_records("user1")
    if count1 == 1 and history1[0]["username"] == "user1":
        print("✅ 用户1只能看到自己的历史记录")
    else:
        print("❌ 用户1权限控制失败")
        return False
    
    # 用户2查询历史记录（应该只看到自己的）
    history2, count2 = get_history_records("user2")
    if count2 == 1 and history2[0]["username"] == "user2":
        print("✅ 用户2只能看到自己的历史记录")
    else:
        print("❌ 用户2权限控制失败")
        return False
    
    # 清理测试数据
    delete_all_history_records("user1")
    delete_all_history_records("user2")
    
    return True


def test_sql_injection_protection():
    """
    测试SQL注入防护
    """
    print("\n=== SQL注入防护测试 ===")
    
    # 初始化组件
    # 使用项目根目录下的users.db文件
    db_path = os.path.join(os.path.dirname(__file__), '..', 'users.db')
    initialize_history_manager(db_path)
    
    # 清理测试数据
    delete_all_history_records("test_user")
    
    # 尝试注入攻击
    malicious_path = "C:/test/video.mp4'); DROP TABLE user_history; --"
    malicious_filename = "video.mp4'); DELETE FROM user_history; --"
    
    # 尝试添加包含注入攻击的历史记录
    success = add_history_record(
        "test_user",
        malicious_path,
        "import",
        malicious_filename,
        1024
    )
    
    if success:
        print("✅ SQL注入防护测试通过：注入尝试被阻止或处理")
    else:
        print("⚠️  SQL注入防护测试：添加历史记录失败（可能是防护机制起作用）")
    
    # 验证表是否仍然存在
    db_path = os.path.join(os.path.dirname(__file__), '..', 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM user_history")
        count = cursor.fetchone()[0]
        print("✅ 用户历史表仍然存在，记录数：", count)
    except sqlite3.OperationalError as e:
        print("❌ SQL注入防护失败：", e)
        return False
    finally:
        conn.close()
    
    # 清理测试数据
    delete_all_history_records("test_user")
    
    return True


def test_input_sanitization():
    """
    测试输入清理功能
    """
    print("\n=== 输入清理功能测试 ===")
    
    # 测试文件路径清理
    test_paths = [
        "C:/test/video.mp4",
        "C:\\test\\video.mp4",
        "C:/test folder/video with spaces.mp4",
        "C:/test/video(with).mp4",  # 包含潜在危险字符
    ]
    
    for path in test_paths:
        sanitized = sanitize_input(path, is_path=True)
        if sanitized and ".mp4" in sanitized:
            print(f"✅ 路径清理成功：{path} -> {sanitized}")
        else:
            print(f"❌ 路径清理失败：{path} -> {sanitized}")
            return False
    
    # 测试文件名清理
    test_filenames = [
        "video.mp4",
        "video with spaces.mp4",
        "video(with)brackets.mp4",
        "video<with>dangerous:chars.mp4",
    ]
    
    for filename in test_filenames:
        sanitized = sanitize_input(filename, is_path=True)
        if sanitized and ".mp4" in sanitized:
            print(f"✅ 文件名清理成功：{filename} -> {sanitized}")
        else:
            print(f"❌ 文件名清理失败：{filename} -> {sanitized}")
            return False
    
    return True


def test_pagination_large_data():
    """
    测试大量数据的分页功能
    """
    print("\n=== 分页功能测试 ===")
    
    # 初始化组件
    # 使用项目根目录下的users.db文件
    db_path = os.path.join(os.path.dirname(__file__), '..', 'users.db')
    initialize_history_manager(db_path)
    
    # 清理测试数据
    delete_all_history_records("pagination_test")
    
    # 添加大量测试数据
    total_records = 50
    page_size = 10
    
    print(f"添加 {total_records} 条测试记录...")
    for i in range(total_records):
        path = f"C:/test/video_{i}.mp4"
        filename = f"video_{i}.mp4"
        add_history_record(
            "pagination_test",
            path,
            "import",
            filename,
            1024 * i
        )
    
    # 测试分页查询
    print(f"测试每页 {page_size} 条记录的分页功能...")
    
    total_pages = (total_records + page_size - 1) // page_size
    
    for page in range(1, total_pages + 1):
        records, count = get_history_records(
            "pagination_test",
            page=page,
            page_size=page_size
        )
        
        expected_count = page_size if page < total_pages else total_records % page_size
        if expected_count == 0:
            expected_count = page_size
        
        if len(records) == expected_count:
            print(f"✅ 第 {page} 页查询成功，获取 {len(records)} 条记录")
        else:
            print(f"❌ 第 {page} 页查询失败，预期 {expected_count} 条，实际 {len(records)} 条")
            return False
    
    # 验证总记录数
    records, total_count = get_history_records("pagination_test", page=1, page_size=100)
    if total_count == total_records:
        print(f"✅ 总记录数验证成功：{total_count} 条")
    else:
        print(f"❌ 总记录数验证失败：预期 {total_records} 条，实际 {total_count} 条")
        return False
    
    # 清理测试数据
    delete_all_history_records("pagination_test")
    
    return True


def test_operation_filtering():
    """
    测试操作类型筛选功能
    """
    print("\n=== 操作类型筛选测试 ===")
    
    # 初始化组件
    # 使用项目根目录下的users.db文件
    db_path = os.path.join(os.path.dirname(__file__), '..', 'users.db')
    initialize_history_manager(db_path)
    
    # 清理测试数据
    delete_all_history_records("filter_test")
    
    # 添加不同类型的历史记录
    add_history_record("filter_test", "C:/test/import1.mp4", "import", "import1.mp4", 1024)
    add_history_record("filter_test", "C:/test/export1.mp4", "export", "export1.mp4", 2048)
    add_history_record("filter_test", "C:/test/import2.mp4", "import", "import2.mp4", 3072)
    add_history_record("filter_test", "C:/test/export2.mp4", "export", "export2.mp4", 4096)
    
    # 查询所有记录
    all_records, all_count = get_history_records("filter_test")
    print(f"✅ 所有记录：{all_count} 条")
    
    # 查询导入记录
    import_records, import_count = get_history_records(
        "filter_test", operation_type="import"
    )
    if import_count == 2:
        print("✅ 导入记录筛选成功：2 条")
    else:
        print(f"❌ 导入记录筛选失败：预期 2 条，实际 {import_count} 条")
        return False
    
    # 查询导出记录
    export_records, export_count = get_history_records(
        "filter_test", operation_type="export"
    )
    if export_count == 2:
        print("✅ 导出记录筛选成功：2 条")
    else:
        print(f"❌ 导出记录筛选失败：预期 2 条，实际 {export_count} 条")
        return False
    
    # 清理测试数据
    delete_all_history_records("filter_test")
    
    return True


def main():
    """
    运行所有测试
    """
    print("=== 历史记录功能安全性和完整性测试 ===")
    
    # 运行测试
    tests = [
        ("权限控制", test_permission_control),
        ("SQL注入防护", test_sql_injection_protection),
        ("输入清理功能", test_input_sanitization),
        ("分页功能", test_pagination_large_data),
        ("操作类型筛选", test_operation_filtering),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常：{e}")
    
    print(f"\n=== 测试结果总结 ===")
    print(f"通过测试：{passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！历史记录功能完整性和安全性验证成功")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
