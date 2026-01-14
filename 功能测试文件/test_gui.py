#!/usr/bin/env python3
"""
测试GUI启动的脚本，用于捕获应用程序的输出和错误信息
"""
import subprocess
import time
import os
import sys

# 可执行文件路径
executable_path = os.path.join("dist", "视频去水印软件.exe")

if not os.path.exists(executable_path):
    print(f"错误：找不到可执行文件 {executable_path}")
    sys.exit(1)

print(f"正在测试可执行文件：{executable_path}")
print(f"测试开始时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 运行可执行文件并捕获输出
try:
    # 使用subprocess运行可执行文件
    process = subprocess.Popen(
        [executable_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False
    )
    
    # 设置超时时间（秒）
    timeout = 30
    
    print(f"正在运行应用程序，超时时间：{timeout}秒...")
    
    # 等待进程结束或超时
    stdout, stderr = process.communicate(timeout=timeout)
    
    # 打印输出
    print("\n" + "=" * 60)
    print("标准输出 (stdout):")
    print("=" * 60)
    if stdout:
        print(stdout)
    else:
        print("无输出")
    
    print("\n" + "=" * 60)
    print("标准错误 (stderr):")
    print("=" * 60)
    if stderr:
        print(stderr)
    else:
        print("无错误输出")
    
    print("\n" + "=" * 60)
    print(f"进程返回码：{process.returncode}")
    
    if process.returncode == 0:
        print("应用程序似乎成功启动并退出")
    else:
        print(f"应用程序以错误码 {process.returncode} 退出")
        
except subprocess.TimeoutExpired:
    print(f"\n超时：应用程序在 {timeout} 秒内未完成")
    print("应用程序可能已经成功启动GUI并在后台运行")
    
    # 尝试获取当前的输出
    stdout_part = process.stdout.read() if process.stdout else ""
    stderr_part = process.stderr.read() if process.stderr else ""
    
    if stdout_part:
        print("\n" + "=" * 60)
        print("部分标准输出:")
        print("=" * 60)
        print(stdout_part)
    
    if stderr_part:
        print("\n" + "=" * 60)
        print("部分标准错误:")
        print("=" * 60)
        print(stderr_part)
    
    # 终止进程
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        
except Exception as e:
    print(f"\n执行测试时出错：{e}")
    import traceback
    traceback.print_exc()
    
finally:
    print(f"\n测试结束时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
