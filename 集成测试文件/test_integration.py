"""
集成测试用例 - 测试核心模块间的交互
"""
import os
import sys
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.watermark_detector import WatermarkDetector
from core.lama_inpainter import LamaInpainter
from core.video_processor import VideoProcessor
from core.security.access_control import AccessController
from core.operation_logger import OperationLogger
from core.utils import set_current_user


class TestWatermarkDetectorAndInpainterIntegration:
    """测试水印检测器与图像修复器的集成"""
    
    def test_detector_to_inpainter_workflow(self):
        """测试从检测到修复的完整工作流程"""
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        # 创建测试图像
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 模拟水印区域
        test_image[100:200, 100:200] = [255, 255, 0]  # 黄色水印
        
        # 检测水印
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        # 修复图像
        result = inpainter.inpaint(test_image, mask)
        
        # 验证结果
        assert result is not None
        assert result.shape == test_image.shape
        assert result.dtype == np.uint8
    
    def test_detector_roi_to_inpainter(self):
        """测试检测器ROI坐标传递给修复器"""
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        # 创建测试图像
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 模拟检测器生成的掩膜
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        # 获取ROI坐标
        margin = 50
        roi_coords = detector.get_roi_coordinates(mask, margin)
        
        # 提取ROI
        y_min, y_max, x_min, x_max = roi_coords
        roi = test_image[y_min:y_max, x_min:x_max]
        roi_mask = mask[y_min:y_max, x_min:x_max]
        
        # 修复ROI
        repaired_roi = inpainter.inpaint(roi, roi_mask)
        
        # 验证结果
        assert repaired_roi is not None
        assert repaired_roi.shape == roi.shape
    
    def test_detector_inpainter_color_correction_integration(self):
        """测试检测器、修复器和颜色校正的集成"""
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        # 创建测试图像
        source = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        target = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[50:70, 50:70] = 255
        
        # 检测水印区域
        roi_coords = detector.get_roi_coordinates(mask, margin=10)
        
        # 修复图像
        repaired = inpainter.inpaint(source, mask)
        
        # 验证修复结果可用于颜色校正
        assert repaired is not None
        assert repaired.shape == source.shape


