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
import logging
import signal
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

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
    max_retries: int = 3
    retry_delay: int = 5
    connection_timeout: int = 10
    # 本地存储相关配置
    local_storage_dir: Path = Path("local_screenshots")
    max_local_files: int = 1000
    local_file_retention_hours: int = 24


class LocalImageStorage:
    """本地图片存储管理器"""
    
    def __init__(self, storage_dir: Path, max_files: int = 1000, retention_hours: int = 24):
        self.storage_dir = storage_dir
        self.max_files = max_files
        self.retention_hours = retention_hours
        self.lock = threading.Lock()
        self.storage_dir.mkdir(exist_ok=True)
        
    def save_image(self, image_bytes: bytes, timestamp: str, source: str) -> bool:
        """保存图片到本地"""
        with self.lock:
            # 检查文件数量限制
            if self.get_file_count() >= self.max_files:
                logging.warning(f"Local storage is full ({self.max_files}), dropping oldest image")
                self._remove_oldest()
            
            filename = f"{timestamp}_{source}.jpg"
            filepath = self.storage_dir / filename
            
            try:
                filepath.write_bytes(image_bytes)
                logging.info(f"Image saved locally: {filename}")
                return True
            except Exception as e:
                logging.error(f"Failed to save image locally: {e}")
                return False
    
    def get_pending_images(self) -> List[Path]:
        """获取待上传的本地图片文件列表"""
        with self.lock:
            files = list(self.storage_dir.glob("*.jpg"))
            # 按创建时间排序，处理最旧的
            files.sort(key=lambda x: x.stat().st_mtime)
            return files
    
    def remove_image(self, filepath: Path) -> bool:
        """删除本地图片文件"""
        with self.lock:
            try:
                if filepath.exists():
                    filepath.unlink()
                    logging.info(f"Removed local image: {filepath.name}")
                    return True
                return False
            except Exception as e:
                logging.error(f"Failed to remove local image: {e}")
                return False
    
    def _remove_oldest(self):
        """移除最旧的图片"""
        files = list(self.storage_dir.glob("*.jpg"))
        if files:
            files.sort(key=lambda x: x.stat().st_mtime)
            files[0].unlink()
    
    def get_file_count(self) -> int:
        """获取本地文件数量"""
        return len(list(self.storage_dir.glob("*.jpg")))
    
    def cleanup_old_files(self):
        """清理过期文件"""
        with self.lock:
            current_time = datetime.now(timezone.utc)
            files_to_remove = []
            
            for filepath in self.storage_dir.glob("*.jpg"):
                file_time = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
                age_hours = (current_time - file_time).total_seconds() / 3600
                
                if age_hours > self.retention_hours:
                    files_to_remove.append(filepath)
            
            for filepath in files_to_remove:
                try:
                    filepath.unlink()
                    logging.info(f"Cleaned up old local image: {filepath.name}")
                except Exception as e:
                    logging.error(f"Failed to clean up old file {filepath.name}: {e}")
    
    def clear_all(self):
        """清空所有本地文件"""
        with self.lock:
            for file in self.storage_dir.glob("*.jpg"):
                file.unlink()
            logging.info("Local storage cleared")


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('client.log', encoding='utf-8')
        ]
    )


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
            "max_retries": 3,
            "retry_delay": 5,
            "connection_timeout": 10,
            "local_storage_dir": "local_screenshots",
            "max_local_files": 1000,
            "local_file_retention_hours": 24,
        }
    }
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            logging.warning(f"Failed to load config: {e}, using defaults")
    c = data.get("client", {})
    return ClientConfig(
        server_url=str(c.get("server_url", "http://127.0.0.1:8000/upload")),
        interval_seconds=int(c.get("interval_seconds", 10)),
        image_format=str(c.get("image_format", "JPEG")),
        jpeg_quality=int(c.get("jpeg_quality", 80)),
        save_local_copy=bool(c.get("save_local_copy", False)),
        local_output_dir=Path(str(c.get("local_output_dir", "screenshots"))),
        max_retries=int(c.get("max_retries", 3)),
        retry_delay=int(c.get("retry_delay", 5)),
        connection_timeout=int(c.get("connection_timeout", 10)),
        local_storage_dir=Path(str(c.get("local_storage_dir", "local_screenshots"))),
        max_local_files=int(c.get("max_local_files", 1000)),
        local_file_retention_hours=int(c.get("local_file_retention_hours", 24)),
    )


