# -*- coding: utf-8 -*-
"""
Agnes AI Video Generation Script
Uses Agnes API to generate videos from text prompts.

Usage:
    python agnes_video_generate.py -p "一只可爱的小猫"
    python agnes_video_generate.py -p "日落" -d 5 -s 720p -o output.mp4
    python agnes_video_generate.py -q task_abc123
    python agnes_video_generate.py --list-models
"""

import argparse
import asyncio
import os
import sys
import time
import json
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)


API_BASE = "https://apihub.agnes-ai.com/v1"
DEFAULT_MODEL = "agnes-video-v2.0"
DEFAULT_SIZE = "720p"
DEFAULT_DURATION = 5
DEFAULT_TIMEOUT = 600
POLL_INTERVAL = 15


def get_api_key():
    key = os.environ.get("AGNES_API_KEY")
    if not key:
        print("Error: AGNES_API_KEY not found in environment variables.")
        print("Set it with: $env:AGNES_API_KEY = 'sk-your-key' (PowerShell)")
        print("Or: export AGNES_API_KEY='sk-your-key' (Linux/macOS)")
        sys.exit(1)
    return key


def list_models():
    key = get_api_key()
    headers = {"Authorization": f"Bearer {key}"}
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{API_BASE}/models", headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}")
            return
        data = resp.json()
        models = data.get("data", [])
        print("Available Models:")
        print("-" * 60)
        for m in models:
            mid = m.get("id", "?")
            endpoints = m.get("supported_endpoint_types", [])
            print(f"  {mid:30s}  endpoints: {endpoints}")
        print("-" * 60)
        video_models = [m for m in models if "video" in m.get("id", "")]
        if video_models:
            print("\nVideo Generation Models:")
            for m in video_models:
                print(f"  - {m['id']}")


