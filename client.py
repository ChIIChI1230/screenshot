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
                logging.warning(f"本地存储已满 ({self.max_files})，删除最旧的图片")
                self._remove_oldest()
            
            filename = f"{timestamp}_{source}.jpg"
            filepath = self.storage_dir / filename
            
            try:
                filepath.write_bytes(image_bytes)
                logging.info(f"图片已保存到本地: {filename}")
                return True
            except Exception as e:
                logging.error(f"保存图片到本地失败: {e}")
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
                    logging.info(f"已删除本地图片: {filepath.name}")
                    return True
                return False
            except Exception as e:
                logging.error(f"删除本地图片失败: {e}")
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
                    logging.info(f"已清理过期本地图片: {filepath.name}")
                except Exception as e:
                    logging.error(f"清理过期文件失败 {filepath.name}: {e}")
    
    def clear_all(self):
        """清空所有本地文件"""
        with self.lock:
            for file in self.storage_dir.glob("*.jpg"):
                file.unlink()
            logging.info("本地存储已清空")


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
            logging.warning(f"加载配置失败: {e}，使用默认配置")
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
        # 尝试连接健康检查端点
        response = requests.get(
            config.server_url.replace('/upload', '/health'), 
            timeout=config.connection_timeout
        )
        if response.status_code == 200:
            logging.debug("服务器健康检查通过")
            return True
        else:
            logging.debug(f"服务器健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logging.debug(f"健康检查端点连接失败: {e}")
        # 如果健康检查端点不可用，尝试连接upload端点
        try:
            response = requests.head(config.server_url, timeout=config.connection_timeout)
            if response.status_code in [200, 405]:  # 405表示方法不允许，但服务器可用
                logging.debug(f"upload端点连接成功: {response.status_code}")
                return True
            else:
                logging.debug(f"upload端点连接失败: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logging.debug(f"upload端点连接异常: {e}")
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
                logging.info(f"截图上传成功: {resp.status_code}")
                logging.info(f"截图已发送到服务器: {timestamp}_{hostname}.jpg")
                return resp
            else:
                logging.warning(f"服务器返回状态 {resp.status_code}")
                if attempt < config.max_retries:
                    logging.info(f"在 {config.retry_delay} 秒后重试... (尝试 {attempt + 1}/{config.max_retries})")
                    time.sleep(config.retry_delay)
                else:
                    logging.error(f"重试 {config.max_retries} 次后上传失败")
                    return None
                    
        except requests.exceptions.ConnectionError as e:
            logging.error(f"连接错误 (尝试 {attempt + 1}/{config.max_retries + 1}): {e}")
            if attempt < config.max_retries:
                logging.info(f"在 {config.retry_delay} 秒后重试...")
                time.sleep(config.retry_delay)
            else:
                logging.error("服务器似乎已关闭")
                return None
                
        except requests.exceptions.Timeout as e:
            logging.error(f"请求超时 (尝试 {attempt + 1}/{config.max_retries + 1}): {e}")
            if attempt < config.max_retries:
                logging.info(f"在 {config.retry_delay} 秒后重试...")
                time.sleep(config.retry_delay)
            else:
                logging.error("所有重试后请求超时")
                return None
                
        except Exception as e:
            logging.error(f"意外错误 (尝试 {attempt + 1}/{config.max_retries + 1}): {e}")
            if attempt < config.max_retries:
                logging.info(f"在 {config.retry_delay} 秒后重试...")
                time.sleep(config.retry_delay)
            else:
                logging.error("所有重试后出现意外错误")
                return None
    
    return None


def upload_local_images(local_storage: LocalImageStorage, config: ClientConfig) -> None:
    """上传本地存储的图片"""
    pending_images = local_storage.get_pending_images()
    
    if not pending_images:
        return
    
    logging.info(f"发现 {len(pending_images)} 个本地图片待上传")
    
    success_count = 0
    fail_count = 0
    
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
            
            logging.info(f"正在上传本地图片: {filename}")
            
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
                logging.info(f"本地图片上传成功: {filename}")
                local_storage.remove_image(filepath)
                success_count += 1
            else:
                logging.warning(f"上传本地图片失败 {filename}: {resp.status_code}")
                fail_count += 1
                # 上传失败时保留文件，下次再试
                
        except Exception as e:
            logging.error(f"上传本地图片时出错 {filepath.name}: {e}")
            fail_count += 1
            # 出错时保留文件，下次再试
    
    # 总结上传结果
    if success_count > 0 or fail_count > 0:
        logging.info(f"本地图片上传完成: 成功 {success_count} 个，失败 {fail_count} 个")


def job_once(config: ClientConfig, local_storage: Optional[LocalImageStorage] = None) -> None:
    """执行一次截图与上传流程。"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    hostname = socket.gethostname()
    
    try:
        logging.info(f"开始截图任务: {timestamp}")
        
        # 先截取屏幕
        img = capture_primary_monitor()
        image_bytes = encode_image(img, config.image_format, config.jpeg_quality)
        logging.info(f"截图完成，图片大小: {len(image_bytes)} 字节")
        
        # 保存本地副本（如果配置了）
        if config.save_local_copy:
            config.local_output_dir.mkdir(parents=True, exist_ok=True)
            local_file = config.local_output_dir / f"{timestamp}.jpg"
            local_file.write_bytes(image_bytes)
            logging.info(f"截图已保存到本地: {local_file}")
        
        # 检查服务器连接
        if not check_server_connection(config):
            logging.warning("服务器不可用，正在保存截图到本地存储")
            # 服务器不可用时，保存到本地存储
            if local_storage:
                if local_storage.save_image(image_bytes, timestamp, hostname):
                    logging.info(f"截图已保存到本地存储: {timestamp}_{hostname}.jpg")
                    logging.info("等待服务器恢复后自动上传")
                else:
                    logging.error("保存截图到本地存储失败")
            else:
                logging.error("本地存储未启用，截图丢失")
            return
        
        # 服务器可用时，先尝试上传本地图片
        if local_storage and local_storage.get_file_count() > 0:
            logging.info("服务器可用，正在上传本地图片...")
            upload_local_images(local_storage, config)
        
        # 然后上传当前截图
        logging.info("正在上传当前截图...")
        result = send_screenshot(image_bytes, config)
        
        if result:
            logging.info(f"截图上传成功: {timestamp}_{hostname}.jpg")
        else:
            logging.warning("截图上传失败，正在保存到本地存储")
            # 上传失败，保存到本地
            if local_storage:
                if local_storage.save_image(image_bytes, timestamp, hostname):
                    logging.info(f"截图已保存到本地存储: {timestamp}_{hostname}.jpg")
                    logging.info("等待服务器恢复后自动上传")
                else:
                    logging.error("上传失败且保存到本地也失败")
            else:
                logging.error("上传失败且本地存储未启用，截图丢失")
        
    except Exception as e:
        logging.error(f"截图任务失败: {e}")
        logging.error(f"任务时间戳: {timestamp}")
        # 即使出错也继续运行，不中断定时任务


# 全局变量用于优雅关闭
shutdown_requested = False


def signal_handler(signum, frame):
    """处理中断信号，实现优雅关闭"""
    global shutdown_requested
    logging.info("收到关闭信号，正在优雅停止...")
    shutdown_requested = True


def run_client() -> None:
    """启动客户端：按配置的秒数周期性截图并上传。"""
    global shutdown_requested
    
    # 设置日志
    setup_logging()
    logging.info("正在启动截图客户端...")
    
    # 设置信号处理（仅在主线程中设置）
    try:
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    except ValueError:
        # 在非主线程中无法设置信号处理，这是正常的
        logging.info("在GUI环境中运行，跳过信号处理设置")
    
    config = load_client_config()
    logging.info(f"客户端配置已加载: {config.server_url}")
    
    # 初始化本地存储
    local_storage = LocalImageStorage(
        config.local_storage_dir, 
        config.max_local_files, 
        config.local_file_retention_hours
    )
    
    # 检查本地存储状态
    local_file_count = local_storage.get_file_count()
    if local_file_count > 0:
        logging.info(f"发现 {local_file_count} 个本地图片来自上次会话")
    else:
        logging.info("未发现本地图片")
    
    # 检查初始连接
    if not check_server_connection(config):
        logging.warning("启动时服务器不可用，但将继续尝试...")
    else:
        logging.info("服务器连接已验证")
        # 服务器可用时，尝试上传本地图片
        if local_file_count > 0:
            logging.info("服务器可用，正在上传本地图片...")
            upload_local_images(local_storage, config)
    
    # 使用精确的时间控制替代schedule
    start_time = time.time()
    last_execution_time = start_time
    cleanup_counter = 0
    
    # 立即执行一次
    logging.info("正在执行初始截图...")
    job_once(config, local_storage)
    
    logging.info(f"客户端已启动，每 {config.interval_seconds} 秒截图一次")
    logging.info("按 Ctrl+C 优雅停止")
    
    try:
        while not shutdown_requested:
            current_time = time.time()
            
            # 检查是否到了执行时间
            if current_time - last_execution_time >= config.interval_seconds:
                job_once(config, local_storage)
                last_execution_time = current_time
            
            # 定期清理过期文件和尝试上传本地图片（每5分钟检查一次）
            cleanup_counter += 1
            if cleanup_counter >= 600:  # 600 * 0.5 = 300秒 = 5分钟
                cleanup_counter = 0
                if local_storage:
                    local_storage.cleanup_old_files()
                    # 如果服务器可用，尝试上传本地图片
                    if check_server_connection(config):
                        upload_local_images(local_storage, config)
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        logging.info("收到键盘中断信号")
    finally:
        logging.info("客户端已优雅停止")
        
        # 显示本地存储状态
        local_file_count = local_storage.get_file_count()
        if local_file_count > 0:
            logging.info(f"本地存储包含 {local_file_count} 个图片，将在下次启动时处理")


if __name__ == "__main__":
    run_client()


