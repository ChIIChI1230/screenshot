from __future__ import annotations

"""
截图客户端

功能：
- 定时截取主显示器画面
- 将截图以 HTTP POST 方式上传到服务器
- 可选在本地保存一份副本

依赖：Pillow(ImageGrab)、requests、schedule
"""

import io
import time
import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from PIL import ImageGrab, Image
import schedule


@dataclass
class ClientConfig:
    server_url: str
    interval_seconds: int
    image_format: str
    jpeg_quality: int
    save_local_copy: bool
    local_output_dir: Path


def load_client_config() -> ClientConfig:
    """从 `config.json` 读取客户端配置，读取失败则返回内置默认值。"""
    config_path = Path(__file__).with_name("config.json")
    # Defaults
    data = {
        "client": {
            "server_url": "http://127.0.0.1:8000/upload",
            "interval_seconds": 10,
            "image_format": "JPEG",
            "jpeg_quality": 80,
            "save_local_copy": False,
            "local_output_dir": "screenshots",
        }
    }
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    c = data.get("client", {})
    return ClientConfig(
        server_url=str(c.get("server_url", "http://127.0.0.1:8000/upload")),
        interval_seconds=int(c.get("interval_seconds", 10)),
        image_format=str(c.get("image_format", "JPEG")),
        jpeg_quality=int(c.get("jpeg_quality", 80)),
        save_local_copy=bool(c.get("save_local_copy", False)),
        local_output_dir=Path(str(c.get("local_output_dir", "screenshots"))),
    )


def capture_primary_monitor() -> Image.Image:
    """截取主显示器画面。

    注：在 Windows 桌面会话下，ImageGrab.grab() 默认抓取主屏。
    """
    return ImageGrab.grab()


def encode_image(img: Image.Image, fmt: str, quality: int) -> bytes:
    """将 PIL 图片编码为字节流。

    - JPEG：使用指定质量，并开启 optimize 以减小体积。
    """
    buf = io.BytesIO()
    params = {}
    if fmt.upper() == "JPEG":
        params["quality"] = quality
        params["optimize"] = True
    img.convert("RGB").save(buf, format=fmt, **params)
    return buf.getvalue()


def send_screenshot(image_bytes: bytes, config: ClientConfig) -> Optional[requests.Response]:
    """通过 HTTP POST 发送截图到服务器。

    失败时返回 None，不抛异常，方便定时任务继续执行。
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    hostname = socket.gethostname()
    files = {"file": (f"{timestamp}.jpg", image_bytes, "image/jpeg")}
    data = {"timestamp": timestamp, "source": hostname}
    try:
        resp = requests.post(config.server_url, files=files, data=data, timeout=10)
        logging.info(f"Screenshot uploaded successfully: {resp.status_code}")
        return resp
    except Exception:
        return None


def job_once(config: ClientConfig) -> None:
    """执行一次截图与上传流程。"""
    img = capture_primary_monitor()
    image_bytes = encode_image(img, config.image_format, config.jpeg_quality)
    if config.save_local_copy:
        config.local_output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        (config.local_output_dir / f"{ts}.jpg").write_bytes(image_bytes)
    send_screenshot(image_bytes, config)


def run_client() -> None:
    """启动客户端：按配置的秒数周期性截图并上传。"""
    config = load_client_config()
    schedule.clear()
    schedule.every(config.interval_seconds).seconds.do(job_once, config=config)
    # Run immediately once
    job_once(config)
    while True:
        schedule.run_pending()
        time.sleep(0.5)


if __name__ == "__main__":
    run_client()


