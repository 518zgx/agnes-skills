# -*- coding: utf-8 -*-
"""
Agnes AI Image Generation Script
Uses Agnes API to generate images from text prompts.

Usage:
    python agnes_image_generate.py -p "A cute cat" -s 1024x1024 -o output.png
    python agnes_image_generate.py -p "Cat" "Dog" -g
    python agnes_image_generate.py --list-models
"""

import argparse
import asyncio
import os
import sys
import time
import json
import io
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


API_BASE = "https://apihub.agnes-ai.com/v1"
DEFAULT_MODEL = "agnes-image-2.1-flash"
DEFAULT_SIZE = "1024x1024"
DEFAULT_TIMEOUT = 120


def get_api_key():
    """Get API key from environment variable."""
    key = os.environ.get("AGNES_API_KEY")
    if not key:
        print("Error: AGNES_API_KEY not found in environment variables.")
        print("Set it with: $env:AGNES_API_KEY = 'sk-your-key' (PowerShell)")
        print("Or: export AGNES_API_KEY='sk-your-key' (Linux/macOS)")
        sys.exit(1)
    return key


def list_models():
    """List available models from Agnes API."""
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
        # Filter image models
        image_models = [m for m in models if "image" in m.get("id", "")]
        if image_models:
            print("\nImage Generation Models:")
            for m in image_models:
                print(f"  - {m['id']}")


async def agnes_generate(
    params: list,
    model_name: str = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Generate images using Agnes API.

    Args:
        params: List of dicts, each containing:
            - prompt (str, required): Image description
            - size (str, optional): Image dimensions, default "1024x1024"
        model_name: Model name, default "agnes-image-2.1-flash"
        timeout: Request timeout in seconds

    Returns:
        dict with:
            - status: "success" | "partial_success" | "error"
            - success_list: [{"prompt": str, "url": str}]
            - error_list: [{"prompt": str, "error": str}]
    """
    api_key = get_api_key()
    model = model_name or DEFAULT_MODEL
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    success_list = []
    error_list = []

    with httpx.Client(timeout=timeout) as client:
        for i, param in enumerate(params):
            prompt = param.get("prompt", "")
            size = param.get("size", DEFAULT_SIZE)

            print(f"\n[{i+1}/{len(params)}] Generating: {prompt[:60]}...", flush=True)

            body = {
                "model": model,
                "prompt": prompt,
                "size": size,
            }

            try:
                resp = client.post(
                    f"{API_BASE}/images/generations",
                    headers=headers,
                    json=body,
                )

                if resp.status_code != 200:
                    err_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    print(f"  Error: {err_msg}", flush=True)
                    error_list.append({"prompt": prompt, "error": err_msg})
                    continue

                data = resp.json()
                images = data.get("data", [])

                if images and images[0].get("url"):
                    url = images[0]["url"]
                    print(f"  URL: {url}", flush=True)
                    success_list.append({"prompt": prompt, "url": url})
                else:
                    err_msg = f"No image URL in response: {data}"
                    print(f"  Error: {err_msg}", flush=True)
                    error_list.append({"prompt": prompt, "error": err_msg})

            except Exception as e:
                err_msg = str(e)
                print(f"  Exception: {err_msg}", flush=True)
                error_list.append({"prompt": prompt, "error": err_msg})

            # Cooldown between requests
            if i < len(params) - 1:
                print("  Cooling down 3s...", flush=True)
                await asyncio.sleep(3)

    status = "success" if not error_list else ("partial_success" if success_list else "error")

    return {
        "status": status,
        "success_list": success_list,
        "error_list": error_list,
    }


def download_image(url: str, output_path: str, target_size=None):
    """
    Download image from URL and optionally resize.

    Args:
        url: Image URL
        output_path: Local file path to save
        target_size: Optional (width, height) tuple for resizing
    """
    print(f"  Downloading...", flush=True)
    with httpx.Client(timeout=120) as client:
        resp = client.get(url, follow_redirects=True)
        resp.raise_for_status()

    img = Image.open(io.BytesIO(resp.content)).convert("RGBA")

    if target_size:
        print(f"  Resizing: {img.size} -> {target_size}", flush=True)
        img = img.resize(target_size, Image.LANCZOS)

    img.save(output_path, "PNG")
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Saved: {output_path} ({size_kb:.1f} KB)", flush=True)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Agnes AI API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-p", "--prompt", nargs="+", required=False,
        help="Image description text (supports multiple prompts)"
    )
    parser.add_argument(
        "-m", "--model", default=DEFAULT_MODEL,
        help=f"Model name (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "-s", "--size", default=DEFAULT_SIZE,
        help=f"Image dimensions (default: {DEFAULT_SIZE})"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output file path (default: agnes_output_<timestamp>.png)"
    )
    parser.add_argument(
        "-g", "--group", action="store_true",
        help="Enable batch generation for multiple prompts"
    )
    parser.add_argument(
        "-t", "--timeout", type=int, default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})"
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="List available models and exit"
    )

    args = parser.parse_args()

    # List models mode
    if args.list_models:
        list_models()
        return

    # Generate mode
    if not args.prompt:
        parser.error("--prompt is required for image generation")

    prompts = args.prompt if args.group else [args.prompt[0]]

    params = [{"prompt": p, "size": args.size} for p in prompts]

    result = asyncio.run(agnes_generate(params, model_name=args.model, timeout=args.timeout))

    print(f"\n{'='*60}")
    print(f"Status: {result['status']}")
    print(f"Success: {len(result['success_list'])}, Errors: {len(result['error_list'])}")

    # Download successful images
    if result["success_list"]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for i, item in enumerate(result["success_list"]):
            if args.output and len(result["success_list"]) == 1:
                out_path = args.output
            else:
                out_path = f"agnes_output_{timestamp}_{i+1}.png"

            download_image(item["url"], out_path)
            print(f"  URL: {item['url']}")

    if result["error_list"]:
        print("\nErrors:")
        for err in result["error_list"]:
            print(f"  - {err['prompt'][:50]}: {err['error'][:100]}")

    # Output JSON for programmatic use
    print(f"\n{json.dumps(result, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    main()
