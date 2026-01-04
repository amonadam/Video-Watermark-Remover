#!/usr/bin/env python3
"""
登录模块压力测试脚本
用于测试登录系统同时处理多个登录请求的性能和稳定性
"""
import sys
import os
import time
import threading
import multiprocessing
import random
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入需要的模块
from src.core.security.access_control import authenticate_user
from src.core.utils import set_current_user, get_current_user

# 测试配置
CONFIG = {
    "total_requests": 1000,  # 总请求数
    "concurrent_users": 50,   # 并发用户数
    "test_duration": None,    # 测试持续时间（秒），None表示完成所有请求
    "success_ratio": 0.8,     # 成功登录的比例
    "invalid_username_ratio": 0.1,  # 使用无效用户名的比例
    "invalid_password_ratio": 0.1   # 使用错误密码的比例
}

# 测试用户数据（必须与数据库中的用户一致）
TEST_USERS = [
    ("admin", "admin123"),    # 管理员用户
    ("user", "user123")       # 普通用户
]

# 全局统计数据
STATS = {
    "total_requests": 0,
    "success_requests": 0,
    "failed_requests": 0,
    "response_times": [],
    "start_time": 0,
    "end_time": 0,
    "errors": []
}

# 线程锁
LOCK = threading.Lock()

def login_request(request_id, username, password):
    """执行单个登录请求
    
    Args:
        request_id: 请求ID
        username: 用户名
        password: 密码
    """
    global STATS
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 执行登录请求
        result = authenticate_user(username, password)
        
        # 记录结束时间
        end_time = time.time()
        response_time = end_time - start_time
        
        # 更新统计数据
        with LOCK:
            STATS["total_requests"] += 1
            STATS["response_times"].append(response_time)
            
            if result is not None:
                STATS["success_requests"] += 1
            else:
                STATS["failed_requests"] += 1
                
        return {
            "request_id": request_id,
            "username": username,
            "password": password,
            "success": result is not None,
            "response_time": response_time,
            "timestamp": start_time
        }
    except Exception as e:
        # 记录错误
        with LOCK:
            STATS["total_requests"] += 1
            STATS["failed_requests"] += 1
            STATS["errors"].append(str(e))
        
        return {
            "request_id": request_id,
            "username": username,
            "password": password,
            "success": False,
            "response_time": -1,
            "timestamp": time.time(),
            "error": str(e)
        }

def generate_login_data():
    """生成登录测试数据
    
    Returns:
        (username, password) 元组
    """
    rand = random.random()
    
    # 随机选择测试类型
    if rand < CONFIG["success_ratio"]:
        # 成功登录
        return random.choice(TEST_USERS)
    elif rand < CONFIG["success_ratio"] + CONFIG["invalid_username_ratio"]:
        # 无效用户名
        return (f"invalid_user_{random.randint(1, 10000)}", "password")
    else:
        # 无效密码
        user, _ = random.choice(TEST_USERS)
        return (user, f"wrong_password_{random.randint(1, 10000)}")

def user_thread(thread_id, requests_per_thread):
    """用户线程，模拟一个用户发送多个登录请求
    
    Args:
        thread_id: 线程ID
        requests_per_thread: 每个线程的请求数
    """
    results = []
    
    for i in range(requests_per_thread):
        # 检查是否达到测试持续时间
        if CONFIG["test_duration"] and (time.time() - STATS["start_time"]) > CONFIG["test_duration"]:
            break
            
        request_id = thread_id * requests_per_thread + i
        username, password = generate_login_data()
        
        # 发送登录请求
        result = login_request(request_id, username, password)
        results.append(result)
        
        # 随机延迟，模拟真实用户行为
        time.sleep(random.uniform(0.01, 0.1))
    
    return results

