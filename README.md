# Agnes AI Skills

基于 Agnes AI 的图像和视频生成技能集合

## 技能列表

### 1. agnes-image-generate

使用 Agnes AI 图像模型（agnes-image-2.1-flash）从文本提示生成图片。

**功能**:
- 文生图（Text-to-Image）
- 支持多种尺寸（1024x1024、1792x1024、1024x1792）
- 命令行 + Python API 双模式
- 自动下载保存生成的图片

**使用方式**:
```bash
# 设置 API Key
$env:AGNES_API_KEY = "sk-your-api-key"

# 生成图片
python .trae/skills/agnes-image-generate/scripts/agnes_image_generate.py -p "一只可爱的小猫" -o output.png
```

### 2. agnes-video-generate

使用 Agnes AI 视频模型（agnes-video-v2.0）从文本提示生成视频。

**功能**:
- 文生视频（Text-to-Video）
- 支持 720p / 1080p 分辨率
- 默认 5 秒时长
- 命令行 + Python API 双模式
- 自动轮询任务状态并下载视频

**使用方式**:
```bash
# 设置 API Key
$env:AGNES_API_KEY = "sk-your-api-key"

# 生成视频
python .trae/skills/agnes-video-generate/scripts/agnes_video_generate.py -p "小猫奔跑" -n cat_video -o output.mp4
```

## 安装依赖

```bash
pip install httpx Pillow
```

## API 配置

- **接口地址**: `https://apihub.agnes-ai.com/v1`
- **认证方式**: Bearer Token（环境变量 `AGNES_API_KEY`）
- **可用模型**:
  - `agnes-image-2.1-flash` - 图像生成
  - `agnes-image-2.0-flash` - 图像生成（旧版）
  - `agnes-video-v2.0` - 视频生成

## 目录结构

```
.trae/skills/
├── agnes-image-generate/
│   ├── SKILL.md
│   └── scripts/
│       └── agnes_image_generate.py
└── agnes-video-generate/
    ├── SKILL.md
    └── scripts/
        └── agnes_video_generate.py
```

## 注意事项

- 视频生成限流：1 次 / 分钟
- 图片 URL 24 小时内有效，请及时下载
- 视频 URL 24 小时内有效，请及时下载

## 许可证

MIT License
