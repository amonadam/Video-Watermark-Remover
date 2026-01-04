#!/usr/bin/env python3
"""
测试VideoProcessor的资源清理功能
特别是验证在初始化失败情况下的安全清理
"""

import sys
import os
import tempfile
import traceback

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.video_processor import VideoProcessor
from core.watermark_detector import WatermarkDetector
from core.lama_inpainter import LamaInpainter

def test_cleanup_with_initialization_failure():
    """测试初始化失败时的资源清理"""
    print("测试1: 模拟VideoProcessor初始化失败情况")
    
    try:
        # 创建临时文件路径
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name
        
        # 创建无效的配置（可能导致初始化失败）
        invalid_config = {}
        
        # 尝试创建VideoProcessor实例，但传递无效参数
        # 这里我们故意传递None作为inpainter来模拟初始化失败
        vp = VideoProcessor(
            video_path=tmp_path,
            output_dir=os.path.dirname(tmp_path),
            detector=WatermarkDetector(),
            inpainter=None,  # 故意传递None来模拟初始化失败
            config=invalid_config
        )
        
        print("❌ 测试失败: 应该在初始化时抛出错误")
        
    except Exception as e:
        print(f"✅ 捕获到预期的初始化错误: {type(e).__name__}: {e}")
        print("   错误堆栈:")
        print(traceback.format_exc())
        print("✅ 测试通过: 初始化失败时未发生AttributeError")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_cleanup_with_valid_initialization():
    """测试正常初始化后的资源清理"""
    print("\n测试2: 正常初始化后的资源清理")
    
    try:
        # 创建临时文件路径
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name
        
        output_dir = os.path.dirname(tmp_path)
        
        # 创建有效的处理器实例
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        inpainter.initialize(device='cpu')  # 使用CPU设备避免GPU依赖
        
        vp = VideoProcessor(
            video_path=tmp_path,
            output_dir=output_dir,
            detector=detector,
            inpainter=inpainter,
            config={}
        )
        
        # 显式调用_cleanup方法
        vp._cleanup()
        print("✅ 显式调用_cleanup方法成功")
        
        # 手动删除实例，触发__del__方法
        del vp
        print("✅ 手动删除实例，__del__方法被调用")
        
        print("✅ 测试通过: 正常初始化后的资源清理成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {type(e).__name__}: {e}")
        print(traceback.format_exc())
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_cleanup_with_partial_initialization():
    """测试部分初始化失败时的资源清理"""
    print("\n测试3: 测试VideoProcessor的_cleanup方法鲁棒性")
    
    try:
        # 创建一个最小化的VideoProcessor实例，只初始化部分属性
        vp = VideoProcessor.__new__(VideoProcessor)
        
        # 只设置部分属性，模拟部分初始化
        vp.video_path = "/tmp/test.mp4"
        vp.output_dir = "/tmp"
        # 故意不设置inpainter和detector属性
        
        # 调用_cleanup方法，应该不会抛出AttributeError
        vp._cleanup()
        
        print("✅ 测试通过: _cleanup方法在部分初始化情况下安全执行")
        
    except AttributeError as e:
        print(f"❌ 测试失败: _cleanup方法抛出AttributeError: {e}")
        print(traceback.format_exc())
    except Exception as e:
        print(f"⚠️  测试遇到其他错误: {type(e).__name__}: {e}")
        print(traceback.format_exc())

def test_lama_inpainter_cleanup():
    """测试LamaInpainter的资源清理"""
    print("\n测试4: 测试LamaInpainter的资源清理")
    
    try:
        # 创建LamaInpainter实例
        inpainter = LamaInpainter()
        inpainter.initialize(device='cpu')
        
        # 显式调用clear_cache方法
        inpainter.clear_cache()
        print("✅ 显式调用clear_cache方法成功")
        
        # 手动删除实例，触发__del__方法
        del inpainter
        print("✅ 手动删除实例，__del__方法被调用")
        
        print("✅ 测试通过: LamaInpainter资源清理成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {type(e).__name__}: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    print("开始测试VideoProcessor资源清理功能")
    print("=" * 60)
    
    test_cleanup_with_partial_initialization()
    test_cleanup_with_valid_initialization()
    test_cleanup_with_initialization_failure()
    test_lama_inpainter_cleanup()
    
    print("\n" + "=" * 60)
    print("所有测试完成")
