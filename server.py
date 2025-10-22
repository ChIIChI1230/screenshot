from __future__ import annotations

"""
截图接收服务器（Flask）

功能：
- 接收客户端上传的截图（multipart/form-data）
- 按日期创建目录保存文件
- 文件名包含时间戳与来源主机名
"""

import os
import datetime as dt
from pathlib import Path
from typing import Tuple

from flask import Flask, request, jsonify
import json


def load_server_config() -> Tuple[str, int, Path]:
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
        except Exception:
            # Use defaults on any config error
            logging.error("Error loading server config: %s", e)
            pass
    return host, port, storage_dir


app = Flask(__name__)


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

    host, port, storage_dir = load_server_config()
    # Ensure date-based directories
    now = dt.datetime.utcnow()
    date_dir = storage_dir / now.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    # Build filename
    timestamp_for_name = ts or now.strftime("%Y%m%dT%H%M%S%fZ")
    safe_source = "".join(c for c in source if c.isalnum() or c in ("-", "_")) or "client"
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    fname = f"{timestamp_for_name}_{safe_source}{ext}"
    target = date_dir / fname

    file.save(target)

    return jsonify({"status": "ok", "path": str(target)})


def run_server() -> None:
    """启动 Flask 服务器。"""
    host, port, _ = load_server_config()
    app.run(host=host, port=port)


if __name__ == "__main__":
    run_server()