def run_login_stress_test():
    """
    运行登录压力测试
    """
    print("=" * 60)
    print(f"开始登录模块压力测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总请求数: {CONFIG['total_requests']}")
    print(f"并发用户数: {CONFIG['concurrent_users']}")
    if CONFIG['test_duration'] is None:
        duration_str = '直到完成所有请求'
    else:
        duration_str = f'{CONFIG["test_duration"]}秒'
    print(f"测试持续时间: {duration_str}")
    print(f"成功登录比例: {CONFIG['success_ratio']*100:.0f}%")
    print("=" * 60)
    
    # 初始化统计数据
    global STATS
    STATS = {
        "total_requests": 0,
        "success_requests": 0,
        "failed_requests": 0,
        "response_times": [],
        "start_time": time.time(),
        "end_time": 0,
        "errors": []
    }
    
    # 计算每个线程的请求数
    requests_per_thread = CONFIG["total_requests"] // CONFIG["concurrent_users"]
    remaining_requests = CONFIG["total_requests"] % CONFIG["concurrent_users"]
    
    # 创建线程列表
    threads = []
    for i in range(CONFIG["concurrent_users"]):
        # 分配剩余请求
        requests = requests_per_thread
        if i < remaining_requests:
            requests += 1
            
        # 创建线程
        thread = threading.Thread(target=user_thread, args=(i, requests))
        threads.append(thread)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 记录结束时间
    STATS["end_time"] = time.time()
    total_duration = STATS["end_time"] - STATS["start_time"]
    
    # 计算统计指标
    if STATS["response_times"]:
        avg_response_time = sum(STATS["response_times"]) / len(STATS["response_times"])
        min_response_time = min(STATS["response_times"])
        max_response_time = max(STATS["response_times"])
        p95_response_time = sorted(STATS["response_times"])[int(len(STATS["response_times"]) * 0.95)]
        p99_response_time = sorted(STATS["response_times"])[int(len(STATS["response_times"]) * 0.99)]
    else:
        avg_response_time = 0
        min_response_time = 0
        max_response_time = 0
        p95_response_time = 0
        p99_response_time = 0
    
    success_rate = STATS["success_requests"] / STATS["total_requests"] * 100 if STATS["total_requests"] > 0 else 0
    throughput = STATS["total_requests"] / total_duration if total_duration > 0 else 0
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print(f"登录压力测试完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"总测试时间: {total_duration:.2f}秒")
    print(f"完成请求数: {STATS['total_requests']}")
    print(f"成功请求数: {STATS['success_requests']}")
    print(f"失败请求数: {STATS['failed_requests']}")
    print(f"成功率: {success_rate:.2f}%")
    print(f"吞吐量: {throughput:.2f} 请求/秒")
    print(f"平均响应时间: {avg_response_time:.4f}秒")
    print(f"最小响应时间: {min_response_time:.4f}秒")
    print(f"最大响应时间: {max_response_time:.4f}秒")
    print(f"95%响应时间: {p95_response_time:.4f}秒")
    print(f"99%响应时间: {p99_response_time:.4f}秒")
    print(f"错误类型数: {len(STATS['errors'])}")
    
    # 输出前10个错误信息
    if STATS['errors']:
        print("\n前10个错误信息:")
        unique_errors = list(set(STATS['errors']))
        for i, error in enumerate(unique_errors[:10]):
            count = STATS['errors'].count(error)
            print(f"  {i+1}. {error} (出现{count}次)")
    
    # 返回统计结果
    return {
        "total_duration": total_duration,
        "total_requests": STATS["total_requests"],
        "success_requests": STATS["success_requests"],
        "failed_requests": STATS["failed_requests"],
        "success_rate": success_rate,
        "throughput": throughput,
        "avg_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time,
        "p95_response_time": p95_response_time,
        "p99_response_time": p99_response_time,
        "error_count": len(STATS['errors'])
    }

def main():
    """主函数"""
    # 可以通过命令行参数覆盖配置
    if len(sys.argv) > 1:
        try:
            CONFIG["total_requests"] = int(sys.argv[1])
        except ValueError:
            pass
    
    if len(sys.argv) > 2:
        try:
            CONFIG["concurrent_users"] = int(sys.argv[2])
        except ValueError:
            pass
    
    if len(sys.argv) > 3:
        try:
            CONFIG["test_duration"] = int(sys.argv[3])
        except ValueError:
            pass
    
    # 运行压力测试
    run_login_stress_test()

if __name__ == "__main__":
    main()