def query_task(client, task_id, headers):
    resp = client.get(f"{API_BASE}/videos/{task_id}", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def download_video(client, url, output_path):
    print(f"  下载视频...", flush=True)
    with client.stream("GET", url, timeout=300, follow_redirects=True) as resp:
        resp.raise_for_status()
        total = 0
        with open(output_path, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=8192):
                f.write(chunk)
                total += len(chunk)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  已保存: {output_path} ({size_mb:.2f} MB)", flush=True)
    return output_path


async def agnes_video_generate(
    params: list,
    model_name: str = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Generate videos using Agnes API.

    Args:
        params: List of dicts, each containing:
            - video_name (str): Name identifier for the video
            - prompt (str, required): Video description text
            - duration (int, optional): Video length in seconds
            - size (str, optional): Video resolution (e.g. "720p")
        model_name: Model name, default "agnes-video-v2.0"
        timeout: Total polling timeout in seconds

    Returns:
        dict with:
            - status: "success" | "partial_success" | "error"
            - success_list: [{"video_name": str, "task_id": str, "url": str}]
            - error_list: [{"video_name": str, "error": str}]
    """
    api_key = get_api_key()
    model = model_name or DEFAULT_MODEL
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    success_list = []
    error_list = []

    with httpx.Client(timeout=30) as client:
        for i, param in enumerate(params):
            name = param.get("video_name", f"video_{i+1}")
            prompt = param.get("prompt", "")
            size = param.get("size", DEFAULT_SIZE)

            print(f"\n[{i+1}/{len(params)}] 生成视频: {name}", flush=True)
            print(f"  提示词: {prompt[:80]}...", flush=True)

            # Step 1: Create video task
            body = {"model": model, "prompt": prompt, "size": size}

            try:
                resp = client.post(f"{API_BASE}/videos", headers=headers, json=body)

                if resp.status_code == 429:
                    err_msg = f"限流: {resp.text[:200]}"
                    print(f"  {err_msg}", flush=True)
                    print(f"  等待 65s 后重试...", flush=True)
                    await asyncio.sleep(65)
                    resp = client.post(f"{API_BASE}/videos", headers=headers, json=body)

                if resp.status_code != 200:
                    err_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    print(f"  Error: {err_msg}", flush=True)
                    error_list.append({"video_name": name, "error": err_msg})
                    continue

                task_data = resp.json()
                task_id = task_data.get("id")
                print(f"  任务ID: {task_id}", flush=True)
                print(f"  分辨率: {task_data.get('size', '?')}", flush=True)
                print(f"  时长: {task_data.get('seconds', '?')}s", flush=True)

            except Exception as e:
                err_msg = str(e)
                print(f"  异常: {err_msg}", flush=True)
                error_list.append({"video_name": name, "error": err_msg})
                continue

            # Step 2: Poll for completion
            start_time = time.time()
            video_url = None

            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    err_msg = f"超时 ({timeout}s)"
                    print(f"  {err_msg}", flush=True)
                    error_list.append({"video_name": name, "error": err_msg, "task_id": task_id})
                    break

                try:
                    task = query_task(client, task_id, headers)
                    status = task.get("status")
                    progress = task.get("progress", 0)

                    print(f"  [{int(elapsed)}s] {status} ({progress}%)", flush=True)

                    if status == "completed":
                        # Video URL is in remixed_from_video_id field
                        video_url = task.get("remixed_from_video_id")
                        if not video_url:
                            # Try other fields
                            video_url = task.get("video_url") or task.get("output_url")

                        if video_url:
                            print(f"  视频URL: {video_url}", flush=True)
                            success_list.append({
                                "video_name": name,
                                "task_id": task_id,
                                "url": video_url,
                            })
                        else:
                            err_msg = f"任务完成但未找到视频URL: {task}"
                            print(f"  {err_msg}", flush=True)
                            error_list.append({"video_name": name, "error": err_msg, "task_id": task_id})
                        break

                    elif status == "failed":
                        err_msg = f"生成失败: {task.get('error', 'unknown error')}"
                        print(f"  {err_msg}", flush=True)
                        error_list.append({"video_name": name, "error": err_msg, "task_id": task_id})
                        break

                except Exception as e:
                    print(f"  查询异常: {e}", flush=True)

                await asyncio.sleep(POLL_INTERVAL)

            # Cooldown between tasks (rate limit: 1 req/min)
            if i < len(params) - 1:
                print(f"  冷却 65s (限流)...", flush=True)
                await asyncio.sleep(65)

    status = "success" if not error_list else ("partial_success" if success_list else "error")

    return {
        "status": status,
        "success_list": success_list,
        "error_list": error_list,
    }


def main():
    parser = argparse.ArgumentParser(
        description="使用 Agnes AI API 生成视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-p", "--prompt", type=str, default=None,
        help="视频描述文本"
    )
    parser.add_argument(
        "-n", "--name", default="agnes_video",
        help="输出视频名称标识 (default: agnes_video)"
    )
    parser.add_argument(
        "-m", "--model", default=DEFAULT_MODEL,
        help=f"模型名称 (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "-d", "--duration", type=int, default=DEFAULT_DURATION,
        help=f"视频时长(秒) (default: {DEFAULT_DURATION})"
    )
    parser.add_argument(
        "-s", "--size", default=DEFAULT_SIZE,
        help=f"视频分辨率 (default: {DEFAULT_SIZE})"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="输出文件路径 (default: <name>.mp4)"
    )
    parser.add_argument(
        "-q", "--query-task", type=str, default=None,
        help="查询指定任务ID的状态"
    )
    parser.add_argument(
        "-t", "--timeout", type=int, default=DEFAULT_TIMEOUT,
        help=f"轮询超时时间(秒) (default: {DEFAULT_TIMEOUT})"
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="列出可用模型"
    )
    parser.add_argument(
        "--no-download", action="store_true",
        help="仅生成不下载视频"
    )

    args = parser.parse_args()

    # List models mode
    if args.list_models:
        list_models()
        return

    # Query task mode
    if args.query_task:
        key = get_api_key()
        headers = {"Authorization": f"Bearer {key}"}
        with httpx.Client(timeout=30) as client:
            task = query_task(client, args.query_task, headers)
            print(json.dumps(task, ensure_ascii=False, indent=2))
        return

    # Generate mode
    if not args.prompt:
        parser.error("--prompt is required for video generation")

    params = [{
        "video_name": args.name,
        "prompt": args.prompt,
        "size": args.size,
        "duration": args.duration,
    }]

    result = asyncio.run(agnes_video_generate(params, model_name=args.model, timeout=args.timeout))

    print(f"\n{'='*60}")
    print(f"Status: {result['status']}")
    print(f"Success: {len(result['success_list'])}, Errors: {len(result['error_list'])}")

    # Download successful videos
    if result["success_list"] and not args.no_download:
        for item in result["success_list"]:
            name = item["video_name"]
            url = item["url"]
            out_path = args.output if args.output else f"{name}.mp4"

            with httpx.Client(timeout=30) as client:
                download_video(client, url, out_path)
            item["local_path"] = os.path.abspath(out_path)
            print(f"  任务ID: {item['task_id']}")
            print(f"  URL: {url}")

    if result["error_list"]:
        print("\nErrors:")
        for err in result["error_list"]:
            tid = err.get("task_id", "N/A")
            print(f"  - {err['video_name']}: {err['error'][:100]} (task: {tid})")

    print(f"\n{json.dumps(result, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
