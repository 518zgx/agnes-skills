---
name: "agnes-video-generate"
description: "使用 Agnes AI 视频模型（agnes-video-v2.0）从文本提示生成视频。当用户想要通过 Agnes API 创建视频、动画或动态视觉内容时调用。"
---

# Agnes 视频生成

使用 Agnes AI 视频模型根据文本提示生成视频内容。

## 何时使用本技能

在以下情况使用本技能：
- 用户想要根据文本描述生成视频
- 用户需要通过 Agnes API 进行 AI 视频生成
- 用户想要创建动画、动态视觉内容或视频片段
- 用户明确要求使用 Agnes 进行视频生成

## 可用模型

| 模型 | 描述 | 推荐度 |
|-------|-------------|----------------|
| `agnes-video-v2.0` | V2.0 视频生成模型，支持文生视频 | ⭐ 推荐 |

## 前置条件

### API 密钥配置

将 API 密钥设置为环境变量：

```bash
# Windows PowerShell
$env:AGNES_API_KEY = "sk-your-api-key-here"

# Linux/macOS
export AGNES_API_KEY="sk-your-api-key-here"
```

脚本会从环境中读取 `AGNES_API_KEY`。

### 依赖安装

```bash
pip install httpx
```

## 使用方法

### 命令行

```bash
# 基础用法（文生视频）
python scripts/agnes_video_generate.py -p "一只可爱的小猫在草地上奔跑"

# 指定时长和分辨率
python scripts/agnes_video_generate.py -p "日落风景" -d 5 -s 720p -o output.mp4

# 使用指定模型
python scripts/agnes_video_generate.py -p "海浪拍岸" -m agnes-video-v2.0

# 查询任务状态
python scripts/agnes_video_generate.py -q task_abc123
```

### Python API

```python
import asyncio
import sys
sys.path.append("scripts")
from agnes_video_generate import agnes_video_generate

async def main():
    result = await agnes_video_generate([
        {
            "video_name": "cat_running",
            "prompt": "一只可爱的小猫在草地上奔跑",
            "duration": 5,
            "size": "720p",
        }
    ])
    print(result)

asyncio.run(main())
```

## 命令行选项

| 选项 | 简写 | 描述 | 默认值 |
|--------|----------|-------------|---------|
| `--prompt` | `-p` | 视频描述文本（必填） | - |
| `--name` | `-n` | 输出视频名称标识 | `agnes_video` |
| `--model` | `-m` | 模型名称 | `agnes-video-v2.0` |
| `--duration` | `-d` | 视频时长（秒） | `5` |
| `--size` | `-s` | 视频分辨率：`720p` / `1080p` | `720p` |
| `--output` | `-o` | 输出文件路径 | `<name>.mp4` |
| `--query-task` | `-q` | 查询指定任务 ID 的状态 | - |
| `--timeout` | `-t` | 轮询超时时间（秒） | `600` |
| `--list-models` | | 列出可用模型 | - |

## API 详情

### 创建任务

- **接口地址**: `POST https://apihub.agnes-ai.com/v1/videos`
- **认证方式**: `Bearer <AGNES_API_KEY>`
- **请求体**:
  ```json
  {
    "model": "agnes-video-v2.0",
    "prompt": "视频描述文本",
    "size": "720p"
  }
  ```

### 查询状态

- **接口地址**: `GET https://apihub.agnes-ai.com/v1/videos/{task_id}`
- **状态值**: `queued` → `processing` → `completed` / `failed`
- **视频 URL**: 任务完成后从 `remixed_from_video_id` 字段获取

### 支持参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | string | 模型名称，默认 `agnes-video-v2.0` |
| `prompt` | string | 视频描述文本（必填） |
| `size` | string | 分辨率：`720p`（1280×704）/ `1080p` |

### 限流说明

- Agnes 视频 API 限流：每 1 分钟 1 个请求
- 批量生成时请确保间隔 ≥ 60 秒

## 视频规格

| 参数 | 值 |
|------|-----|
| 默认时长 | 5 秒 |
| 720p 分辨率 | 1280 × 704 |
| 格式 | MP4 |
| 输出 | 视频 URL（24 小时内有效，请及时下载） |

## 提示词编写技巧

- 描述要生动详细：场景、动作、光线、氛围
- 运动描述：镜头移动、主体动作、动态元素
- 风格指定：像素风、写实、卡通、油画等
- 避免过于复杂的长镜头，聚焦一个主要动作

## 错误处理

| 错误 | 原因 | 解决方法 |
|------|------|---------|
| 401 Unauthorized | API 密钥无效 | 检查 AGNES_API_KEY 是否正确 |
| 429 rate_limit_exceeded | 触发限流 | 等待 60 秒后重试 |
| 404 Invalid URL | 接口路径错误 | 使用 `/v1/videos` 路径 |
| 任务超时 | 生成时间过长 | 增加 `--timeout` 参数 |
| 任务 failed | 生成失败 | 查看 error 字段，调整提示词重试 |

## 返回值

脚本返回一个 JSON 对象：

```python
{
    "status": "success" | "partial_success" | "error",
    "success_list": [
        {
            "video_name": "视频名称",
            "task_id": "task_xxx",
            "url": "https://...mp4",
            "local_path": "本地路径.mp4"
        }
    ],
    "error_list": [
        {"video_name": "视频名称", "error": "错误信息"}
    ]
}
```

## 返回信息规范

必须返回三类信息：

1. **下载视频的本地文件路径**，例如：
   `local_path: e:\AI\FM\agnes_video_20260704_120000.mp4`

2. **用于展示的 Markdown 视频列表**：
   ```
   <video src="https://platform-outputs.agnes-ai.space/videos/xxx.mp4" width="640" controls>video-name</video>
   ```

3. **任务 ID**（便于后续查询）：
   `task_id: task_abc123`

## 许可证

本技能用于 Agnes AI 服务。使用时请遵守 Agnes AI 的服务条款。
