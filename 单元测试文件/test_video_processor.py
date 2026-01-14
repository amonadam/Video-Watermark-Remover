"""
视频处理器单元测试
"""
import os
import sys
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any
import tempfile
import shutil

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.video_processor import VideoProcessor
from core.watermark_detector import WatermarkDetector
from core.lama_inpainter import LamaInpainter


class TestVideoProcessorInit:
    """测试VideoProcessor初始化"""
    
    def test_init_normal(self):
        """测试正常初始化"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {"auto_select_roi": True, "margin": 50}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        assert processor.video_path == video_path
        assert processor.output_dir == output_dir
        assert processor.detector == detector
        assert processor.inpainter == inpainter
        assert processor.config == config
        assert processor.video_clip is None
        assert processor.watermark_mask is None
        assert processor.roi_coords is None
        assert processor.roi_mask is None
        assert processor.stats["start_time"] == 0
        assert processor.stats["end_time"] == 0
        assert processor.stats["total_frames"] == 0
        assert processor.stats["processed_frames"] == 0
        assert processor.stats["failed_frames"] == 0
    
    def test_init_empty_config(self):
        """测试空配置初始化"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        assert processor.config == {}
    
    def test_init_with_complex_config(self):
        """测试复杂配置初始化"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {
            "auto_select_roi": False,
            "margin": 100,
            "codec": "libx264",
            "bitrate": "8000k",
            "preset": "slow"
        }
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        assert processor.config == config


class TestVideoProcessorGetVideoInfo:
    """测试获取视频信息"""
    
    def test_get_video_info_normal(self):
        """测试正常获取视频信息"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟视频剪辑对象
        mock_clip = Mock()
        mock_clip.w = 1920
        mock_clip.h = 1080
        mock_clip.duration = 10.5
        mock_clip.fps = 30.0
        processor.video_clip = mock_clip
        
        info = processor._get_video_info()
        
        assert info["filename"] == "test.mp4"
        assert info["filepath"] == video_path
        assert info["resolution"] == "1920x1080"
        assert info["duration"] == "10.50秒"
        assert info["total_frames"] == int(10.5 * 30.0)
        assert info["fps"] == "30.00"
        assert info["codec"] == "未知"
        assert info["format"] == "MP4"
    
    def test_get_video_info_no_clip(self):
        """测试无视频剪辑对象时获取信息"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        info = processor._get_video_info()
        
        assert info == {}
    
    def test_get_video_info_different_formats(self):
        """测试不同视频格式"""
        formats = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"]
        expected = ["MP4", "AVI", "MOV", "MKV", "FLV", "WMV"]
        
        for ext, expected_format in zip(formats, expected):
            video_path = f"test{ext}"
            output_dir = "output"
            detector = WatermarkDetector()
            inpainter = LamaInpainter()
            config = {}
            
            processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
            
            # 模拟视频剪辑对象
            mock_clip = Mock()
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.duration = 10.0
            mock_clip.fps = 30.0
            processor.video_clip = mock_clip
            
            info = processor._get_video_info()
            
            assert info["format"] == expected_format


class TestVideoProcessorGetFileSize:
    """测试获取文件大小"""
    
    def test_get_file_size_bytes(self):
        """测试获取字节大小"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟小文件
        with patch('os.path.getsize', return_value=500):
            size = processor._get_file_size(video_path)
            assert size == "500.00 B"
        
        # 模拟KB文件
        with patch('os.path.getsize', return_value=2048):
            size = processor._get_file_size(video_path)
            assert size == "2.00 KB"
        
        # 模拟MB文件
        with patch('os.path.getsize', return_value=2097152):
            size = processor._get_file_size(video_path)
            assert size == "2.00 MB"
        
        # 模拟GB文件
        with patch('os.path.getsize', return_value=2147483648):
            size = processor._get_file_size(video_path)
            assert size == "2.00 GB"
    
    def test_get_file_size_error(self):
        """测试获取文件大小出错"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟文件不存在
        with patch('os.path.getsize', side_effect=OSError("File not found")):
            size = processor._get_file_size(video_path)
            assert size == "未知"


class TestVideoProcessorGetVideoFormat:
    """测试获取视频格式"""
    
    def test_get_video_format_normal(self):
        """测试正常获取视频格式"""
        formats = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"]
        expected = ["MP4", "AVI", "MOV", "MKV", "FLV", "WMV"]
        
        for ext, expected_format in zip(formats, expected):
            video_path = f"test{ext}"
            output_dir = "output"
            detector = WatermarkDetector()
            inpainter = LamaInpainter()
            config = {}
            
            processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
            
            format_result = processor._get_video_format()
            assert format_result == expected_format
    
    def test_get_video_format_unknown(self):
        """测试未知格式"""
        video_path = "test.xyz"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        format_result = processor._get_video_format()
        assert format_result == "未知"


class TestVideoProcessorMatchColors:
    """测试颜色校正"""
    
    def test_match_colors_normal(self):
        """测试正常颜色校正"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 创建测试图像
        source = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        target = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[50:70, 50:70] = 255  # 水印区域
        
        result = processor._match_colors(source, target, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == source.shape
        assert result.dtype == np.uint8
    
    def test_match_colors_small_background(self):
        """测试背景区域太小"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 创建测试图像，背景区域很小
        source = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        target = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mask = np.ones((100, 100), dtype=np.uint8) * 255  # 全是水印
        
        result = processor._match_colors(source, target, mask)
        
        # 背景区域太小，应该返回原图
        assert np.array_equal(result, source)
    
    def test_match_colors_error_handling(self):
        """测试错误处理"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 创建无效的输入
        source = np.array([[[1]]], dtype=np.uint8)
        target = np.array([[[1]]], dtype=np.uint8)
        mask = np.array([[0]], dtype=np.uint8)
        
        # 应该返回原图而不抛出异常
        result = processor._match_colors(source, target, mask)
        assert result is not None


class TestVideoProcessorGetProgressInfo:
    """测试获取处理进度信息"""
    
    def test_get_progress_info_not_started(self):
        """测试未开始时的进度信息"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        progress_info = processor.get_progress_info()
        
        assert progress_info["progress"] == 0.0
        assert progress_info["message"] == "等待开始"
    
    def test_get_progress_info_in_progress(self):
        """测试处理中的进度信息"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        processor.stats["start_time"] = 100.0
        processor.stats["total_frames"] = 100
        processor.stats["processed_frames"] = 50
        processor.stats["failed_frames"] = 2
        
        progress_info = processor.get_progress_info()
        
        assert progress_info["progress"] == 50.0
        assert progress_info["processed_frames"] == 50
        assert progress_info["total_frames"] == 100
        assert progress_info["failed_frames"] == 2
        assert "elapsed_time" in progress_info
        assert "remaining_time" in progress_info
    
    def test_get_progress_info_completed(self):
        """测试完成时的进度信息"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        processor.stats["start_time"] = 100.0
        processor.stats["total_frames"] = 100
        processor.stats["processed_frames"] = 100
        processor.stats["failed_frames"] = 0
        
        progress_info = processor.get_progress_info()
        
        assert progress_info["progress"] == 100.0
        assert progress_info["processed_frames"] == 100
        assert progress_info["total_frames"] == 100
        assert progress_info["failed_frames"] == 0


class TestVideoProcessorCleanup:
    """测试清理资源"""
    
    def test_cleanup_normal(self):
        """测试正常清理"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟视频剪辑对象
        mock_clip = Mock()
        mock_clip.close = Mock()
        processor.video_clip = mock_clip
        
        # 模拟修复器
        mock_inpainter = Mock()
        mock_inpainter.clear_cache = Mock()
        processor.inpainter = mock_inpainter
        
        processor._cleanup()
        
        assert processor.video_clip is None
        mock_clip.close.assert_called_once()
        mock_inpainter.clear_cache.assert_called_once()
    
    def test_cleanup_no_clip(self):
        """测试无视频剪辑对象时的清理"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 不设置video_clip
        processor._cleanup()
        
        assert processor.video_clip is None
    
    def test_cleanup_exception_handling(self):
        """测试清理时的异常处理"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟视频剪辑对象，close方法抛出异常
        mock_clip = Mock()
        mock_clip.close = Mock(side_effect=Exception("Close error"))
        processor.video_clip = mock_clip
        
        # 应该不抛出异常
        processor._cleanup()
        
        assert processor.video_clip is None


class TestVideoProcessorPreviewFrame:
    """测试预览帧"""
    
    def test_preview_frame_no_clip(self):
        """测试无视频剪辑对象时预览"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        original, processed = processor.preview_frame(0)
        
        assert original is None
        assert processed is None
    
    @patch('cv2.cvtColor')
    def test_preview_frame_normal(self, mock_cvtcolor):
        """测试正常预览帧"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟视频剪辑对象
        mock_clip = Mock()
        mock_clip.duration = 10.0
        mock_clip.fps = 30.0
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        processor.video_clip = mock_clip
        
        # 模拟水印掩膜
        processor.watermark_mask = np.zeros((480, 640), dtype=np.uint8)
        processor.watermark_mask[100:200, 100:200] = 255
        processor.roi_coords = (100, 200, 100, 200)
        processor.roi_mask = np.zeros((100, 100), dtype=np.uint8)
        processor.roi_mask[50:70, 50:70] = 255
        
        # 模拟修复器
        mock_inpainter = Mock()
        mock_inpainter.inpaint = Mock(return_value=np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        processor.inpainter = mock_inpainter
        
        # 模拟颜色转换
        mock_cvtcolor.side_effect = lambda x, y: x
        
        original, processed = processor.preview_frame(0)
        
        assert original is not None
        assert processed is not None
        assert isinstance(original, np.ndarray)
        assert isinstance(processed, np.ndarray)
    
    @patch('cv2.cvtColor')
    def test_preview_frame_error_handling(self, mock_cvtcolor):
        """测试预览帧时的错误处理"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟视频剪辑对象
        mock_clip = Mock()
        mock_clip.duration = 10.0
        mock_clip.fps = 30.0
        mock_clip.get_frame = Mock(side_effect=Exception("Frame error"))
        processor.video_clip = mock_clip
        
        # 模拟颜色转换
        mock_cvtcolor.side_effect = lambda x, y: x
        
        # 应该返回None而不抛出异常
        original, processed = processor.preview_frame(0)
        
        assert original is None
        assert processed is None


class TestVideoProcessorProcess:
    """测试处理视频主流程"""
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_process_file_not_found(self, mock_exists, mock_makedirs):
        """测试文件不存在"""
        video_path = "nonexistent.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟文件不存在
        mock_exists.return_value = False
        
        stats = processor.process()
        
        assert stats["success"] is False
        assert "error" in stats
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('core.video_processor.VideoFileClip')
    def test_process_mask_generation_failed(self, mock_videoclip, mock_exists, mock_makedirs):
        """测试水印掩膜生成失败"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {}
        
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
        mock_videoclip.return_value = mock_clip
        
        # 模拟水印掩膜生成失败
        detector.generate_mask = Mock(return_value=None)
        
        stats = processor.process()
        
        assert stats["success"] is False
        assert "error" in stats
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('core.video_processor.ImageSequenceClip')
    @patch('core.video_processor.VideoFileClip')
    @patch('time.strftime')
    def test_process_normal(self, mock_strftime, mock_videoclip, mock_imagesequence, mock_exists, mock_makedirs):
        """测试正常处理视频"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {"codec": "libx264", "bitrate": "5000k", "preset": "medium"}
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟文件存在
        mock_exists.return_value = True
        
        # 模拟时间戳
        mock_strftime.return_value = "20240101_120000"
        
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
        
        stats = processor.process()
        
        assert stats["success"] is True
        assert stats["processed_frames"] > 0
        assert "output_path" in stats
        assert "processing_time" in stats


class TestVideoProcessorIntegration:
    """测试视频处理器集成"""
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('core.video_processor.ImageSequenceClip')
    @patch('core.video_processor.VideoFileClip')
    @patch('time.strftime')
    def test_full_processing_workflow(self, mock_strftime, mock_videoclip, mock_imagesequence, mock_exists, mock_makedirs):
        """测试完整处理流程"""
        video_path = "test.mp4"
        output_dir = "output"
        detector = WatermarkDetector()
        inpainter = LamaInpainter()
        config = {
            "auto_select_roi": True,
            "margin": 50,
            "codec": "libx264",
            "bitrate": "5000k",
            "preset": "medium"
        }
        
        processor = VideoProcessor(video_path, output_dir, detector, inpainter, config)
        
        # 模拟文件存在
        mock_exists.return_value = True
        
        # 模拟时间戳
        mock_strftime.return_value = "20240101_120000"
        
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
        
        # 验证结果
        assert stats["success"] is True
        assert stats["processed_frames"] == int(10.0 * 30.0)  # 300帧
        assert stats["failed_frames"] == 0
        assert stats["total_frames"] == int(10.0 * 30.0)
        assert "output_path" in stats
        assert "processing_time" in stats
        assert stats["video_info"]["filename"] == "test.mp4"
        assert stats["video_info"]["resolution"] == "1920x1080"
        assert stats["video_info"]["duration"] == "10.00秒"
        assert stats["video_info"]["fps"] == "30.00"
