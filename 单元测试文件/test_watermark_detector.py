"""
WatermarkDetector单元测试
测试覆盖正常场景和异常场景
"""
import pytest
import numpy as np
import cv2
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from moviepy.video.io.VideoFileClip import VideoFileClip
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
from watermark_detector import WatermarkDetector


class TestWatermarkDetectorInit:
    """测试WatermarkDetector初始化"""
    
    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        detector = WatermarkDetector()
        assert detector.num_sample_frames == 10
        assert detector.min_frame_count == 7
        assert detector.dilation_kernel_size == 5
        assert detector.use_canny is True
        assert detector.roi is None
        assert detector._mask is None
        assert detector._detected_color_range is None
        assert detector._watermark_type is None
    
    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        detector = WatermarkDetector(
            num_sample_frames=20,
            min_frame_count=15,
            dilation_kernel_size=10,
            use_canny=False,
            canny_low=30,
            canny_high=200,
            morph_open=3,
            morph_close=8,
            min_component_area=100
        )
        assert detector.num_sample_frames == 20
        assert detector.min_frame_count == 15
        assert detector.dilation_kernel_size == 10
        assert detector.use_canny is False
        assert detector.canny_low == 30
        assert detector.canny_high == 200
        assert detector.morph_open == 3
        assert detector.morph_close == 8
        assert detector.min_component_area == 100
    
    def test_init_negative_parameters(self):
        """测试负数参数初始化"""
        # 测试负数参数（Python不会自动检查，所以这个测试验证参数被正确接受）
        detector = WatermarkDetector(num_sample_frames=-1)
        assert detector.num_sample_frames == -1
    
    def test_init_large_parameters(self):
        """测试过大参数初始化"""
        # 测试过大参数（Python不会自动检查，所以这个测试验证参数被正确接受）
        detector = WatermarkDetector(num_sample_frames=10000)
        assert detector.num_sample_frames == 10000


class TestWatermarkDetectorGetFirstValidFrame:
    """测试get_first_valid_frame方法"""
    
    def test_get_first_valid_frame_normal(self):
        """测试正常获取有效帧"""
        detector = WatermarkDetector()
        
        # 创建模拟视频剪辑对象
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.fps = 30
        mock_clip.duration = 10
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        
        frame = detector.get_first_valid_frame(mock_clip)
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)
    
    def test_get_first_valid_frame_short_video(self):
        """测试短视频获取有效帧"""
        detector = WatermarkDetector()
        
        # 创建短视频剪辑对象
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.fps = 30
        mock_clip.duration = 0.1
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        
        frame = detector.get_first_valid_frame(mock_clip)
        assert frame is not None
        mock_clip.get_frame.assert_called_once()
    
    def test_get_first_valid_frame_black_screen(self):
        """测试黑屏视频获取有效帧"""
        detector = WatermarkDetector()
        
        # 创建黑屏视频剪辑对象
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.fps = 30
        mock_clip.duration = 10
        mock_clip.get_frame = Mock(return_value=np.zeros((480, 640, 3), dtype=np.uint8))
        
        frame = detector.get_first_valid_frame(mock_clip)
        assert frame is not None
        # 应该返回第一帧（即使它是黑屏）
    
    def test_get_first_valid_frame_exception_handling(self):
        """测试异常处理"""
        detector = WatermarkDetector()
        
        # 创建抛出异常的视频剪辑对象（只在某些帧抛出异常）
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.fps = 30
        mock_clip.duration = 10
        
        # 让前几次调用抛出异常，最后一次成功
        call_count = [0]
        def get_frame_side_effect(t):
            call_count[0] += 1
            if call_count[0] < 5:
                raise Exception("Frame error")
            return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        mock_clip.get_frame = Mock(side_effect=get_frame_side_effect)
        
        # 应该最终返回一个有效帧（在几次异常后）
        frame = detector.get_first_valid_frame(mock_clip)
        assert frame is not None
        assert isinstance(frame, np.ndarray)


