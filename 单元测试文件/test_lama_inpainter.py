"""
LamaInpainter单元测试
测试覆盖正常场景和异常场景
"""
import pytest
import numpy as np
import cv2
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
from lama_inpainter import LamaInpainter, LAMA_AVAILABLE


class TestLamaInpainterInit:
    """测试LamaInpainter初始化"""
    
    def test_init_default(self):
        """测试默认初始化"""
        inpainter = LamaInpainter()
        assert inpainter.model is None
        assert inpainter.config is None
        assert inpainter.device == "cpu"
        assert inpainter.initialized is False
        assert inpainter.use_cv2_fallback is True
    
    def test_is_available(self):
        """测试检查Lama是否可用"""
        inpainter = LamaInpainter()
        available = inpainter.is_available()
        assert isinstance(available, bool)


class TestLamaInpainterInitialize:
    """测试initialize方法"""
    
    @patch('lama_inpainter.LAMA_AVAILABLE', True)
    @patch('lama_inpainter.ModelManager')
    @patch('lama_inpainter.Config')
    @patch('lama_inpainter.torch.cuda.is_available')
    def test_initialize_cpu(self, mock_cuda_available, mock_config, mock_model_manager):
        """测试CPU初始化"""
        mock_cuda_available.return_value = False
        mock_model_instance = Mock()
        mock_model_manager.return_value = mock_model_instance
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        inpainter = LamaInpainter()
        inpainter.initialize(device="cpu", ldm_steps=50)
        
        assert inpainter.device == "cpu"
        assert inpainter.initialized is True
        assert inpainter.model is not None
        assert inpainter.config is not None
    
    @patch('lama_inpainter.LAMA_AVAILABLE', True)
    @patch('lama_inpainter.ModelManager')
    @patch('lama_inpainter.Config')
    @patch('lama_inpainter.torch.cuda.is_available')
    def test_initialize_cuda(self, mock_cuda_available, mock_config, mock_model_manager):
        """测试CUDA初始化"""
        mock_cuda_available.return_value = True
        mock_model_instance = Mock()
        mock_model_manager.return_value = mock_model_instance
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        inpainter = LamaInpainter()
        inpainter.initialize(device="cuda", ldm_steps=50)
        
        assert inpainter.device == "cuda"
        assert inpainter.initialized is True
    
    @patch('lama_inpainter.LAMA_AVAILABLE', True)
    @patch('lama_inpainter.ModelManager')
    @patch('lama_inpainter.Config')
    @patch('lama_inpainter.torch.cuda.is_available')
    def test_initialize_cuda_fallback_to_cpu(self, mock_cuda_available, mock_config, mock_model_manager):
        """测试CUDA不可用时回退到CPU"""
        mock_cuda_available.return_value = False
        mock_model_instance = Mock()
        mock_model_manager.return_value = mock_model_instance
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        inpainter = LamaInpainter()
        inpainter.initialize(device="cuda", ldm_steps=50)
        
        assert inpainter.device == "cpu"
        assert inpainter.initialized is True
    
    @patch('lama_inpainter.LAMA_AVAILABLE', False)
    def test_initialize_lama_not_available(self):
        """测试Lama不可用时初始化"""
        inpainter = LamaInpainter()
        
        with pytest.raises(ImportError, match="lama_cleaner未安装"):
            inpainter.initialize(device="cpu")
    
    @patch('lama_inpainter.LAMA_AVAILABLE', True)
    @patch('lama_inpainter.ModelManager')
    @patch('lama_inpainter.Config')
    @patch('lama_inpainter.torch.cuda.is_available')
    def test_initialize_custom_parameters(self, mock_cuda_available, mock_config, mock_model_manager):
        """测试自定义参数初始化"""
        mock_cuda_available.return_value = False
        mock_model_instance = Mock()
        mock_model_manager.return_value = mock_model_instance
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        inpainter = LamaInpainter()
        inpainter.initialize(
            device="cpu",
            ldm_steps=100,
            hd_strategy="CROP",
            hd_strategy_crop_margin=64,
            hd_strategy_crop_trigger_size=4096
        )
        
        assert inpainter.initialized is True
        mock_config.assert_called_once()
    
    @patch('lama_inpainter.LAMA_AVAILABLE', True)
    @patch('lama_inpainter.ModelManager')
    @patch('lama_inpainter.Config')
    @patch('lama_inpainter.torch.cuda.is_available')
    def test_initialize_exception(self, mock_cuda_available, mock_config, mock_model_manager):
        """测试初始化异常"""
        mock_cuda_available.return_value = False
        mock_model_manager.side_effect = Exception("Model initialization failed")
        
        inpainter = LamaInpainter()
        
        with pytest.raises(RuntimeError, match="Lama模型初始化失败"):
            inpainter.initialize(device="cpu")
        
        assert inpainter.initialized is False


