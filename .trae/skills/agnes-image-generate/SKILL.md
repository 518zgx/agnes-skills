---
name: "agnes-image-generate"
description: "使用 Agnes AI 图像模型（agnes-image-2.1-flash）从文本提示生成图片。当用户想要通过 Agnes API 创建图片、美术作品或视觉内容时调用。"
---

# Agnes 图像生成

使用 Agnes AI 图像模型根据文本提示生成高质量图片。

## 何时使用本技能

在以下情况使用本技能：
- 用户想要根据文本描述生成图片
- 用户需要通过 Agnes API 进行 AI 图像生成
- 用户想要创建美术作品、插画或视觉内容
- 用户明确要求使用 Agnes 进行图像生成

## 可用模型

| 模型 | 描述 | 推荐度 |
|-------|-------------|----------------|
| `agnes-image-2.1-flash` | 最新 flash 模型，速度快且质量高 | ⭐ 推荐 |
| `agnes-image-2.0-flash` | 稳定的 flash 模型 | 备选 |

## 前置条件

### API 密钥配置

将 API 密钥设置为环境变量：

```bash
# Windows PowerShell
$env:AGNES_API_KEY = "sk-your-api-key-here"

# Linux/macOS
export AGNES_API_KEY="sk-your-api-key-here"
```

脚本会从环境中读取 `AGNES_API_KEY`。如果未设置，将提示用户输入密钥。

### 依赖安装

```bash
pip install httpx Pillow
```

## 使用方法

### 命令行

```bash
# 基础用法
python scripts/agnes_image_generate.py -p "一只在花园里玩耍的可爱猫咪"

# 指定尺寸和输出路径
python scripts/agnes_image_generate.py -p "像素风风景" -s 1024x1024 -o output.png

# 使用指定模型
python scripts/agnes_image_generate.py -p "山间日落" -m agnes-image-2.1-flash

# 批量生成（多个提示词）
python scripts/agnes_image_generate.py -p "猫" "狗" "鸟" -g
```

### Python API

```python
import asyncio
import sys
sys.path.append("scripts")
from agnes_image_generate import agnes_generate

async def main():
    result = await agnes_generate([
        {
            "prompt": "像素风格的可爱小猫",
            "size": "1024x1024",
        }
    ])
    print(result)

asyncio.run(main())
```

## 命令行选项

| 选项 | 简写 | 描述 | 默认值 |
|--------|----------|-------------|---------|
| `--prompt` | `-p` | 图片描述文本（必填，支持多个） | - |
| `--model` | `-m` | 模型名称 | `agnes-image-2.1-flash` |
| `--size` | `-s` | 图片尺寸 | `1024x1024` |
| `--output` | `-o` | 输出文件路径 | `agnes_output_<时间戳>.png` |
| `--group` | `-g` | 启用批量生成 | `false` |
| `--timeout` | `-t` | 请求超时时间（秒） | `120` |
| `--list-models` | | 列出可用模型 | - |

## API 详情

- **接口地址**: `POST https://apihub.agnes-ai.com/v1/images/generations`
- **认证方式**: `Bearer <AGNES_API_KEY>`
- **支持参数**: `model`、`prompt`、`size`
- **不支持参数**: `response_format`、`watermark`、`output_format`
- **响应格式**: `data[0].url` 包含生成的图片 URL（24 小时内有效）

## 支持的尺寸

| 尺寸 | 宽高比 |
|------|-------------|
| `1024x1024` | 1:1（默认） |
| `1792x1024` | 16:9 横屏 |
| `1024x1792` | 9:16 竖屏 |
| `768x768` | 1:1 小尺寸 |

## 提示词编写技巧

- 描述要详细：指定风格、主题、光线、颜色
- 像素艺术：在提示词中加入 "pixel art 8-bit retro"
- 保持一致性：在提示词中参考现有的艺术风格
- 避免请求特定输出格式（API 不支持）

## 错误处理

- **401 Unauthorized**: 检查 API 密钥是否有效
- **400 UnsupportedParamsError**: 从请求中移除 `response_format` 参数
- **503 model_not_found**: 使用 `--list-models` 查看正确的模型名称
- **超时**: 增加 `--timeout` 参数值

## 返回值

脚本返回一个 JSON 对象：

```python
{
    "status": "success" | "error",
    "success_list": [{"prompt": "...", "url": "https://...", "local_path": "..."}],
    "error_list": [{"prompt": "...", "error": "..."}]
}
```

## 返回信息规范

必须返回两类信息：

1. **下载图片的本地文件路径**，例如：
   `local_path: e:\AI\FM\agnes_output_20260704_120000.png`

2. **用于展示的 Markdown 图片列表**：
   ```
   ![generated-image-1](https://platform-outputs.agnes-ai.space/images/xxx.png)
   ```

## 许可证

本技能用于 Agnes AI 服务。使用时请遵守 Agnes AI 的服务条款。