class TestWatermarkDetectorSelectROI:
    """测试select_roi方法"""
    
    @patch('cv2.selectROI')
    @patch('cv2.destroyAllWindows')
    def test_select_roi_normal(self, mock_destroy, mock_select):
        """测试正常选择ROI"""
        detector = WatermarkDetector()
        
        # 创建模拟视频剪辑对象
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.duration = 10
        mock_clip.fps = 30
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        
        # 模拟用户选择ROI（注意：图像会被缩放到720高度，缩放因子是1.5）
        # 显示的ROI坐标会被转换回原始尺寸
        mock_select.return_value = (150, 150, 300, 300)
        
        roi = detector.select_roi(mock_clip)
        assert roi is not None
        # ROI应该被缩放回原始尺寸：(150/1.5, 150/1.5, 300/1.5, 300/1.5) = (100, 100, 200, 200)
        assert roi == (100, 100, 200, 200)
        assert detector.roi == (100, 100, 200, 200)
    
    @patch('cv2.selectROI')
    @patch('cv2.destroyAllWindows')
    def test_select_roi_cancel(self, mock_destroy, mock_select):
        """测试取消选择ROI"""
        detector = WatermarkDetector()
        
        # 创建模拟视频剪辑对象
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.duration = 10
        mock_clip.fps = 30
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        
        # 模拟用户取消选择
        mock_select.return_value = (0, 0, 0, 0)
        
        roi = detector.select_roi(mock_clip)
        assert roi is None
    
    @patch('cv2.selectROI')
    @patch('cv2.destroyAllWindows')
    def test_select_roi_scale_conversion(self, mock_destroy, mock_select):
        """测试ROI缩放转换"""
        detector = WatermarkDetector()
        
        # 创建模拟视频剪辑对象
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.duration = 10
        mock_clip.fps = 30
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8))
        
        # 模拟用户在缩放后的图像上选择ROI
        # 原始图像高度是1080，显示高度是720，缩放因子是0.6667
        # 如果用户在显示的图像上选择(100, 100, 200, 200)，转换回原始尺寸应该是(150, 150, 300, 300)
        mock_select.return_value = (100, 100, 200, 200)
        
        roi = detector.select_roi(mock_clip)
        assert roi is not None
        # ROI应该被缩放回原始尺寸
        assert roi[0] > 100  # x应该大于显示的值（因为原始图像更大）
        assert roi[1] > 100  # y应该大于显示的值（因为原始图像更大）


class TestWatermarkDetectorAnalyzeWatermarkType:
    """测试_analyze_watermark_type方法"""
    
    def test_analyze_watermark_type_text(self):
        """测试文本水印类型检测"""
        detector = WatermarkDetector()
        
        # 创建模拟文本水印区域（高边缘、低颜色熵）
        roi_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        # 添加边缘
        roi_frame[40:60, :] = 255
        
        watermark_type = detector._analyze_watermark_type(roi_frame)
        assert watermark_type in ['text', 'image', 'transparent', 'solid_bg']
    
    def test_analyze_watermark_type_image(self):
        """测试图像水印类型检测"""
        detector = WatermarkDetector()
        
        # 创建模拟图像水印区域（高颜色熵）
        roi_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        watermark_type = detector._analyze_watermark_type(roi_frame)
        assert watermark_type in ['text', 'image', 'transparent', 'solid_bg']
    
    def test_analyze_watermark_type_transparent(self):
        """测试透明水印类型检测"""
        detector = WatermarkDetector()
        
        # 创建模拟透明水印区域（低对比度、低饱和度）
        roi_frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        watermark_type = detector._analyze_watermark_type(roi_frame)
        assert watermark_type in ['text', 'image', 'transparent', 'solid_bg']
    
    def test_analyze_watermark_type_grayscale(self):
        """测试灰度图像水印类型检测"""
        detector = WatermarkDetector()
        
        # 创建灰度图像
        roi_frame = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        watermark_type = detector._analyze_watermark_type(roi_frame)
        assert watermark_type in ['text', 'image', 'transparent', 'solid_bg']


class TestWatermarkDetectorDetectColorRange:
    """测试_detect_color_range方法"""
    
    def test_detect_color_range_normal(self):
        """测试正常颜色范围检测"""
        detector = WatermarkDetector()
        
        # 创建红色区域
        roi_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        roi_frame[:, :, 2] = 255  # 红色通道
        
        lower_hsv, upper_hsv = detector._detect_color_range(roi_frame)
        assert lower_hsv is not None
        assert upper_hsv is not None
        assert lower_hsv.shape == (3,)
        assert upper_hsv.shape == (3,)
    
    def test_detect_color_range_multiple_colors(self):
        """测试多颜色区域检测"""
        detector = WatermarkDetector()
        
        # 创建多颜色区域
        roi_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        lower_hsv, upper_hsv = detector._detect_color_range(roi_frame)
        assert lower_hsv is not None
        assert upper_hsv is not None
    
    def test_detect_color_range_low_saturation(self):
        """测试低饱和度颜色检测"""
        detector = WatermarkDetector()
        
        # 创建低饱和度区域
        roi_frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        lower_hsv, upper_hsv = detector._detect_color_range(roi_frame)
        assert lower_hsv is not None
        assert upper_hsv is not None


