# 启动视频去水印软件（修复路径版）
Write-Host "启动视频去水印软件（修复路径版）" -ForegroundColor Green

# 设置环境变量
$env:TORCH_HOME = "F:\AI_Models\lama_cache"
$env:HF_HOME = "F:\AI_Models\lama_cache\huggingface"
$env:HUGGINGFACE_HUB_CACHE = "F:\AI_Models\lama_cache\huggingface"

# 激活虚拟环境
& .\venv\Scripts\Activate.ps1

# 运行程序
python run.py

Read-Host "按Enter键退出"
