#!/usr/bin/env python3
"""
视频去水印软件启动脚本 - 修复中文路径版本
"""
import sys
import os
import warnings
from pathlib import Path

# ====================================================
# 1. 修复中文路径问题（关键修复）
# ====================================================

# 在导入任何其他模块前设置环境变量
def setup_environment():
    """设置环境变量，避免中文路径问题"""
    
    # 检查是否在PyInstaller打包后的环境中运行
    if hasattr(sys, '_MEIPASS'):
        # 打包后的环境，使用临时目录
        base_path = sys._MEIPASS
        torch_home = os.path.join(base_path, 'lama_cache')
        hf_home = os.path.join(base_path, 'lama_cache', 'huggingface')
    else:
        # 开发环境，使用原始路径
        torch_home = "F:/AI_Models/lama_cache"
        hf_home = "F:/AI_Models/lama_cache/huggingface"
    
    # 应用环境变量
    os.environ.update({
        'TORCH_HOME': torch_home,
        'HF_HOME': hf_home,
        'HUGGINGFACE_HUB_CACHE': hf_home,
        'XDG_CACHE_HOME': torch_home,
        'PYTHONWARNINGS': 'ignore'  # 忽略警告
    })
    
    # 设置torch hub目录
    try:
        import torch
        torch.hub.set_dir(f"{torch_home}/torch/hub")
    except ImportError:
        pass
    
    # 创建目录
    Path(torch_home).mkdir(parents=True, exist_ok=True)
    Path(f"{torch_home}/torch/hub/checkpoints").mkdir(parents=True, exist_ok=True)
    Path(hf_home).mkdir(parents=True, exist_ok=True)
    
    return torch_home, hf_home

# 执行环境设置
TORCH_HOME, HF_HOME = setup_environment()

print("=" * 60)
print("视频去水印软件 - 修复中文路径版本")
print("=" * 60)
print(f"模型存储路径: {TORCH_HOME}")
print(f"HuggingFace缓存: {HF_HOME}")
print("=" * 60)

# ====================================================
# 2. 添加项目根目录到Python模块搜索路径
# ====================================================

# 获取当前脚本的绝对路径
if hasattr(sys, '_MEIPASS'):
    # 打包后的环境，使用临时目录作为项目根目录
    project_root = sys._MEIPASS
else:
    # 开发环境，使用脚本所在目录
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(current_file)

# 将项目根目录添加到模块搜索路径的最前面
sys.path.insert(0, project_root)

# 可选：添加src目录到模块搜索路径
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

# ====================================================
# 3. 原有依赖检查代码（修改版）
# ====================================================

def check_dependencies():
    """检查必要依赖"""
    missing_deps = []
    
    try:
        import PyQt5
    except ImportError:
        missing_deps.append("PyQt5")
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import torch
    except ImportError:
        missing_deps.append("torch")
    
    try:
        import moviepy
    except ImportError:
        missing_deps.append("moviepy")
    
    try:
        import lama_cleaner
    except ImportError:
        missing_deps.append("lama_cleaner")
    
    if missing_deps:
        print("缺少必要的依赖包:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    return True

# ====================================================
# 4. 检查模型文件
# ====================================================

def check_model_file():
    """检查模型文件"""
    model_path = Path(TORCH_HOME) / "torch/hub/checkpoints/big-lama.pt"
    
    if model_path.exists():
        model_size = model_path.stat().st_size / (1024 * 1024 * 1024)  # GB
        print(f"✅ 模型文件存在: {model_path}")
        print(f"   文件大小: {model_size:.2f} GB")
        return True
    else:
        print(f"⚠ 模型文件不存在: {model_path}")
        print("   首次运行时会自动下载（约2-4GB）")
        print("   如果下载失败，请手动下载:")
        print("   https://huggingface.co/lama-cleaner/big-lama/resolve/main/big-lama.pt")
        print(f"   保存到: {model_path}")
        return False

# ====================================================
# 5. 主函数
# ====================================================

def main():
    """主函数"""
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查模型文件
    check_model_file()
    
    # 检查配置文件目录
    config_dir = os.path.join(project_root, "configs")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    # 运行主程序
    try:
        # 导入主程序
        from src.main import main as app_main
        
        print("\n" + "=" * 60)
        print("启动主程序...")
        print("=" * 60)
        
        # 运行应用程序
        app_main()
        
    except ImportError as e:
        print(f"\n❌ 导入模块时出错: {e}")
        print("\n可能的原因:")
        print("1. 项目目录结构不正确")
        print("2. src目录下缺少__init__.py文件")
        print("3. 缺少必要的Python包")
        print("\n项目结构应该如下:")
        print("F:\\waterremove\\")
        print("├── run.py")
        print("├── src\\")
        print("│   ├── __init__.py")
        print("│   ├── main.py")
        print("│   ├── gui\\")
        print("│   │   ├── __init__.py")
        print("│   │   ├── main_window.py")
        print("│   │   └── ...")
        print("│   └── core\\")
        print("│       ├── __init__.py")
        print("│       └── ...")
        print("└── venv\\")
        
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 启动程序时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ====================================================
# 6. 程序入口
# ====================================================

if __name__ == "__main__":
    main()