def check_server_connection(config: ClientConfig) -> bool:
    """检查服务器是否可用"""
    try:
        # 尝试连接服务器
        response = requests.get(
            config.server_url.replace('/upload', '/health'), 
            timeout=config.connection_timeout
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        # 如果健康检查端点不存在，尝试HEAD请求到upload端点
        try:
            response = requests.head(config.server_url, timeout=config.connection_timeout)
            return True
        except requests.exceptions.RequestException:
            return False


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
    """通过 HTTP POST 发送截图到服务器，支持重试机制。

    失败时返回 None，不抛异常，方便定时任务继续执行。
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    hostname = socket.gethostname()
    files = {"file": (f"{timestamp}.jpg", image_bytes, "image/jpeg")}
    data = {"timestamp": timestamp, "source": hostname}
    
    for attempt in range(config.max_retries + 1):
        try:
            resp = requests.post(
                config.server_url, 
                files=files, 
                data=data, 
                timeout=config.connection_timeout
            )
            if resp.status_code == 200:
                logging.info(f"Screenshot uploaded successfully: {resp.status_code}")
                return resp
            else:
                logging.warning(f"Server returned status {resp.status_code}")
                if attempt < config.max_retries:
                    logging.info(f"Retrying in {config.retry_delay} seconds... (attempt {attempt + 1}/{config.max_retries})")
                    time.sleep(config.retry_delay)
                else:
                    logging.error(f"Failed to upload after {config.max_retries} retries")
                    return None
                    
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error (attempt {attempt + 1}/{config.max_retries + 1}): {e}")
            if attempt < config.max_retries:
                logging.info(f"Retrying in {config.retry_delay} seconds...")
                time.sleep(config.retry_delay)
            else:
                logging.error("Server appears to be down")
                return None
                
        except requests.exceptions.Timeout as e:
            logging.error(f"Request timeout (attempt {attempt + 1}/{config.max_retries + 1}): {e}")
            if attempt < config.max_retries:
                logging.info(f"Retrying in {config.retry_delay} seconds...")
                time.sleep(config.retry_delay)
            else:
                logging.error("Request timeout after all retries")
                return None
                
        except Exception as e:
            logging.error(f"Unexpected error (attempt {attempt + 1}/{config.max_retries + 1}): {e}")
            if attempt < config.max_retries:
                logging.info(f"Retrying in {config.retry_delay} seconds...")
                time.sleep(config.retry_delay)
            else:
                logging.error("Unexpected error after all retries")
                return None
    
    return None


def upload_local_images(local_storage: LocalImageStorage, config: ClientConfig) -> None:
    """上传本地存储的图片"""
    pending_images = local_storage.get_pending_images()
    
    if not pending_images:
        return
    
    logging.info(f"Found {len(pending_images)} local images to upload")
    
    for filepath in pending_images:
        try:
            # 从文件名解析时间戳和源
            filename = filepath.name
            if '_' in filename:
                timestamp, source = filename.rsplit('_', 1)
                source = source.replace('.jpg', '')
            else:
                # 如果文件名格式不正确，使用文件修改时间
                timestamp = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                source = socket.gethostname()
            
            # 读取图片数据
            image_bytes = filepath.read_bytes()
            
            # 尝试上传
            files = {"file": (filename, image_bytes, "image/jpeg")}
            data = {"timestamp": timestamp, "source": source}
            
            resp = requests.post(
                config.server_url,
                files=files,
                data=data,
                timeout=config.connection_timeout
            )
            
            if resp.status_code == 200:
                logging.info(f"Local image uploaded successfully: {filename}")
                local_storage.remove_image(filepath)
            else:
                logging.warning(f"Failed to upload local image {filename}: {resp.status_code}")
                # 上传失败时保留文件，下次再试
                
        except Exception as e:
            logging.error(f"Error uploading local image {filepath.name}: {e}")
            # 出错时保留文件，下次再试


def job_once(config: ClientConfig, local_storage: Optional[LocalImageStorage] = None) -> None:
    """执行一次截图与上传流程。"""
    try:
        # 先截取屏幕
        img = capture_primary_monitor()
        image_bytes = encode_image(img, config.image_format, config.jpeg_quality)
        
        # 保存本地副本（如果配置了）
        if config.save_local_copy:
            config.local_output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            (config.local_output_dir / f"{ts}.jpg").write_bytes(image_bytes)
            logging.info(f"Screenshot saved locally: {config.local_output_dir / f'{ts}.jpg'}")
        
        # 检查服务器连接
        if not check_server_connection(config):
            logging.warning("Server is not available, saving screenshot locally")
            # 服务器不可用时，保存到本地存储
            if local_storage:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                hostname = socket.gethostname()
                if local_storage.save_image(image_bytes, timestamp, hostname):
                    logging.info("Screenshot saved to local storage for later upload")
                else:
                    logging.error("Failed to save screenshot to local storage")
            return
        
        # 服务器可用时，尝试上传
        if send_screenshot(image_bytes, config):
            logging.info("Screenshot uploaded successfully")
        else:
            # 上传失败，保存到本地
            if local_storage:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                hostname = socket.gethostname()
                if local_storage.save_image(image_bytes, timestamp, hostname):
                    logging.info("Upload failed, screenshot saved to local storage")
                else:
                    logging.error("Upload failed and failed to save locally")
        
    except Exception as e:
        logging.error(f"Error in job_once: {e}")
        # 即使出错也继续运行，不中断定时任务


# 全局变量用于优雅关闭
shutdown_requested = False


def signal_handler(signum, frame):
    """处理中断信号，实现优雅关闭"""
    global shutdown_requested
    logging.info("Received shutdown signal, stopping gracefully...")
    shutdown_requested = True


def run_client() -> None:
    """启动客户端：按配置的秒数周期性截图并上传。"""
    global shutdown_requested
    
    # 设置日志
    setup_logging()
    logging.info("Starting screenshot client...")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    
    config = load_client_config()
    logging.info(f"Client configuration loaded: {config.server_url}")
    
    # 初始化本地存储
    local_storage = LocalImageStorage(
        config.local_storage_dir, 
        config.max_local_files, 
        config.local_file_retention_hours
    )
    
    # 检查本地存储状态
    local_file_count = local_storage.get_file_count()
    if local_file_count > 0:
        logging.info(f"Found {local_file_count} local images from previous session")
    else:
        logging.info("No local images found")
    
    # 检查初始连接
    if not check_server_connection(config):
        logging.warning("Server is not available at startup, but will continue trying...")
    else:
        logging.info("Server connection verified")
        # 服务器可用时，尝试上传本地图片
        if local_file_count > 0:
            logging.info("Server is available, uploading local images...")
            upload_local_images(local_storage, config)
    
    schedule.clear()
    schedule.every(config.interval_seconds).seconds.do(job_once, config=config, local_storage=local_storage)
    
    # 立即执行一次
    logging.info("Running initial screenshot...")
    job_once(config, local_storage)
    
    logging.info(f"Client started, taking screenshots every {config.interval_seconds} seconds")
    logging.info("Press Ctrl+C to stop gracefully")
    
    try:
        while not shutdown_requested:
            schedule.run_pending()
            
            # 定期清理过期文件和尝试上传本地图片（每5分钟检查一次）
            if local_storage:
                local_storage.cleanup_old_files()
                # 如果服务器可用，尝试上传本地图片
                if check_server_connection(config):
                    upload_local_images(local_storage, config)
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
    finally:
        logging.info("Client stopped gracefully")
        schedule.clear()
        
        # 显示本地存储状态
        local_file_count = local_storage.get_file_count()
        if local_file_count > 0:
            logging.info(f"Local storage contains {local_file_count} images that will be processed on next startup")


if __name__ == "__main__":
    run_client()


