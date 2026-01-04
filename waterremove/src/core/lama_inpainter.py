"""
Lama图像修复器
"""
import torch
import numpy as np
import cv2
from typing import Optional, Union, Dict, Any
import warnings

try:
    from lama_cleaner.model_manager import ModelManager
    from lama_cleaner.schema import Config, HDStrategy
    LAMA_AVAILABLE = True
except ImportError:
    LAMA_AVAILABLE = False
    warnings.warn("lama_cleaner未安装，部分功能将不可用")

class LamaInpainter:
    """Lama图像修复器"""
    
    def __init__(self):
        self.model: Optional[ModelManager] = None
        self.config: Optional[Config] = None
        self.device: str = "cpu"
        self.initialized: bool = False
        self.use_cv2_fallback: bool = True
    
    def is_available(self) -> bool:
        """检查Lama是否可用"""
        return LAMA_AVAILABLE
    
    def initialize(self, device: str = "cpu", ldm_steps: int = 50, 
                   hd_strategy: str = "ORIGINAL", **kwargs):
        """
        初始化Lama模型
        
        Args:
            device: 设备类型 ('cpu' 或 'cuda')
            ldm_steps: LDM步数
            hd_strategy: 高清策略 ('ORIGINAL', 'CROP', 'RESIZE')
            **kwargs: 其他配置参数
        """
        if not LAMA_AVAILABLE:
            raise ImportError("lama_cleaner未安装，请先安装: pip install lama_cleaner")
        
        try:
            # 设置设备
            if device == "cuda" and not torch.cuda.is_available():
                warnings.warn("CUDA不可用，将使用CPU")
                device = "cpu"
            
            self.device = device
            
            # 初始化模型管理器
            self.model = ModelManager(name="lama", device=device)
            
            # 映射高清策略
            hd_strategy_map = {
                "ORIGINAL": HDStrategy.ORIGINAL,
                "CROP": HDStrategy.CROP,
                "RESIZE": HDStrategy.RESIZE
            }
            
            strategy = hd_strategy_map.get(hd_strategy.upper(), HDStrategy.ORIGINAL)
            
            # 创建配置
            config_params = {
                "ldm_steps": ldm_steps,
                "hd_strategy": strategy,
                "hd_strategy_crop_margin": kwargs.get("hd_strategy_crop_margin", 32),
                "hd_strategy_crop_trigger_size": kwargs.get("hd_strategy_crop_trigger_size", 2048),
                "hd_strategy_resize_limit": kwargs.get("hd_strategy_resize_limit", 2048),
            }
            
            # 添加可选参数
            optional_params = [
                "ldm_sampler", "zits_wireframe", "hd_strategy_erase_restore",
                "prompt", "negative_prompt", "use_croper", "croper_width",
                "croper_height", "sd_scale", "sd_strength", "sd_steps",
                "sd_guidance_scale", "sd_seed", "sd_match_histograms",
                "cv2_flag", "cv2_radius", "paint_by_example_steps",
                "paint_by_example_guidance_scale", "paint_by_example_mask_blur",
                "paint_by_example_seed", "paint_by_example_match_histograms"
            ]
            
            for param in optional_params:
                if param in kwargs:
                    config_params[param] = kwargs[param]
            
            self.config = Config(**config_params)
            self.initialized = True
            
            print(f"Lama修复器已初始化，设备: {device}, LDM步数: {ldm_steps}, 策略: {hd_strategy}")
            
        except Exception as e:
            self.initialized = False
            raise RuntimeError(f"Lama模型初始化失败: {e}")
    
    def inpaint(self, image: np.ndarray, mask: np.ndarray, current_user=None) -> np.ndarray:
        """
        图像修复
        
        Args:
            image: 输入图像 (BGR格式)
            mask: 掩膜 (单通道，0-255)
            current_user: 保留参数以保持兼容性
            
        Returns:
            修复后的图像 (BGR格式)
        """
        if not self.initialized and not self.use_cv2_fallback:
            raise RuntimeError("Lama修复器未初始化，请先调用initialize()方法，或启用cv2回退")
        
        # If lama isn't available or model not initialized, fallback to cv2.inpaint
        if (self.model is None or self.config is None) and not self.use_cv2_fallback:
            raise RuntimeError("Lama模型或配置未正确初始化")
        
        try:
            # 预处理输入
            image_prepared = self._prepare_image(image)
            mask_prepared = self._prepare_mask(mask)
            
            # 尝试使用 Lama 进行修复
            try:
                if self.model is not None and self.config is not None:
                    result_rgb = self.model(image_prepared, mask_prepared, self.config)
                    # 后处理结果
                    result_bgr = self._postprocess_result(result_rgb, image.shape)
                    return result_bgr
            except Exception as e_model:
                # 如果 Lama 模型失败，记录警告并回退到 cv2
                warnings.warn(f"Lama模型修复失败，尝试cv2回退: {e_model}")

            # 如果 lama 不可用或失败，使用 OpenCV 的 inpaint 作为回退方案
            if self.use_cv2_fallback:
                try:
                    mask_bin = self._prepare_mask(mask)
                    
                    # 自适应修复半径
                    # 根据水印区域的大小调整修复半径
                    mask_area = np.sum(mask_bin > 0)
                    if mask_area > 0:
                        # 小区域使用小半径，大区域使用大半径
                        adaptive_radius = min(15, max(3, int(np.sqrt(mask_area) / 50)))
                    else:
                        adaptive_radius = 3
                    
                    # 先使用TELEA算法进行初步修复
                    inpaint_telea = cv2.inpaint(image, mask_bin, adaptive_radius, cv2.INPAINT_TELEA)
                    
                    # 对修复边缘进行平滑处理
                    # 创建边缘检测掩码
                    edge_mask = cv2.Canny(mask_bin, 100, 200)
                    edge_dilated = cv2.dilate(edge_mask, np.ones((3, 3), np.uint8), iterations=1)
                    
                    # 在边缘区域使用NS算法进行二次修复，获得更好的结构连续性
                    if np.sum(edge_dilated) > 0:
                        inpaint_ns = cv2.inpaint(image, mask_bin, adaptive_radius, cv2.INPAINT_NS)
                        # 融合两种修复结果，边缘区域使用NS结果，其他区域使用TELEA结果
                        result = inpaint_telea.copy()
                        result[edge_dilated > 0] = inpaint_ns[edge_dilated > 0]
                    else:
                        result = inpaint_telea
                    
                    return result
                except Exception as e_cv2:
                    raise RuntimeError(f"cv2回退修复也失败: {e_cv2}")
            
        except Exception as e:
            raise RuntimeError(f"图像修复失败: {e}")
    
    def _prepare_image(self, image: np.ndarray) -> np.ndarray:
        """预处理图像"""
        # 确保图像是3通道RGB
        if len(image.shape) == 2:
            # 灰度图转RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 1:
            # 单通道转RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 3:
            # BGR转RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif image.shape[2] == 4:
            # BGRA转RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            raise ValueError(f"不支持的图像通道数: {image.shape[2]}")
        
        return image_rgb
    
    def _prepare_mask(self, mask: np.ndarray) -> np.ndarray:
        """预处理掩膜"""
        if len(mask.shape) not in [2, 3]:
            raise ValueError(f"不支持的掩膜维度: {mask.shape}")
        
        # 转换为单通道
        if len(mask.shape) == 3:
            if mask.shape[2] == 3:
                # RGB转灰度
                mask_gray = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
            elif mask.shape[2] == 1:
                # 已经是单通道
                mask_gray = mask[:, :, 0]
            else:
                raise ValueError(f"不支持的掩膜通道数: {mask.shape[2]}")
        else:
            mask_gray = mask
        
        # 二值化
        mask_binary = np.where(mask_gray > 127, 255, 0).astype(np.uint8)
        
        return mask_binary
    
    def _postprocess_result(self, result: np.ndarray, original_shape: tuple) -> np.ndarray:
        """后处理修复结果"""
        # 处理数据类型
        if result.dtype == np.float32 or result.dtype == np.float64:
            if np.max(result) <= 1.0:
                result = (result * 255).astype(np.uint8)
            else:
                result = result.astype(np.uint8)
        
        # 确保结果尺寸与原始图像匹配
        if result.shape[:2] != original_shape[:2]:
            result = cv2.resize(result, (original_shape[1], original_shape[0]))
        
        # RGB转BGR
        if result.shape[2] == 3:
            result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        else:
            result_bgr = result
        
        return result_bgr
    
    def batch_inpaint(self, images: list, masks: list, current_user=None) -> list:
        """
        批量图像修复
        
        Args:
            images: 图像列表
            masks: 掩膜列表
            current_user: 保留参数以保持兼容性
            
        Returns:
            修复后的图像列表
        """
        
        if len(images) != len(masks):
            raise ValueError("图像和掩膜数量不匹配")
        
        results = []
        for i, (image, mask) in enumerate(zip(images, masks)):
            try:
                result = self.inpaint(image, mask, current_user)
                results.append(result)
                print(f"已处理图像 {i+1}/{len(images)}")
            except Exception as e:
                warnings.warn(f"处理图像 {i+1} 时出错: {e}")
                # 如果出错，返回原始图像
                results.append(image)
        
        return results
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        info = {
            "device": self.device,
            "initialized": self.initialized,
            "lama_available": LAMA_AVAILABLE
        }
        
        if self.device == "cuda" and torch.cuda.is_available():
            info.update({
                "cuda_device_name": torch.cuda.get_device_name(0),
                "cuda_device_count": torch.cuda.device_count(),
                "cuda_memory_allocated": torch.cuda.memory_allocated(0) / 1024**2,  # MB
                "cuda_memory_reserved": torch.cuda.memory_reserved(0) / 1024**2  # MB
            })
        
        return info
    
    def clear_cache(self):
        """清除缓存"""
        if hasattr(self, 'device') and self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("GPU缓存已清除")
    
    def __del__(self):
        """析构函数"""
        self.clear_cache()