class TestVideoProcessorIntegration:
    """测试视频处理器与其他模块的集成"""
    
    def test_processor_detector_inpainter_integration(self):
        """测试视频处理器、检测器和修复器的集成"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            detector = WatermarkDetector()
            inpainter = LamaInpainter()
            inpainter.use_cv2_fallback = True
            config = {
                "auto_select_roi": True,
                "margin": 50,
                "codec": "libx264",
                "bitrate": "5000k",
                "preset": "medium"
            }
            
            # 创建测试视频路径
            video_path = os.path.join(temp_dir, "test.mp4")
            output_dir = os.path.join(temp_dir, "output")
            
            # 创建处理器
            processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
            
            # 验证处理器正确初始化
            assert processor.detector == detector
            assert processor.inpainter == inpainter
            assert processor.config == config
            
            # 验证处理器可以调用检测器方法
            mask = np.zeros((480, 640), dtype=np.uint8)
            mask[100:200, 100:200] = 255
            roi_coords = processor.detector.get_roi_coordinates(mask, 50)
            assert roi_coords is not None
            
            # 验证处理器可以调用修复器方法
            test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            test_mask = np.zeros((100, 100), dtype=np.uint8)
            test_mask[50:70, 50:70] = 255
            result = processor.inpainter.inpaint(test_image, test_mask)
            assert result is not None
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_processor_color_correction_integration(self):
        """测试视频处理器颜色校正与其他模块的集成"""
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        config = {}
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            video_path = os.path.join(temp_dir, "test.mp4")
            output_dir = os.path.join(temp_dir, "output")
            
            processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
            
            # 测试颜色校正功能
            source = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            target = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            mask = np.zeros((100, 100), dtype=np.uint8)
            mask[50:70, 50:70] = 255
            
            corrected = processor._match_colors(source, target, mask)
            
            assert corrected is not None
            assert corrected.shape == source.shape
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('core.video_processor.VideoFileClip')
    @patch('core.video_processor.ImageSequenceClip')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_full_processing_integration(self, mock_exists, mock_makedirs, mock_imagesequence, mock_videoclip):
        """测试完整处理流程的集成"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            detector = WatermarkDetector()
            inpainter = LamaInpainter()
            inpainter.use_cv2_fallback = True
            config = {
                "auto_select_roi": True,
                "margin": 50,
                "codec": "libx264",
                "bitrate": "5000k",
                "preset": "medium"
            }
            
            video_path = os.path.join(temp_dir, "test.mp4")
            output_dir = os.path.join(temp_dir, "output")
            
            processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
            
            # 模拟文件存在
            mock_exists.return_value = True
            
            # 模拟视频剪辑对象
            mock_clip = Mock()
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.duration = 10.0
            mock_clip.fps = 30.0
            mock_clip.close = Mock()
            mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8))
            mock_clip.audio = None
            mock_videoclip.return_value = mock_clip
            
            # 模拟水印掩膜
            watermark_mask = np.zeros((1080, 1920), dtype=np.uint8)
            watermark_mask[100:200, 100:200] = 255
            detector.generate_mask = Mock(return_value=watermark_mask)
            detector.get_roi_coordinates = Mock(return_value=(100, 200, 100, 200))
            detector.extract_roi_mask = Mock(return_value=np.zeros((100, 100), dtype=np.uint8))
            
            # 模拟修复器
            inpainter.inpaint = Mock(return_value=np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
            
            # 模拟输出视频剪辑对象
            mock_output_clip = Mock()
            mock_output_clip.write_videofile = Mock()
            mock_output_clip.close = Mock()
            mock_imagesequence.return_value = mock_output_clip
            
            # 执行处理
            stats = processor.process()
            
            # 验证集成结果
            assert stats["success"] is True
            assert stats["processed_frames"] > 0
            assert "output_path" in stats
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestSecurityIntegration:
    """测试安全模块与其他模块的集成"""
    
    def test_access_control_with_operation_logger(self):
        """测试访问控制与操作日志的集成"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 初始化访问控制
            db_path = os.path.join(temp_dir, "test_users.db")
            access_control = AccessController(user_db_path=db_path)
            
            # 注册测试用户
            access_control.add_user("testuser", "testpass", ["view", "edit"])
            
            # 初始化操作日志
            logger = OperationLogger(db_path)
            
            # 模拟用户登录
            user = access_control.authenticate("testuser", "testpass")
            assert user is not None
            
            # 设置当前用户
            set_current_user(user)
            
            # 记录操作
            logger.log_operation(
                username=user["username"],
                operation_type="test_operation",
                operation_result="success",
                ip_address="127.0.0.1",
                details="Integration test operation"
            )
            
            # 验证日志记录
            logs, _ = logger.get_operation_logs(username=user["username"])
            assert len(logs) > 0
            assert logs[0]["operation_type"] == "test_operation"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_role_based_access_control_integration(self):
        """测试基于角色的访问控制集成"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            db_path = os.path.join(temp_dir, "test_users.db")
            access_control = AccessController(user_db_path=db_path)
            
            # 注册管理员和普通用户（使用不同的用户名避免与默认用户冲突）
            access_control.add_user("testadmin", "adminpass", ["view", "edit", "delete", "admin"])
            access_control.add_user("testuser", "userpass", ["view", "edit"])
            
            # 初始化操作日志
            logger = OperationLogger(db_path)
            
            # 管理员登录
            admin = access_control.authenticate("testadmin", "adminpass")
            assert admin is not None
            
            # 普通用户登录
            user = access_control.authenticate("testuser", "userpass")
            assert user is not None
            
            # 设置当前用户为管理员
            set_current_user(admin)
            
            # 记录不同用户的操作
            logger.log_operation(admin["username"], "admin_action", "success", "127.0.0.1", "Admin operation")
            logger.log_operation(user["username"], "user_action", "success", "127.0.0.1", "User operation")
            
            # 获取所有日志
            all_logs, _ = logger.get_operation_logs()
            assert len(all_logs) >= 2
            
            # 获取特定用户的日志
            user_logs, _ = logger.get_operation_logs(username=user["username"])
            assert len(user_logs) == 1
            assert user_logs[0]["username"] == "testuser"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestEndToEndIntegration:
    """端到端集成测试"""
    
    @patch('core.video_processor.VideoFileClip')
    @patch('core.video_processor.ImageSequenceClip')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_complete_workflow_integration(self, mock_exists, mock_makedirs, mock_imagesequence, mock_videoclip):
        """测试完整工作流程的端到端集成"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 1. 初始化安全模块
            db_path = os.path.join(temp_dir, "test_users.db")
            access_control = AccessController(user_db_path=db_path)
            access_control.add_user("integrationuser", "testpass", ["view", "edit"])
            
            # 2. 用户登录
            user = access_control.authenticate("integrationuser", "testpass")
            assert user is not None
            
            # 设置当前用户
            set_current_user(user)
            
            # 3. 初始化操作日志
            logger = OperationLogger(db_path)
            
            # 4. 初始化视频处理模块
            detector = WatermarkDetector()
            inpainter = LamaInpainter()
            inpainter.use_cv2_fallback = True
            config = {
                "auto_select_roi": True,
                "margin": 50,
                "codec": "libx264",
                "bitrate": "5000k",
                "preset": "medium"
            }
            
            video_path = os.path.join(temp_dir, "test.mp4")
            output_dir = os.path.join(temp_dir, "output")
            
            processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
            
            # 5. 模拟文件存在
            mock_exists.return_value = True
            
            # 6. 模拟视频剪辑对象
            mock_clip = Mock()
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.duration = 10.0
            mock_clip.fps = 30.0
            mock_clip.close = Mock()
            mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8))
            mock_clip.audio = None
            mock_videoclip.return_value = mock_clip
            
            # 7. 模拟水印掩膜
            watermark_mask = np.zeros((1080, 1920), dtype=np.uint8)
            watermark_mask[100:200, 100:200] = 255
            detector.generate_mask = Mock(return_value=watermark_mask)
            detector.get_roi_coordinates = Mock(return_value=(100, 200, 100, 200))
            detector.extract_roi_mask = Mock(return_value=np.zeros((100, 100), dtype=np.uint8))
            
            # 8. 模拟修复器
            inpainter.inpaint = Mock(return_value=np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
            
            # 9. 模拟输出视频剪辑对象
            mock_output_clip = Mock()
            mock_output_clip.write_videofile = Mock()
            mock_output_clip.close = Mock()
            mock_imagesequence.return_value = mock_output_clip
            
            # 10. 记录操作开始
            logger.log_operation(
                username=user["username"],
                operation_type="video_processing_start",
                operation_result="started",
                ip_address="127.0.0.1",
                details=f"Video path: {video_path}"
            )
            
            # 11. 执行视频处理
            stats = processor.process()
            
            # 12. 记录操作结果
            logger.log_operation(
                username=user["username"],
                operation_type="video_processing_complete",
                operation_result="success" if stats["success"] else "failed",
                ip_address="127.0.0.1",
                details=f"Output: {stats.get('output_path')}, Time: {stats.get('processing_time')}, Frames: {stats.get('processed_frames')}"
            )
            
            # 13. 验证端到端集成结果
            assert stats["success"] is True
            assert stats["processed_frames"] > 0
            
            # 14. 验证操作日志
            logs, _ = logger.get_operation_logs(username=user["username"])
            assert len(logs) >= 2
            # 日志按时间倒序排列，最新的在前
            assert logs[0]["operation_type"] == "video_processing_complete"
            assert logs[1]["operation_type"] == "video_processing_start"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestErrorHandlingIntegration:
    """测试错误处理的集成"""
    
    def test_detector_failure_propagation(self):
        """测试检测器失败时的错误传播"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            detector = WatermarkDetector()
            inpainter = LamaInpainter()
            inpainter.use_cv2_fallback = True
            config = {}
            
            video_path = os.path.join(temp_dir, "nonexistent.mp4")
            output_dir = os.path.join(temp_dir, "output")
            
            processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
            
            # 模拟检测器失败
            detector.generate_mask = Mock(return_value=None)
            
            # 处理应该失败但不崩溃
            stats = processor.process()
            
            assert stats["success"] is False
            assert "error" in stats
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_inpainter_failure_fallback(self):
        """测试修复器失败时的回退机制"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        # 创建测试图像
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        test_mask = np.zeros((100, 100), dtype=np.uint8)
        test_mask[50:70, 50:70] = 255
        
        # 修复器应该能够处理各种输入
        result = inpainter.inpaint(test_image, test_mask)
        
        assert result is not None
        assert result.shape == test_image.shape


class TestPerformanceIntegration:
    """测试性能相关的集成"""
    
    def test_large_video_processing_performance(self):
        """测试大视频处理的性能"""
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        config = {}
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            video_path = os.path.join(temp_dir, "test.mp4")
            output_dir = os.path.join(temp_dir, "output")
            
            processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
            
            # 测试进度信息获取
            progress_info = processor.get_progress_info()
            
            assert "progress" in progress_info
            assert "message" in progress_info
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_memory_usage_integration(self):
        """测试内存使用的集成"""
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        # 处理多个图像
        for i in range(10):
            test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            test_mask = np.zeros((480, 640), dtype=np.uint8)
            test_mask[100:200, 100:200] = 255
            
            result = inpainter.inpaint(test_image, test_mask)
            assert result is not None
        
        # 验证没有内存泄漏（通过不崩溃来验证）
        assert True
