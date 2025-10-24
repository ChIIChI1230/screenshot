from __future__ import annotations

"""
截图接收服务器（Flask）

功能：
- 接收客户端上传的截图（multipart/form-data）
- 按日期创建目录保存文件
- 文件名包含时间戳与来源主机名
"""

import os
import logging
import datetime as dt
from pathlib import Path
from typing import Tuple
from dataclasses import dataclass

from flask import Flask, request, jsonify
import json


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('server.log', encoding='utf-8')
        ]
    )


@dataclass
class ServerConfig:
    host: str
    port: int
    storage_dir: Path


def load_server_config() -> ServerConfig:
    """从 `config.json` 读取服务器配置，失败则采用内置默认值。"""
    config_path = Path(__file__).with_name("config.json")
    host = "0.0.0.0"
    port = 8000
    storage_dir = Path("received_screenshots")
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            srv = data.get("server", {})
            host = str(srv.get("host", host))
            port = int(srv.get("port", port))
            storage_dir = Path(str(srv.get("storage_dir", str(storage_dir))))
        except Exception as e:
            # Use defaults on any config error
            logging.error("加载服务器配置错误: %s", e)
            pass
    return ServerConfig(host=host, port=port, storage_dir=storage_dir)


app = Flask(__name__)


@app.get("/health")
def health():
    """健康检查端点"""
    return jsonify({"status": "ok", "message": "Server is running"}), 200


@app.post("/upload")
def upload():
    """上传接口：要求字段 `file`，可包含 `timestamp` 与 `source`。"""
    if "file" not in request.files:
        return jsonify({"error": "missing file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    # Optional metadata
    ts = request.form.get("timestamp")
    source = request.form.get("source", "client")

    config = load_server_config()
    storage_dir = config.storage_dir
    # Ensure date-based directories
    now = dt.datetime.now(dt.timezone.utc)
    date_dir = storage_dir / now.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    # Build filename
    timestamp_for_name = ts or now.strftime("%Y%m%dT%H%M%S%fZ")
    safe_source = "".join(c for c in source if c.isalnum() or c in ("-", "_")) or "client"
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    fname = f"{timestamp_for_name}_{safe_source}{ext}"
    target = date_dir / fname

    file.save(target)
    logging.info(f"收到截图: {fname} 来自 {source}")

    return jsonify({"status": "ok", "path": str(target)})


def run_server() -> None:
    """启动 Flask 服务器。"""
    setup_logging()
    config = load_server_config()
    logging.info(f"正在启动截图服务器...")
    logging.info(f"服务器地址: {config.host}:{config.port}")
    logging.info(f"存储目录: {config.storage_dir}")
    app.run(host=config.host, port=config.port)


if __name__ == "__main__":
    run_server()


