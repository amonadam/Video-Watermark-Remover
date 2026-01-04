#!/usr/bin/env python3
"""
视频去水印系统压力测试脚本
用于测试系统同时处理多个视频文件的性能和稳定性
"""
import sys
import os
import time
import multiprocessing
import psutil
import torch
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入需要的模块
from src.core.watermark_detector import WatermarkDetector
from src.core.lama_inpainter import LamaInpainter
from src.core.video_processor import VideoProcessor
from src.core.utils import set_current_user

# 配置
CONFIG = {
    "auto_select_roi": True,
    "margin": 50,
    "inpainting_method": "lama",
    "inpainting_mask_blur": 5,
    "color_correction": True,
    "blending_strength": 0.8,
    "enable_gpu": True
}

def process_video(video_path, output_dir, config, process_id):
    """处理单个视频的函数
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        config: 配置参数
        process_id: 进程ID
    """
    try:
        # 初始化检测器和修复器
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        
        # 初始化修复器
        device = "cuda" if config.get("enable_gpu", True) and torch.cuda.is_available() else "cpu"
        inpainter.initialize(device=device, ldm_steps=50, hd_strategy="ORIGINAL")
        
        # 创建处理器
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 处理视频
        result = processor.process()
        
        return {
            "process_id": process_id,
            "video_path": video_path,
            "success": result.get("success", False),
            "processing_time": result.get("processing_time", 0),
            "total_frames": result.get("total_frames", 0),
            "processed_frames": result.get("processed_frames", 0),
            "failed_frames": result.get("failed_frames", 0)
        }
    except Exception as e:
        return {
            "process_id": process_id,
            "video_path": video_path,
            "success": False,
            "error": str(e),
            "processing_time": 0,
            "total_frames": 0,
            "processed_frames": 0,
            "failed_frames": 0
        }

def monitor_system(interval=1, stop_event=None):
    """监控系统资源使用情况
    
    Args:
        interval: 监控间隔（秒）
        stop_event: 停止事件
    """
    stats = {
        "cpu_usage": [],
        "memory_usage": [],
        "disk_usage": [],
        "start_time": time.time()
    }
    
    while True:
        if stop_event and stop_event.is_set():
            break
            
        # 记录系统资源使用情况
        stats["cpu_usage"].append(psutil.cpu_percent(interval=0.1))
        stats["memory_usage"].append(psutil.virtual_memory().percent)
        stats["disk_usage"].append(psutil.disk_usage('/').percent)
        
        time.sleep(interval)
    
    stats["end_time"] = time.time()
    stats["duration"] = stats["end_time"] - stats["start_time"]
    
    return stats

def run_stress_test(video_paths, output_dir, num_parallel_processes=4, test_duration=None):
    """
    运行压力测试
    
    Args:
        video_paths: 视频文件路径列表
        output_dir: 输出目录
        num_parallel_processes: 并行处理的进程数
        test_duration: 测试持续时间（秒），None表示处理完所有视频
    """
    print("=" * 60)
    print(f"开始系统压力测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"并行进程数: {num_parallel_processes}")
    print(f"测试视频数: {len(video_paths)}")
    print(f"测试持续时间: {'直到处理完所有视频' if test_duration is None else f'{test_duration}秒'}")
    print("=" * 60)
    
    # 设置当前用户为管理员
    set_current_user({
        'username': 'admin',
        'permissions': ['view', 'edit', 'delete', 'admin']
    })
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 启动系统监控
    stop_event = multiprocessing.Event()
    monitor_process = multiprocessing.Process(target=monitor_system, args=(1, stop_event))
    monitor_process.start()
    
    # 记录开始时间
    start_time = time.time()
    
    # 创建进程池
    results = []
    with multiprocessing.Pool(processes=num_parallel_processes) as pool:
        # 提交任务
        tasks = []
        for i, video_path in enumerate(video_paths):
            output_subdir = os.path.join(output_dir, f"output_{i}")
            os.makedirs(output_subdir, exist_ok=True)
            
            task = pool.apply_async(process_video, (video_path, output_subdir, CONFIG, i))
            tasks.append(task)
            
            # 如果设置了测试持续时间，检查是否超时
            if test_duration and (time.time() - start_time) > test_duration:
                break
        
        # 获取结果
        for task in tasks:
            results.append(task.get())
    
    # 停止监控
    stop_event.set()
    monitor_process.join()
    
    # 记录结束时间
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 统计结果
    total_processed = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total_processed - successful
    
    total_processing_time = sum(r["processing_time"] for r in results)
    average_processing_time = total_processing_time / successful if successful > 0 else 0
    
    total_frames = sum(r["total_frames"] for r in results)
    processed_frames = sum(r["processed_frames"] for r in results)
    failed_frames = sum(r["failed_frames"] for r in results)
    
    print("\n" + "=" * 60)
    print(f"压力测试完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"总测试时间: {total_duration:.2f}秒")
    print(f"总处理视频数: {total_processed}")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    print(f"成功率: {(successful/total_processed*100):.2f}%" if total_processed > 0 else "成功率: 0.00%")
    print(f"平均处理时间: {average_processing_time:.2f}秒/视频")
    print(f"总帧数: {total_frames}")
    print(f"成功处理帧数: {processed_frames}")
    print(f"失败帧数: {failed_frames}")
    print(f"帧成功率: {(processed_frames/total_frames*100):.2f}%" if total_frames > 0 else "帧成功率: 0.00%")
    print("\n详细结果:")
    for i, result in enumerate(results):
        print(f"视频 {i+1}: {os.path.basename(result['video_path'])}")
        print(f"  状态: {'成功' if result['success'] else '失败'}")
        print(f"  处理时间: {result['processing_time']:.2f}秒")
        if not result['success'] and 'error' in result:
            print(f"  错误信息: {result['error']}")
    
    return {
        "total_duration": total_duration,
        "total_processed": total_processed,
        "successful": successful,
        "failed": failed,
        "average_processing_time": average_processing_time,
        "total_frames": total_frames,
        "processed_frames": processed_frames,
        "failed_frames": failed_frames
    }

def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python stress_test.py <视频目录> <输出目录> [并行进程数] [测试持续时间(秒)]")
        print("示例: python stress_test.py test_videos stress_output 4 300")
        sys.exit(1)
    
    video_dir = sys.argv[1]
    output_dir = sys.argv[2]
    num_parallel_processes = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    test_duration = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    # 检查视频目录
    if not os.path.exists(video_dir):
        print(f"错误: 视频目录 '{video_dir}' 不存在")
        sys.exit(1)
    
    # 获取所有视频文件
    video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
    video_paths = []
    
    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if os.path.splitext(file)[1].lower() in video_extensions:
                video_paths.append(os.path.join(root, file))
    
    if not video_paths:
        print(f"错误: 在目录 '{video_dir}' 中未找到视频文件")
        sys.exit(1)
    
    print(f"找到 {len(video_paths)} 个视频文件")
    for video_path in video_paths:
        print(f"  - {video_path}")
    
    # 运行压力测试
    run_stress_test(video_paths, output_dir, num_parallel_processes, test_duration)

if __name__ == "__main__":
    main()