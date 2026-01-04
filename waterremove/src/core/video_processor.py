"""
视频处理器
"""
import os
import time
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from datetime import timedelta
from tqdm import tqdm
from moviepy import VideoFileClip, ImageSequenceClip
import warnings
import traceback

# 引用原有依赖
from .watermark_detector import WatermarkDetector
from .lama_inpainter import LamaInpainter

class VideoProcessor:
    """视频处理器：包含色彩校正和优化的融合逻辑"""
    
    def __init__(self, video_path: str, output_dir: str, 
                 detector: WatermarkDetector, inpainter: LamaInpainter, 
                 config: Dict[str, Any]):
        """初始化视频处理器"""
        self.video_path = video_path
        self.output_dir = output_dir
        self.detector = detector
        self.inpainter = inpainter
        self.config = config
        
        from .utils import get_current_user
        self.current_user = get_current_user()

        self.video_clip: Optional[VideoFileClip] = None
        self.watermark_mask: Optional[np.ndarray] = None
        self.roi_coords: Optional[Tuple[int, int, int, int]] = None
        self.roi_mask: Optional[np.ndarray] = None

        self.stats: Dict[str, Any] = {
            "start_time": 0,
            "end_time": 0,
            "total_frames": 0,
            "processed_frames": 0,
            "failed_frames": 0,
            "video_info": {}
        }
    
    def process(self) -> Dict[str, Any]:
        """处理视频主流程"""
        self.stats["start_time"] = time.time()
        
        try:
            if not os.path.exists(self.video_path):
                raise FileNotFoundError(f"视频文件不存在: {self.video_path}")
            
            os.makedirs(self.output_dir, exist_ok=True)
            
            print(f"正在打开视频: {self.video_path}")
            self.video_clip = VideoFileClip(self.video_path)
            
            self.stats["video_info"] = self._get_video_info()
            self.stats["total_frames"] = self.stats["video_info"]["total_frames"]
            
            print("正在检测水印...")
            auto_select_roi = self.config.get("auto_select_roi", True)
            self.watermark_mask = self.detector.generate_mask(self.video_clip, auto_select_roi, self.current_user)
            
            if self.watermark_mask is None:
                raise ValueError("未能生成水印掩膜")
            
            # 获取ROI坐标
            margin = self.config.get("margin", 50)
            self.roi_coords = self.detector.get_roi_coordinates(self.watermark_mask, margin)
            
            # 提取 ROI 掩膜
            # 注意：这里我们获取最原始的 mask，后续会根据需要进行膨胀处理
            self.roi_mask = self.detector.extract_roi_mask(self.watermark_mask, self.roi_coords)
            
            # 处理视频帧
            output_path = self._process_video_frames()
            
            self.stats["end_time"] = time.time()
            self.stats["processing_time"] = self.stats["end_time"] - self.stats["start_time"]
            self.stats["success"] = True
            self.stats["output_path"] = output_path
            
            print(f"视频处理完成: {output_path}")
            
        except Exception as e:
            self.stats["success"] = False
            self.stats["error"] = str(e)
            self.stats["traceback"] = traceback.format_exc()
            print(f"视频处理失败: {e}")
            
        finally:
            self._cleanup()
        
        return self.stats

    def _match_colors(self, source: np.ndarray, target: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        颜色校正核心算法：Reinhard 颜色迁移的简化版。
        将 source (修复后的图) 的颜色分布调整为 target (原图背景) 的分布。
        
        Args:
            source: 修复后的图像 (ROI区域)
            target: 原始图像 (ROI区域)
            mask: 掩膜 (255为水印区域，0为背景区域)
        
        Returns:
            校正后的图像
        """
        try:
            # 1. 确定背景区域（参考区域）
            # 这里的 mask 255 是水印，0 是背景。我们需要背景作为参考。
            # 为了稳健，我们稍微腐蚀背景区域（即膨胀 mask），避免取到水印边缘的脏像素
            dilated_mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
            background_mask = (dilated_mask == 0)
            
            # 如果背景区域太小，无法统计，直接返回原图
            if np.sum(background_mask) < 100:
                return source

            # 2. 转换到 LAB 空间 (L: 亮度, A/B: 色彩)
            # LAB 空间比 RGB 更适合做亮度分离，避免调整亮度时产生怪异的色偏
            src_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype(np.float32)
            tgt_lab = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype(np.float32)
            
            corrected_lab = src_lab.copy()
            
            # 3. 对三个通道分别计算统计量 (Reinhard Method)
            # 我们只统计背景区域的均值和标准差
            for i in range(3):
                # 提取背景区域的像素值
                tgt_pixels = tgt_lab[:, :, i][background_mask]
                src_pixels = src_lab[:, :, i] # 我们调整整个 source，不仅是水印区，反正最后会 mask 融合
                
                tgt_mean = np.mean(tgt_pixels)
                tgt_std = np.std(tgt_pixels)
                
                src_mean = np.mean(src_pixels)
                src_std = np.std(src_pixels)
                
                # 避免除以零
                if src_std < 1e-5:
                    src_std = 1e-5
                
                # 线性变换: (Pixel - SourceMean) * (TargetStd / SourceStd) + TargetMean
                # 这种方法比直方图匹配更线性，不会产生那种“椒盐噪声”或剧烈的彩色噪点
                # 为了防止暗部过度放大噪点，我们可以限制 std 的缩放比例
                scale = tgt_std / src_std
                scale = np.clip(scale, 0.8, 1.2) # 限制对比度调整幅度，防止噪点爆炸
                
                corrected_channel = (src_pixels - src_mean) * scale + tgt_mean
                corrected_lab[:, :, i] = corrected_channel

            # 4. 转换回 BGR
            corrected_lab = np.clip(corrected_lab, 0, 255).astype(np.uint8)
            corrected_bgr = cv2.cvtColor(corrected_lab, cv2.COLOR_LAB2BGR)
            
            return corrected_bgr

        except Exception as e:
            # 如果校正过程出错（比如数学错误），降级返回原始修复结果
            # warnings.warn(f"色彩校正失败: {e}")
            return source
    
    def _process_video_frames(self) -> str:
        """处理视频帧（包含改进的预处理和后处理）"""
        if self.video_clip is None or self.roi_coords is None or self.roi_mask is None:
            raise ValueError("视频处理器未正确初始化")
        
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_filename = f"{video_name}_clean_{timestamp}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        y_min, y_max, x_min, x_max = self.roi_coords
        processed_frames: List[np.ndarray] = []
        total_frames = self.stats["total_frames"]
        
        # 预计算掩膜
        # 1. inpaint_mask: 稍微膨胀，让模型修复范围大一点，覆盖水印边缘
        inpaint_mask = cv2.dilate(self.roi_mask, np.ones((5, 5), np.uint8), iterations=2)
        
        # 2. blend_mask: 用于最终融合。
        # 使用高斯模糊实现羽化，但基础 mask 也要稍微膨胀一点点，确保不会把水印边缘混进去
        # 这里的逻辑是：Mask 越白，越使用修复后的图。
        blend_base = cv2.dilate(self.roi_mask, np.ones((3, 3), np.uint8), iterations=1)
        blend_mask = cv2.GaussianBlur(blend_base.astype(np.float32), (15, 15), 0) / 255.0
        # 扩展维度以匹配 BGR 通道 (H, W, 1)
        blend_mask = blend_mask[:, :, np.newaxis]

        progress_bar = tqdm(
            total=total_frames,
            desc=f"处理视频: {video_name}",
            unit="帧",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
        )
        
        for frame_index in range(total_frames):
            try:
                frame_time = min(frame_index / self.video_clip.fps, self.video_clip.duration - 0.01)
                frame = self.video_clip.get_frame(frame_time)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                roi = frame_bgr[y_min:y_max, x_min:x_max]
                
                if roi.size == 0:
                    processed_frames.append(frame)
                    continue
                
                # --- 核心处理步骤 ---
                
                # 1. 修复 (Inpaint)
                # 使用膨胀过的 mask，确保完全覆盖
                processed_roi = self.inpainter.inpaint(roi, inpaint_mask, self.current_user)
                
                # 2. 色彩校正 (Color Correction)
                # 解决"半透明罩子"问题的关键步骤
                # 仅当两者尺寸一致时进行
                if processed_roi.shape == roi.shape:
                    processed_roi = self._match_colors(processed_roi, roi, self.roi_mask)

                # 3. 融合 (Blend)
                # 使用预计算的 blend_mask 进行线性插值
                if processed_roi.shape[:2] == roi.shape[:2]:
                    # 转换 float 进行计算以保证精度
                    blended = (
                        blend_mask * processed_roi.astype(np.float32) +
                        (1.0 - blend_mask) * roi.astype(np.float32)
                    )
                    blended = np.clip(blended, 0, 255).astype(np.uint8)
                    
                    # 将处理好的 ROI 放回原图
                    result = frame_bgr.copy()
                    result[y_min:y_max, x_min:x_max] = blended
                    
                    # 转回 RGB 存入列表
                    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
                    processed_frames.append(result_rgb)
                else:
                    # 尺寸不匹配时的回退
                    processed_frames.append(frame)
                
                self.stats["processed_frames"] += 1
                
            except Exception as e:
                self.stats["failed_frames"] += 1
                # 错误处理：尝试添加原帧
                try:
                    frame = self.video_clip.get_frame(frame_time)
                    processed_frames.append(frame)
                except:
                    if processed_frames:
                        processed_frames.append(processed_frames[-1]) # 重复上一帧
            
            progress_bar.update(1)
        
        progress_bar.close()
        
        # 写入视频文件
        print("正在创建输出视频...")
        output_clip = ImageSequenceClip(processed_frames, fps=self.video_clip.fps)
        
        codec = self.config.get("codec", "libx264")
        bitrate = self.config.get("bitrate", "5000k")
        preset = self.config.get("preset", "medium")
        
        output_clip.write_videofile(
            output_path,
            codec=codec,
            bitrate=bitrate,
            preset=preset,
            audio_codec='aac' if self.video_clip.audio else None,
            temp_audiofile=None,
            remove_temp=True,
            logger=None
        )
        output_clip.close()
        
        return output_path
    
    def _get_video_info(self) -> Dict[str, Any]:
        """获取视频信息"""
        if self.video_clip is None:
            return {}
        return {
            "filename": os.path.basename(self.video_path),
            "filepath": self.video_path,
            "filesize": self._get_file_size(self.video_path),
            "resolution": f"{int(self.video_clip.w)}x{int(self.video_clip.h)}",
            "duration": f"{self.video_clip.duration:.2f}秒",
            "total_frames": int(self.video_clip.duration * self.video_clip.fps),
            "fps": f"{self.video_clip.fps:.2f}",
            "codec": "未知",
            "format": self._get_video_format()
        }
    
    def _get_file_size(self, filepath: str) -> str:
        """获取文件大小"""
        try:
            size_bytes = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.2f} TB"
        except:
            return "未知"
    
    def _get_video_format(self) -> str:
        """获取视频格式"""
        ext = os.path.splitext(self.video_path)[1].lower()
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']:
            return ext[1:].upper()
        return "未知"

    def preview_frame(self, frame_index: int = 0) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """预览指定帧的效果"""
        if self.video_clip is None:
            return None, None
        
        try:
            frame_time = min(frame_index / self.video_clip.fps, self.video_clip.duration - 0.01)
            frame = self.video_clip.get_frame(frame_time)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            if self.watermark_mask is None:
                auto_select_roi = self.config.get("auto_select_roi", True)
                self.watermark_mask = self.detector.generate_mask(self.video_clip, auto_select_roi, self.current_user)

                if self.watermark_mask is None:
                    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    return rgb, rgb

                margin = self.config.get("margin", 50)
                self.roi_coords = self.detector.get_roi_coordinates(self.watermark_mask, margin)
                self.roi_mask = self.detector.extract_roi_mask(self.watermark_mask, self.roi_coords)

            if self.roi_coords is None or self.roi_mask is None:
                rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                return rgb, rgb

            y_min, y_max, x_min, x_max = self.roi_coords
            roi = frame_bgr[y_min:y_max, x_min:x_max]

            if roi.size == 0:
                rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                return rgb, rgb

            # 1. Inpaint
            inpaint_mask = cv2.dilate(self.roi_mask, np.ones((5, 5), np.uint8), iterations=2)
            processed_roi = self.inpainter.inpaint(roi, inpaint_mask, self.current_user)

            # 2. Color Correction (Reuse the logic)
            processed_roi = self._match_colors(processed_roi, roi, self.roi_mask)

            # 3. Blend
            blend_base = cv2.dilate(self.roi_mask, np.ones((3, 3), np.uint8), iterations=1)
            blend_mask = cv2.GaussianBlur(blend_base.astype(np.float32), (15, 15), 0) / 255.0
            blend_mask = blend_mask[:, :, np.newaxis]

            result = frame_bgr.copy()
            if processed_roi.shape[:2] == roi.shape[:2]:
                blended = (
                    blend_mask * processed_roi.astype(np.float32) +
                    (1.0 - blend_mask) * roi.astype(np.float32)
                )
                blended = np.clip(blended, 0, 255).astype(np.uint8)
                result[y_min:y_max, x_min:x_max] = blended

            return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB), cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            
        except Exception as e:
            warnings.warn(f"预览帧 {frame_index} 时出错: {e}")
            # 出错返回原图
            try:
                rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                return rgb, rgb
            except:
                return None, None

    def get_progress_info(self) -> Dict[str, Any]:
        """获取处理进度信息"""
        if self.stats["total_frames"] == 0:
            return {"progress": 0.0, "message": "等待开始"}
        
        progress = self.stats["processed_frames"] / self.stats["total_frames"] * 100
        
        elapsed_time = time.time() - self.stats["start_time"]
        if self.stats["processed_frames"] > 0:
            remaining_time = elapsed_time / self.stats["processed_frames"] * (self.stats["total_frames"] - self.stats["processed_frames"])
        else:
            remaining_time = 0
        
        return {
            "progress": min(progress, 100.0),
            "processed_frames": self.stats["processed_frames"],
            "total_frames": self.stats["total_frames"],
            "failed_frames": self.stats["failed_frames"],
            "elapsed_time": str(timedelta(seconds=int(elapsed_time))),
            "remaining_time": str(timedelta(seconds=int(remaining_time))),
            "video_info": self.stats["video_info"]
        }
    
    def _cleanup(self):
        """清理资源"""
        if hasattr(self, 'video_clip') and self.video_clip:
            try:
                self.video_clip.close()
            except:
                pass
            self.video_clip = None
        
        if hasattr(self, 'inpainter') and hasattr(self.inpainter, 'clear_cache'):
            try:
                self.inpainter.clear_cache()
            except:
                pass
    
    def __del__(self):
        self._cleanup()