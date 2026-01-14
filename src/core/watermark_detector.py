"""
水印检测器模块
"""
import cv2
import numpy as np
from moviepy import VideoFileClip
import warnings
from typing import Tuple, Optional, List

class WatermarkDetector:
    """水印检测器类"""
    
    def __init__(self, num_sample_frames: int = 10, min_frame_count: int = 7, 
                 dilation_kernel_size: int = 5,
                 use_canny: bool = True,
                 canny_low: int = 50,
                 canny_high: int = 150,
                 canny_ratio: float = 3.0,
                 adaptive_canny: bool = True,
                 morph_open: int = 2,
                 morph_close: int = 5,
                 min_component_area: int = 50,
                 use_color_segmentation: bool = True,
                 color_lower_hsv: Tuple[int, int, int] = (0, 50, 50),
                 color_upper_hsv: Tuple[int, int, int] = (180, 255, 255),
                 auto_detect_color: bool = True):
        """
        初始化水印检测器
        
        Args:
            num_sample_frames: 采样帧数
            min_frame_count: 水印出现的最小帧数
            dilation_kernel_size: 膨胀核大小
            auto_detect_color: 是否自动检测水印颜色
        """
        self.num_sample_frames = num_sample_frames
        self.min_frame_count = min_frame_count
        self.dilation_kernel_size = dilation_kernel_size
        self.use_canny = use_canny
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.canny_ratio = canny_ratio
        self.adaptive_canny = adaptive_canny
        self.morph_open = morph_open
        self.morph_close = morph_close
        self.min_component_area = min_component_area
        self.use_color_segmentation = use_color_segmentation
        self.color_lower_hsv = np.array(color_lower_hsv, dtype=np.uint8)
        self.color_upper_hsv = np.array(color_upper_hsv, dtype=np.uint8)
        self.auto_detect_color = auto_detect_color
        self._detected_color_range = None  # 存储自动检测到的颜色范围
        self._watermark_type = None  # 存储检测到的水印类型
        self.roi: Optional[Tuple[int, int, int, int]] = None
        self._mask: Optional[np.ndarray] = None
        
        # 不同水印类型的参数配置
        self._type_params = {
            'text': {
                'canny_low': 40,
                'canny_high': 120,
                'morph_open': 1,
                'morph_close': 3,
                'min_component_area': 20,
                'use_canny': True
            },
            'image': {
                'canny_low': 60,
                'canny_high': 180,
                'morph_open': 2,
                'morph_close': 7,
                'min_component_area': 100,
                'use_canny': True
            },
            'transparent': {
                'canny_low': 30,
                'canny_high': 90,
                'morph_open': 1,
                'morph_close': 5,
                'min_component_area': 30,
                'use_canny': True,
                'use_color_segmentation': False
            },
            'solid_bg': {
                'canny_low': 50,
                'canny_high': 150,
                'morph_open': 3,
                'morph_close': 5,
                'min_component_area': 50,
                'use_canny': False
            }
        }
    
    def get_first_valid_frame(self, video_clip: VideoFileClip, threshold: float = 10.0) -> np.ndarray:
        """
        获取第一个有效帧（非黑屏帧）
        
        Args:
            video_clip: 视频剪辑对象
            threshold: 亮度阈值
            
        Returns:
            第一个有效帧
        """
        total_frames = int(video_clip.fps * video_clip.duration)
        
        # 如果视频很短，直接返回第一帧
        if total_frames <= self.num_sample_frames:
            return video_clip.get_frame(0)
        
        frame_indices = [
            int(i * total_frames / self.num_sample_frames) 
            for i in range(self.num_sample_frames)
        ]
        
        for idx in frame_indices:
            try:
                frame = video_clip.get_frame(idx / video_clip.fps)
                # 计算帧的平均亮度
                if len(frame.shape) == 3:
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                else:
                    gray_frame = frame
                
                if gray_frame.mean() > threshold:
                    return frame
            except Exception as e:
                warnings.warn(f"Error getting frame {idx}: {e}")
                continue
        
        # 如果所有采样帧都是黑屏，返回第一帧
        return video_clip.get_frame(0)
    
    def select_roi(self, video_clip: VideoFileClip, window_name: str = "Select Watermark Area") -> Optional[Tuple[int, int, int, int]]:
        """
        手动选择水印区域
        
        Args:
            video_clip: 视频剪辑对象
            window_name: 窗口名称
            
        Returns:
            ROI坐标 (x, y, width, height) 或 None（如果取消）
        """
        frame = self.get_first_valid_frame(video_clip)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # 调整显示大小
        display_height = 720
        scale_factor = display_height / frame.shape[0]
        display_width = int(frame.shape[1] * scale_factor)
        display_frame = cv2.resize(frame, (display_width, display_height))
        
        # 添加操作说明
        instructions = [
            "选择水印区域:",
            "1. 用鼠标拖拽选择矩形区域",
            "2. 按SPACE或ENTER确认选择",
            "3. 按ESC取消选择"
        ]
        
        try:
            # 使用PIL绘制中文文本
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            
            # 转换为PIL图像
            pil_image = Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)
            
            # 尝试加载中文字体
            font_path = "C:\Windows\Fonts\simhei.ttf"
            try:
                font = ImageFont.truetype(font_path, 20)
            except IOError:
                # 如果字体文件不存在，使用默认字体
                font = ImageFont.load_default()
            
            # 绘制文本
            for i, line in enumerate(instructions):
                # 绘制白色背景
                draw.text((10, 30 + i * 30), line, font=font, fill=(255, 255, 255), stroke_width=2)
                # 绘制红色文字
                draw.text((10, 30 + i * 30), line, font=font, fill=(255, 0, 0), stroke_width=0)
            
            # 转换回OpenCV图像
            display_frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except ImportError:
            # 如果PIL不可用，回退到OpenCV绘制英文文本
            font = cv2.FONT_HERSHEY_SIMPLEX
            # 使用英文指令作为fallback
            english_instructions = [
                "Select Watermark Area:",
                "1. Drag to select rectangle area",
                "2. Press SPACE or ENTER to confirm",
                "3. Press ESC to cancel"
            ]
            for i, line in enumerate(english_instructions):
                cv2.putText(display_frame, line, (10, 30 + i * 30), 
                           font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(display_frame, line, (10, 30 + i * 30), 
                           font, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
        
        # 选择ROI
        r = cv2.selectROI(window_name, display_frame, False, False)
        cv2.destroyAllWindows()
        
        # 如果用户按ESC，r为(0, 0, 0, 0)
        if r[2] == 0 or r[3] == 0:
            return None
        
        # 将ROI坐标转换回原始尺寸
        self.roi = (
            int(r[0] / scale_factor),      # x
            int(r[1] / scale_factor),      # y
            int(r[2] / scale_factor),      # width
            int(r[3] / scale_factor)       # height
        )
        
        return self.roi
    
    def _analyze_watermark_type(self, roi_frame: np.ndarray) -> str:
        """
        分析水印类型
        
        Args:
            roi_frame: ROI区域图像 (BGR格式)
            
        Returns:
            水印类型: 'text'（文本）, 'image'（图像）, 'transparent'（透明）, 'solid_bg'（纯色背景）
        """
        # 转换为灰度图
        if len(roi_frame.shape) == 3:
            gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi_frame
        
        # 计算对比度
        contrast = gray.std()
        
        # 边缘检测
        edges = cv2.Canny(gray, 100, 200)
        edge_ratio = np.sum(edges > 0) / edges.size
        
        # 计算颜色多样性
        if len(roi_frame.shape) == 3:
            # 计算颜色直方图
            hist_b = cv2.calcHist([roi_frame], [0], None, [256], [0, 256])
            hist_g = cv2.calcHist([roi_frame], [1], None, [256], [0, 256])
            hist_r = cv2.calcHist([roi_frame], [2], None, [256], [0, 256])
            
            # 计算颜色分布的熵
            def entropy(hist):
                hist = hist[hist > 0]
                hist = hist / hist.sum()
                return -np.sum(hist * np.log2(hist))
            
            color_entropy = (entropy(hist_b) + entropy(hist_g) + entropy(hist_r)) / 3
        else:
            color_entropy = 0
        
        # 计算透明度特征
        if len(roi_frame.shape) == 3:
            hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1]
            saturation_mean = saturation.mean()
        else:
            saturation_mean = 0
        
        # 判断水印类型
        if contrast < 50 and saturation_mean < 50:
            # 低对比度、低饱和度 -> 透明水印
            return 'transparent'
        elif edge_ratio > 0.1 and color_entropy < 5:
            # 高边缘比例、低颜色熵 -> 文本水印
            return 'text'
        elif color_entropy > 6 and edge_ratio > 0.05:
            # 高颜色熵、中等边缘比例 -> 图像水印
            return 'image'
        else:
            # 其他情况 -> 纯色背景水印
            return 'solid_bg'
    
    def _detect_color_range(self, roi_frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        自动检测ROI区域中的主要颜色范围
        
        Args:
            roi_frame: ROI区域图像 (BGR格式)
            
        Returns:
            (lower_hsv, upper_hsv): 检测到的HSV颜色范围
        """
        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
        
        # 计算HSV各通道的直方图
        h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        v_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # 找到主要的色相值
        h_peak = np.argmax(h_hist)
        
        # 设置色相范围 (±10度)
        h_lower = max(0, h_peak - 10)
        h_upper = min(179, h_peak + 10)
        
        # 处理色相环的边界情况 (0度和180度相邻)
        if h_lower == 0 and h_upper < 20:
            # 红色区域特殊处理
            h_lower = 0
            h_upper = 20
        elif h_upper == 179 and h_lower > 160:
            # 红色区域特殊处理
            h_lower = 160
            h_upper = 179
        
        # 找到饱和度和明度的阈值
        s_peak = np.argmax(s_hist)
        v_peak = np.argmax(v_hist)
        
        # 设置饱和度范围 (±50)
        s_lower = max(30, s_peak - 50)
        s_upper = min(255, s_peak + 50)
        
        # 设置明度范围 (±50)
        v_lower = max(30, v_peak - 50)
        v_upper = min(255, v_peak + 50)
        
        # 对于低饱和度的情况，扩大范围
        if s_peak < 50:
            s_lower = max(0, s_peak - 20)
            s_upper = min(255, s_peak + 80)
        
        # 对于低明度的情况，扩大范围
        if v_peak < 50:
            v_lower = max(0, v_peak - 20)
            v_upper = min(255, v_peak + 80)
        
        return np.array([h_lower, s_lower, v_lower], dtype=np.uint8), np.array([h_upper, s_upper, v_upper], dtype=np.uint8)
    
    def detect_watermark_in_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        在单帧中检测水印
        
        Args:
            frame: 输入帧 (BGR格式)
            
        Returns:
            水印掩膜
        """
        if self.roi is None:
            raise ValueError("ROI未选择，请先调用select_roi()方法")
        
        # 提取ROI区域
        x, y, w, h = self.roi
        roi_frame = frame[y:y + h, x:x + w]
        
        if roi_frame.size == 0:
            raise ValueError("ROI区域为空，请重新选择")
        
        # 转换为灰度图
        if len(roi_frame.shape) == 3:
            gray_frame = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_frame = roi_frame
        
        # 先做高斯模糊以减少噪点
        blurred = cv2.GaussianBlur(gray_frame, (5, 5), 0)

        # 使用OTSU阈值处理
        _, otsu_mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 边缘检测辅助
        edge_mask = np.zeros_like(otsu_mask)
        if self.use_canny:
            if self.adaptive_canny:
                # 使用自适应阈值的Canny边缘检测
                v = np.median(blurred)
                lower = int(max(0, (1.0 - 0.33) * v))
                upper = int(min(255, (1.0 + 0.33) * v))
                edges = cv2.Canny(blurred, lower, upper)
            else:
                edges = cv2.Canny(blurred, self.canny_low, self.canny_high)
            # 扩展边缘线宽度
            edge_kernel = np.ones((2, 2), np.uint8)  # 调整为更小的核
            edge_mask = cv2.dilate(edges, edge_kernel, iterations=1)

        # Color segmentation for watermark background
        color_mask = np.zeros_like(otsu_mask)
        if self.use_color_segmentation and len(roi_frame.shape) == 3:
            try:
                hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
                
                # 自动检测颜色范围
                if self.auto_detect_color and self._detected_color_range is None:
                    self.color_lower_hsv, self.color_upper_hsv = self._detect_color_range(roi_frame)
                    self._detected_color_range = (self.color_lower_hsv.copy(), self.color_upper_hsv.copy())
                
                color_mask_local = cv2.inRange(hsv, self.color_lower_hsv, self.color_upper_hsv)
                # reduce salt noise
                if self.morph_open > 0:
                    k = np.ones((self.morph_open, self.morph_open), np.uint8)
                    color_mask_local = cv2.morphologyEx(color_mask_local, cv2.MORPH_OPEN, k)
                color_mask = color_mask_local
            except Exception as e:
                color_mask = np.zeros_like(otsu_mask)

        # 合并掩膜（先计算各自覆盖比例，根据情况决定合并策略）
        total_area = otsu_mask.size
        otsu_fraction = np.count_nonzero(otsu_mask) / total_area
        edge_fraction = np.count_nonzero(edge_mask) / total_area
        color_fraction = np.count_nonzero(color_mask) / total_area

        # Default merged = otsu OR edge
        merged = cv2.bitwise_or(otsu_mask, edge_mask)

        # If color is dominant (likely background rectangle), try to focus on OTSU inside color or edges
        if color_fraction > 0.35:
            if otsu_fraction > 0.02:
                # text likely detected inside the colored background -> pick intersection
                merged = cv2.bitwise_and(otsu_mask, color_mask)
            else:
                # fallback: focus on edges within the color area
                merged = cv2.bitwise_and(edge_mask, color_mask)
                # if edges are empty, fallback to color mask but shrink by opening
                if np.count_nonzero(merged) == 0:
                    merged = color_mask
        else:
            # otherwise use otsu+edge
            merged = cv2.bitwise_or(otsu_mask, edge_mask)

        # 对合并掩膜进行形态学处理，去噪并填充
        # 自适应调整形态学核大小
        open_kernel_size = max(1, min(5, int(self.morph_open)))
        close_kernel_size = max(1, min(10, int(self.morph_close)))
        
        if open_kernel_size > 0:
            kernel_open = np.ones((open_kernel_size, open_kernel_size), np.uint8)
            merged = cv2.morphologyEx(merged, cv2.MORPH_OPEN, kernel_open)
        if close_kernel_size > 0:
            kernel_close = np.ones((close_kernel_size, close_kernel_size), np.uint8)
            merged = cv2.morphologyEx(merged, cv2.MORPH_CLOSE, kernel_close)

        # 清理小连通域
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(merged, connectivity=8)
        cleaned = np.zeros_like(merged)
        for label in range(1, num_labels):
            area = stats[label, cv2.CC_STAT_AREA]
            if area >= self.min_component_area:
                cleaned[labels == label] = 255
        
        # 自适应膨胀：根据水印区域大小调整膨胀程度
        if self.dilation_kernel_size > 0:
            # 计算有效区域的平均大小
            valid_areas = [stats[label, cv2.CC_STAT_AREA] for label in range(1, num_labels) if stats[label, cv2.CC_STAT_AREA] >= self.min_component_area]
            if valid_areas:
                avg_area = np.mean(valid_areas)
                # 小水印使用小核，大水印使用大核
                adaptive_dilation = max(2, min(10, int(np.sqrt(avg_area) / 10)))
                dilate_kernel = np.ones((adaptive_dilation, adaptive_dilation), np.uint8)
                cleaned = cv2.dilate(cleaned, dilate_kernel, iterations=1)

        # 创建完整尺寸的掩膜
        # combine color mask into cleaned mask, scale types consistently
        combined_cleaned = cv2.bitwise_or(cleaned, color_mask)
        if len(frame.shape) == 3:
            mask = np.zeros_like(frame[:, :, 0], dtype=np.uint8)
        else:
            mask = np.zeros_like(frame, dtype=np.uint8)
        mask[y:y + h, x:x + w] = combined_cleaned
        
        return mask
    
    def generate_mask(self, video_clip: VideoFileClip, 
                      auto_select_roi: bool = True, current_user=None) -> np.ndarray:
        """
        生成水印掩膜
        
        Args:
            video_clip: 视频剪辑对象
            auto_select_roi: 是否自动选择ROI
            current_user: 保留参数以保持兼容性
            
        Returns:
            水印掩膜
        """
        # 如果ROI未选择且不需要自动选择，则需要用户手动选择
        if self.roi is None and not auto_select_roi:
            result = self.select_roi(video_clip)
            if result is None:
                raise ValueError("用户取消了ROI选择")
        # 如果ROI未选择但需要自动选择，则自动检测ROI
        elif self.roi is None and auto_select_roi:
            # 自动检测ROI：选择视频中心区域作为默认ROI（占视频的20%区域）
            first_frame = self.get_first_valid_frame(video_clip)
            h, w = first_frame.shape[:2]
            roi_size = int(min(w, h) * 0.2)  # 20% of the smaller dimension
            x = int((w - roi_size) / 2)
            y = int((h - roi_size) / 2)
            self.roi = (x, y, roi_size, roi_size)
            print(f"自动检测到的ROI: x={x}, y={y}, width={roi_size}, height={roi_size}")
        
        total_frames = int(video_clip.duration * video_clip.fps)
        if total_frames < self.num_sample_frames:
            self.num_sample_frames = total_frames
        # ensure min_frame_count is reasonable
        self.min_frame_count = max(1, min(self.min_frame_count, self.num_sample_frames))
        
        # 选择采样帧
        frame_indices = [
            int(i * total_frames / self.num_sample_frames) 
            for i in range(self.num_sample_frames)
        ]
        
        masks: List[np.ndarray] = []
        valid_frames = 0
        
        for idx in frame_indices:
            try:
                frame = video_clip.get_frame(idx / video_clip.fps)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                mask = self.detect_watermark_in_frame(frame_bgr)
                masks.append(mask)
                valid_frames += 1
            except Exception as e:
                warnings.warn(f"处理帧 {idx} 时出错: {e}")
                continue
        
        if valid_frames == 0:
            raise ValueError("未能成功处理任何帧")
        
        # 合并多个掩膜（统计每一像素出现次数）
        combined_mask = np.zeros_like(masks[0], dtype=np.uint16)
        for m in masks:
            combined_mask += (m == 255).astype(np.uint16)
        
        # 应用最小帧数阈值
        threshold_mask = np.where(combined_mask >= self.min_frame_count, 255, 0).astype(np.uint8)
        
        # 膨胀处理以覆盖整个水印区域，并进行开闭运算
        if self.dilation_kernel_size > 0:
            kernel = np.ones((self.dilation_kernel_size, self.dilation_kernel_size), np.uint8)
            threshold_mask = cv2.dilate(threshold_mask, kernel, iterations=2)

        # 最后再做一次形态学清理，避免孤立点
        if self.morph_open > 0:
            kernel_open = np.ones((self.morph_open, self.morph_open), np.uint8)
            threshold_mask = cv2.morphologyEx(threshold_mask, cv2.MORPH_OPEN, kernel_open)

        if self.morph_close > 0:
            kernel_close = np.ones((self.morph_close, self.morph_close), np.uint8)
            threshold_mask = cv2.morphologyEx(threshold_mask, cv2.MORPH_CLOSE, kernel_close)
        
        self._mask = threshold_mask
        return threshold_mask
    
    def get_roi_coordinates(self, watermark_mask: np.ndarray, margin: int = 50) -> Tuple[int, int, int, int]:
        """
        获取水印区域的坐标（带边距）
        
        Args:
            watermark_mask: 水印掩膜
            margin: 边距大小
            
        Returns:
            ROI坐标 (y_min, y_max, x_min, x_max)
        """
        y_indices, x_indices = np.where(watermark_mask > 0)
        
        if len(y_indices) == 0 or len(x_indices) == 0:
            raise ValueError("水印掩膜中未找到水印区域")
        
        # 计算边界
        y_min = max(0, np.min(y_indices) - margin)
        y_max = min(watermark_mask.shape[0], np.max(y_indices) + margin)
        x_min = max(0, np.min(x_indices) - margin)
        x_max = min(watermark_mask.shape[1], np.max(x_indices) + margin)
        
        return (y_min, y_max, x_min, x_max)
    
    def extract_roi_mask(self, watermark_mask: np.ndarray, 
                        roi_coords: Tuple[int, int, int, int]) -> np.ndarray:
        """
        提取ROI区域的掩膜
        
        Args:
            watermark_mask: 完整水印掩膜
            roi_coords: ROI坐标 (y_min, y_max, x_min, x_max)
            
        Returns:
            ROI区域的掩膜
        """
        y_min, y_max, x_min, x_max = roi_coords
        
        # 验证坐标
        if y_min >= y_max or x_min >= x_max:
            raise ValueError(f"无效的ROI坐标: {roi_coords}")
        
        roi_mask = watermark_mask[y_min:y_max, x_min:x_max]
        
        if roi_mask.size == 0:
            raise ValueError("提取的ROI掩膜为空")
        
        return roi_mask
    
    def preview_mask(self, frame: np.ndarray, mask: np.ndarray, 
                    alpha: float = 0.5) -> np.ndarray:
        """
        预览掩膜效果
        
        Args:
            frame: 原始帧
            mask: 水印掩膜
            alpha: 透明度
            
        Returns:
            叠加了掩膜的图像
        """
        # 确保掩膜是3通道
        if len(mask.shape) == 2:
            mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        else:
            mask_color = mask
        
        # 创建红色掩膜
        red_mask = np.zeros_like(frame)
        red_mask[:, :, 2] = mask_color[:, :, 0]  # 红色通道
        
        # 叠加掩膜
        result = cv2.addWeighted(frame, 1 - alpha, red_mask, alpha, 0)
        
        return result
    
    @property
    def mask(self) -> Optional[np.ndarray]:
        """获取当前掩膜"""
        return self._mask
    
    @mask.setter
    def mask(self, value: np.ndarray):
        """设置掩膜"""
        self._mask = value
    
    def reset(self):
        """重置检测器状态"""
        self.roi = None
        self._mask = None
    
    def save_mask(self, filepath: str):
        """
        保存掩膜到文件
        
        Args:
            filepath: 文件路径
        """
        if self._mask is not None:
            cv2.imwrite(filepath, self._mask)
        else:
            raise ValueError("没有可用的掩膜")
    
    def load_mask(self, filepath: str):
        """
        从文件加载掩膜
        
        Args:
            filepath: 文件路径
        """
        self._mask = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        if self._mask is None:
            raise ValueError(f"无法加载掩膜文件: {filepath}")