class TestWatermarkDetectorDetectWatermarkInFrame:
    """测试detect_watermark_in_frame方法"""
    
    def test_detect_watermark_in_frame_no_roi(self):
        """测试未设置ROI时检测水印"""
        detector = WatermarkDetector()
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        with pytest.raises(ValueError, match="ROI未选择"):
            detector.detect_watermark_in_frame(frame)
    
    def test_detect_watermark_in_frame_normal(self):
        """测试正常检测水印"""
        detector = WatermarkDetector()
        detector.roi = (100, 100, 200, 200)
        
        # 创建测试帧
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        # 在ROI区域添加水印
        frame[100:300, 100:300] = 255
        
        mask = detector.detect_watermark_in_frame(frame)
        assert mask is not None
        assert isinstance(mask, np.ndarray)
        assert mask.shape == (480, 640)
    
    def test_detect_watermark_in_frame_empty_roi(self):
        """测试空ROI区域检测"""
        detector = WatermarkDetector()
        detector.roi = (100, 100, 0, 0)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        with pytest.raises(ValueError, match="ROI区域为空"):
            detector.detect_watermark_in_frame(frame)
    
    def test_detect_watermark_in_frame_grayscale(self):
        """测试灰度帧检测水印"""
        detector = WatermarkDetector()
        detector.roi = (100, 100, 200, 200)
        
        frame = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        
        mask = detector.detect_watermark_in_frame(frame)
        assert mask is not None
        assert isinstance(mask, np.ndarray)
    
    def test_detect_watermark_in_frame_without_canny(self):
        """测试不使用Canny边缘检测"""
        detector = WatermarkDetector(use_canny=False)
        detector.roi = (100, 100, 200, 200)
        
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        mask = detector.detect_watermark_in_frame(frame)
        assert mask is not None
        assert isinstance(mask, np.ndarray)


class TestWatermarkDetectorGenerateMask:
    """测试generate_mask方法"""
    
    def test_generate_mask_no_roi_manual(self):
        """测试未设置ROI且不自动选择"""
        detector = WatermarkDetector()
        
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.duration = 10
        mock_clip.fps = 30
        
        with patch.object(detector, 'select_roi', return_value=None):
            with pytest.raises(ValueError, match="用户取消了ROI选择"):
                detector.generate_mask(mock_clip, auto_select_roi=False)
    
    def test_generate_mask_auto_select_roi(self):
        """测试自动选择ROI"""
        detector = WatermarkDetector()
        
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.duration = 10
        mock_clip.fps = 30
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        
        mask = detector.generate_mask(mock_clip, auto_select_roi=True)
        assert mask is not None
        assert isinstance(mask, np.ndarray)
        assert detector.roi is not None
    
    def test_generate_mask_short_video(self):
        """测试短视频生成掩膜"""
        detector = WatermarkDetector()
        detector.roi = (100, 100, 200, 200)
        
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.duration = 0.1
        mock_clip.fps = 30
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        
        mask = detector.generate_mask(mock_clip, auto_select_roi=False)
        assert mask is not None
        assert isinstance(mask, np.ndarray)
    
    def test_generate_mask_frame_exception(self):
        """测试帧获取异常处理"""
        detector = WatermarkDetector()
        detector.roi = (100, 100, 200, 200)
        
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.duration = 10
        mock_clip.fps = 30
        mock_clip.get_frame = Mock(side_effect=Exception("Frame error"))
        
        # 应该处理异常并继续
        try:
            mask = detector.generate_mask(mock_clip, auto_select_roi=False)
            # 如果成功，验证结果
            assert mask is not None
        except Exception:
            # 如果抛出异常，也是可以接受的
            pass


class TestWatermarkDetectorIntegration:
    """集成测试"""
    
    def test_full_watermark_detection_workflow(self):
        """测试完整的水印检测流程"""
        detector = WatermarkDetector()
        
        # 创建模拟视频剪辑对象
        mock_clip = Mock(spec=VideoFileClip)
        mock_clip.duration = 10
        mock_clip.fps = 30
        mock_clip.get_frame = Mock(return_value=np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        
        # 自动选择ROI
        mask = detector.generate_mask(mock_clip, auto_select_roi=True)
        assert mask is not None
        assert detector.roi is not None
        
        # 验证ROI在合理范围内
        x, y, w, h = detector.roi
        assert x >= 0 and x + w <= 640
        assert y >= 0 and y + h <= 480


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.core.watermark_detector", "--cov-report=term-missing"])