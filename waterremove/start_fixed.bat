@echo off
echo 启动视频去水印软件（修复路径版）
echo.

REM 设置环境变量
set TORCH_HOME=F:\AI_Models\lama_cache
set HF_HOME=F:\AI_Models\lama_cache\huggingface
set HUGGINGFACE_HUB_CACHE=F:\AI_Models\lama_cache\huggingface

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 运行程序
python run.py

pause
