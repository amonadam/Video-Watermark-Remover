# 单元测试文档

## 概述

本项目为视频水印去除系统的核心代码编写了全面的单元测试，覆盖正常/异常场景，语句覆盖率较高。测试使用pytest框架，确保核心功能的稳定性和可靠性。

## 测试环境配置

### 依赖安装

确保已安装pytest和pytest-cov：

```bash
pip install pytest pytest-cov
```

### 测试目录结构

```
单元测试文件/
├── pytest.ini              # pytest配置文件
├── test_watermark_detector.py  # 水印检测器测试
├── test_lama_inpainter.py      # 图像修复器测试
├── test_video_processor.py      # 视频处理器测试
└── README.md               # 本文档
```

## 测试文件说明

### 1. test_watermark_detector.py

测试水印检测器（WatermarkDetector）类的功能。

**测试类**：
- `TestWatermarkDetectorInit` - 测试初始化功能
- `TestWatermarkDetectorSelectROI` - 测试ROI选择功能
- `TestWatermarkDetectorAnalyzeWatermarkType` - 测试水印类型分析
- `TestWatermarkDetectorDetectColorRange` - 测试颜色范围检测
- `TestWatermarkDetectorGetRoiCoordinates` - 测试ROI坐标获取
- `TestWatermarkDetectorExtractRoiMask` - 测试ROI掩膜提取
- `TestWatermarkDetectorGenerateMask` - 测试水印掩膜生成

**测试用例数**: 44个

**覆盖率**: 83%

**主要测试场景**：
- 正常初始化参数
- 负数和超大参数处理
- ROI选择（正常、手动、异常）
- 水印类型分析（彩色、灰度、单通道）
- 颜色范围自动检测
- ROI坐标计算和掩膜提取
- 水印掩膜生成（正常、异常处理）

### 2. test_lama_inpainter.py

测试图像修复器（LamaInpainter）类的功能。

**测试类**：
- `TestLamaInpainterInit` - 测试初始化功能
- `TestLamaInpainterInpaint` - 测试图像修复功能
- `TestLamaInpainterBatchProcess` - 测试批量处理功能
- `TestLamaInpainterCacheManagement` - 测试缓存管理功能
- `TestLamaInpainterErrorHandling` - 测试错误处理功能

**测试用例数**: 26个

**覆盖率**: 89%

**主要测试场景**：
- 初始化（正常、GPU/CPU模式）
- 图像修复（彩色、灰度、BGRA图像）
- 批量处理（多图像、异常处理）
- 缓存管理（启用/禁用、清除缓存）
- 错误处理（无效输入、回退机制）

### 3. test_video_processor.py

测试视频处理器（VideoProcessor）类的功能。

**测试类**：
- `TestVideoProcessorInit` - 测试初始化功能
- `TestVideoProcessorGetVideoInfo` - 测试视频信息获取
- `TestVideoProcessorGetFileSize` - 测试文件大小计算
- `TestVideoProcessorGetVideoFormat` - 测试视频格式识别
- `TestVideoProcessorMatchColors` - 测试颜色校正
- `TestVideoProcessorGetProgressInfo` - 测试进度信息获取
- `TestVideoProcessorCleanup` - 测试资源清理
- `TestVideoProcessorPreviewFrame` - 测试帧预览
- `TestVideoProcessorProcess` - 测试视频处理流程
- `TestVideoProcessorIntegration` - 测试集成功能

**测试用例数**: 26个

**覆盖率**: 86%

**主要测试场景**：
- 初始化（正常、空配置、复杂配置）
- 视频信息获取（正常、不同格式）
- 文件大小计算（字节、KB、MB、GB）
- 颜色校正（正常、小背景、错误处理）
- 进度跟踪（未开始、处理中、完成）
- 资源清理（正常、异常处理）
- 帧预览（正常、错误处理）
- 完整处理流程（文件不存在、掩膜生成失败、正常处理）

## 运行测试

### 运行所有测试

```bash
pytest 单元测试文件/ -v
```

### 运行特定测试文件

```bash
pytest 单元测试文件/test_watermark_detector.py -v
pytest 单元测试文件/test_lama_inpainter.py -v
pytest 单元测试文件/test_video_processor.py -v
```

### 运行特定测试类

```bash
pytest 单元测试文件/test_watermark_detector.py::TestWatermarkDetectorInit -v
```

### 运行特定测试方法

```bash
pytest 单元测试文件/test_watermark_detector.py::TestWatermarkDetectorInit::test_init_normal -v
```

### 生成测试覆盖率报告

```bash
pytest 单元测试文件/ --cov=src --cov-report=html --cov-report=term-missing
```

覆盖率报告将生成在 `htmlcov` 目录中，可以在浏览器中打开 `htmlcov/index.html` 查看详细报告。

## 测试结果

### 当前测试状态

- **总测试用例数**: 96个
- **通过**: 96个 (100%)
- **失败**: 0个
- **警告**: 18个（库的弃用警告，不影响测试结果）

### 核心模块覆盖率

| 模块 | 覆盖率 | 测试用例数 |
|------|--------|-----------|
| WatermarkDetector | 83% | 44 |
| LamaInpainter | 89% | 26 |
| VideoProcessor | 86% | 26 |

### 测试覆盖的场景

✅ **正常场景测试**
- 标准输入参数
- 正常处理流程
- 预期输出验证

✅ **异常场景测试**
- 文件不存在
- 无效参数
- 处理失败
- 网络错误

✅ **边界条件测试**
- 空输入
- 零值处理
- 小背景区域
- 单通道图像

✅ **错误处理测试**
- 异常捕获
- 降级处理
- 资源清理
- 回退机制

✅ **集成测试**
- 完整处理流程
- 模块间交互
- 端到端测试

## 测试驱动开发（TDD）

本项目采用测试驱动开发方法：

1. **先写测试用例**：根据需求文档和功能规格，先编写测试用例
2. **运行测试**：运行测试用例，预期失败
3. **编写代码**：编写功能代码，使测试通过
4. **重构代码**：优化代码结构，保持测试通过
5. **重复迭代**：持续改进和扩展测试

## 测试最佳实践

1. **测试独立性**：每个测试用例应该独立运行，不依赖其他测试
2. **测试可读性**：使用清晰的测试名称和描述
3. **测试覆盖**：覆盖正常流程、异常流程和边界条件
4. **Mock使用**：使用Mock对象隔离外部依赖
5. **断言明确**：使用明确的断言验证预期结果
6. **测试速度**：保持测试快速执行，避免不必要的等待

## 持续集成

建议将单元测试集成到CI/CD流程中：

```yaml
# 示例GitHub Actions配置
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest 单元测试文件/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 常见问题

### Q: 测试运行很慢怎么办？

A: 可以使用pytest的并行执行插件：

```bash
pip install pytest-xdist
pytest 单元测试文件/ -n auto
```

### Q: 如何调试失败的测试？

A: 使用pytest的调试选项：

```bash
pytest 单元测试文件/ -v --pdb
```

### Q: 如何只运行失败的测试？

A: 使用pytest的last-failed选项：

```bash
pytest 单元测试文件/ --lf
```

### Q: 测试覆盖率不够怎么办？

A: 分析覆盖率报告中的未覆盖代码，添加相应的测试用例。重点关注：
- 异常处理分支
- 边界条件
- 错误回退路径

## 更新日志

### 2024-01-05
- 完成所有核心模块的单元测试
- 实现测试驱动开发流程
- 生成完整的测试覆盖率报告
- 96个测试用例全部通过

## 联系方式

如有问题或建议，请联系项目维护者。
