import os
import sys
import cv2
import numpy as np

# 测试cv2.selectROI函数
def test_select_roi():
    # 创建一个测试图像
    img = np.zeros((500, 800, 3), dtype=np.uint8)
    img[:, :] = (200, 200, 200)  # 灰色背景
    
    # 添加一些测试文本
    cv2.putText(img, "Test Image", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
    cv2.putText(img, "Drag to select area", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # 测试selectROI函数
    print("Testing cv2.selectROI...")
    r = cv2.selectROI("Test Window", img, False, False)
    cv2.destroyAllWindows()
    
    print(f"Selected ROI: {r}")

if __name__ == "__main__":
    test_select_roi()