class TestLamaInpainterInpaint:
    """测试inpaint方法"""
    
    def test_inpaint_not_initialized_no_fallback(self):
        """测试未初始化且无回退"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = False
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        with pytest.raises(RuntimeError, match="Lama修复器未初始化"):
            inpainter.inpaint(image, mask)
    
    @patch('lama_inpainter.LAMA_AVAILABLE', False)
    def test_inpaint_cv2_fallback(self):
        """测试cv2回退修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        result = inpainter.inpaint(image, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == image.shape
    
    def test_inpaint_bgr_image(self):
        """测试BGR图像修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        result = inpainter.inpaint(image, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == image.shape
    
    def test_inpaint_grayscale_image(self):
        """测试灰度图像修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        image = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        result = inpainter.inpaint(image, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (480, 640, 3)
    
    def test_inpaint_bgra_image(self):
        """测试BGRA图像修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        image = np.random.randint(0, 255, (480, 640, 4), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        result = inpainter.inpaint(image, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (480, 640, 3)
    
    def test_inpaint_rgb_mask(self):
        """测试RGB掩膜修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mask = np.zeros((480, 640, 3), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        result = inpainter.inpaint(image, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
    
    def test_inpaint_empty_mask(self):
        """测试空掩膜修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        
        result = inpainter.inpaint(image, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
    
    def test_inpaint_full_mask(self):
        """测试全掩膜修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mask = np.ones((480, 640), dtype=np.uint8) * 255
        
        result = inpainter.inpaint(image, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
    
    def test_inpaint_with_current_user(self):
        """测试带current_user参数的修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        result = inpainter.inpaint(image, mask, current_user="test_user")
        
        assert result is not None
        assert isinstance(result, np.ndarray)


class TestLamaInpainterPrepareImage:
    """测试_prepare_image方法"""
    
    def test_prepare_image_bgr(self):
        """测试BGR图像预处理"""
        inpainter = LamaInpainter()
        
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = inpainter._prepare_image(image)
        
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.uint8
    
    def test_prepare_image_grayscale(self):
        """测试灰度图像预处理"""
        inpainter = LamaInpainter()
        
        image = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        result = inpainter._prepare_image(image)
        
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.uint8
    
    def test_prepare_image_bgra(self):
        """测试BGRA图像预处理"""
        inpainter = LamaInpainter()
        
        image = np.random.randint(0, 255, (480, 640, 4), dtype=np.uint8)
        result = inpainter._prepare_image(image)
        
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.uint8
    
    def test_prepare_image_single_channel(self):
        """测试单通道图像预处理"""
        inpainter = LamaInpainter()
        
        image = np.random.randint(0, 255, (480, 640, 1), dtype=np.uint8)
        result = inpainter._prepare_image(image)
        
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.uint8
    
    def test_prepare_image_invalid_channels(self):
        """测试无效通道数图像预处理"""
        inpainter = LamaInpainter()
        
        image = np.random.randint(0, 255, (480, 640, 5), dtype=np.uint8)
        
        with pytest.raises(ValueError, match="不支持的图像通道数"):
            inpainter._prepare_image(image)


class TestLamaInpainterPrepareMask:
    """测试_prepare_mask方法"""
    
    def test_prepare_mask_grayscale(self):
        """测试灰度掩膜预处理"""
        inpainter = LamaInpainter()
        
        mask = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        result = inpainter._prepare_mask(mask)
        
        assert result.shape == (480, 640)
        assert result.dtype == np.uint8
        assert np.all(np.isin(result, [0, 255]))
    
    def test_prepare_mask_rgb(self):
        """测试RGB掩膜预处理"""
        inpainter = LamaInpainter()
        
        mask = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = inpainter._prepare_mask(mask)
        
        assert result.shape == (480, 640)
        assert result.dtype == np.uint8
        assert np.all(np.isin(result, [0, 255]))
    
    def test_prepare_mask_single_channel(self):
        """测试单通道掩膜预处理"""
        inpainter = LamaInpainter()
        
        mask = np.random.randint(0, 255, (480, 640, 1), dtype=np.uint8)
        result = inpainter._prepare_mask(mask)
        
        assert result.shape == (480, 640)
        assert result.dtype == np.uint8
        assert np.all(np.isin(result, [0, 255]))
    
    def test_prepare_mask_invalid_dimensions(self):
        """测试无效维度掩膜预处理"""
        inpainter = LamaInpainter()
        
        mask = np.random.randint(0, 255, (480, 640, 3, 2), dtype=np.uint8)
        
        with pytest.raises(ValueError, match="不支持的掩膜维度"):
            inpainter._prepare_mask(mask)
    
    def test_prepare_mask_invalid_channels(self):
        """测试无效通道数掩膜预处理"""
        inpainter = LamaInpainter()
        
        mask = np.random.randint(0, 255, (480, 640, 5), dtype=np.uint8)
        
        with pytest.raises(ValueError, match="不支持的掩膜通道数"):
            inpainter._prepare_mask(mask)


class TestLamaInpainterPostprocessResult:
    """测试_postprocess_result方法"""
    
    def test_postprocess_result_float_0_1(self):
        """测试0-1范围浮点结果后处理"""
        inpainter = LamaInpainter()
        
        result = np.random.rand(480, 640, 3).astype(np.float32)
        original_shape = (480, 640, 3)
        
        processed = inpainter._postprocess_result(result, original_shape)
        
        assert processed.shape == original_shape
        assert processed.dtype == np.uint8
    
    def test_postprocess_result_float_0_255(self):
        """测试0-255范围浮点结果后处理"""
        inpainter = LamaInpainter()
        
        result = np.random.rand(480, 640, 3).astype(np.float32) * 255
        original_shape = (480, 640, 3)
        
        processed = inpainter._postprocess_result(result, original_shape)
        
        assert processed.shape == original_shape
        assert processed.dtype == np.uint8
    
    def test_postprocess_result_uint8(self):
        """测试uint8结果后处理"""
        inpainter = LamaInpainter()
        
        result = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        original_shape = (480, 640, 3)
        
        processed = inpainter._postprocess_result(result, original_shape)
        
        assert processed.shape == original_shape
        assert processed.dtype == np.uint8
    
    def test_postprocess_result_resize(self):
        """测试尺寸调整后处理"""
        inpainter = LamaInpainter()
        
        result = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        original_shape = (480, 640, 3)
        
        processed = inpainter._postprocess_result(result, original_shape)
        
        assert processed.shape == original_shape
        assert processed.dtype == np.uint8
    
    def test_postprocess_result_single_channel(self):
        """测试单通道结果后处理"""
        inpainter = LamaInpainter()
        
        result = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        original_shape = (480, 640)
        
        processed = inpainter._postprocess_result(result, original_shape)
        
        assert processed.shape == original_shape
        assert processed.dtype == np.uint8


class TestLamaInpainterBatchInpaint:
    """测试batch_inpaint方法"""
    
    def test_batch_inpaint_normal(self):
        """测试正常批量修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]
        masks = [np.zeros((480, 640), dtype=np.uint8) for _ in range(3)]
        for mask in masks:
            mask[100:200, 100:200] = 255
        
        results = inpainter.batch_inpaint(images, masks)
        
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert isinstance(result, np.ndarray)
    
    def test_batch_inpaint_mismatch(self):
        """测试图像和掩膜数量不匹配"""
        inpainter = LamaInpainter()
        
        images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]
        masks = [np.zeros((480, 640), dtype=np.uint8) for _ in range(2)]
        
        with pytest.raises(ValueError, match="图像和掩膜数量不匹配"):
            inpainter.batch_inpaint(images, masks)
    
    def test_batch_inpaint_with_current_user(self):
        """测试带current_user参数的批量修复"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(2)]
        masks = [np.zeros((480, 640), dtype=np.uint8) for _ in range(2)]
        for mask in masks:
            mask[100:200, 100:200] = 255
        
        results = inpainter.batch_inpaint(images, masks, current_user="test_user")
        
        assert len(results) == 2
    
    def test_batch_inpaint_exception_handling(self):
        """测试批量修复异常处理"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        ]
        masks = [np.zeros((480, 640), dtype=np.uint8) for _ in range(3)]
        
        # 模拟一个图像修复失败
        with patch.object(inpainter, 'inpaint', side_effect=[images[0], Exception("Error"), images[2]]):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                results = inpainter.batch_inpaint(images, masks)
                
                assert len(results) == 3
                assert len(w) > 0


class TestLamaInpainterGetDeviceInfo:
    """测试get_device_info方法"""
    
    def test_get_device_info_cpu(self):
        """测试CPU设备信息"""
        inpainter = LamaInpainter()
        inpainter.device = "cpu"
        inpainter.initialized = False
        
        info = inpainter.get_device_info()
        
        assert info["device"] == "cpu"
        assert info["initialized"] is False
        assert isinstance(info["lama_available"], bool)
    
    def test_get_device_info_initialized(self):
        """测试已初始化设备信息"""
        inpainter = LamaInpainter()
        inpainter.device = "cpu"
        inpainter.initialized = True
        
        info = inpainter.get_device_info()
        
        assert info["device"] == "cpu"
        assert info["initialized"] is True


class TestLamaInpainterClearCache:
    """测试clear_cache方法"""
    
    @patch('lama_inpainter.torch.cuda.is_available')
    @patch('lama_inpainter.torch.cuda.empty_cache')
    def test_clear_cache_cuda(self, mock_empty_cache, mock_cuda_available):
        """测试CUDA缓存清除"""
        mock_cuda_available.return_value = True
        
        inpainter = LamaInpainter()
        inpainter.device = "cuda"
        inpainter.clear_cache()
        
        mock_empty_cache.assert_called_once()
    
    @patch('lama_inpainter.torch.cuda.is_available')
    def test_clear_cache_cpu(self, mock_cuda_available):
        """测试CPU缓存清除"""
        mock_cuda_available.return_value = False
        
        inpainter = LamaInpainter()
        inpainter.device = "cpu"
        inpainter.clear_cache()
        
        # 不应该抛出异常


class TestLamaInpainterIntegration:
    """集成测试"""
    
    def test_full_inpaint_workflow(self):
        """测试完整修复流程"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        # 创建测试图像和掩膜
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100:200, 100:200] = 255
        
        # 修复图像
        result = inpainter.inpaint(image, mask)
        
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == image.shape
    
    def test_batch_workflow(self):
        """测试批量处理流程"""
        inpainter = LamaInpainter()
        inpainter.use_cv2_fallback = True
        
        # 创建多个测试图像和掩膜
        images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]
        masks = [np.zeros((480, 640), dtype=np.uint8) for _ in range(5)]
        for mask in masks:
            mask[100:200, 100:200] = 255
        
        # 批量修复
        results = inpainter.batch_inpaint(images, masks)
        
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.shape == images[0].shape


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.core.lama_inpainter", "--cov-report=term-missing"])