"""
截图客户端核心模块

提供屏幕截图、上传和本地存储管理功能。
"""

import io
import time
import socket
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
from PIL import ImageGrab, Image

from ..utils.logger import get_logger
from ..utils.file_utils import ensure_directory, cleanup_old_files, get_file_count
from ..utils.network_utils import check_connection, upload_file, get_hostname
from .config import ClientConfig


class LocalImageStorage:
    """本地图片存储管理器"""
    
    def __init__(self, storage_dir: str, max_files: int = 1000, retention_hours: int = 24):
        self.storage_dir = Path(storage_dir)
        self.max_files = max_files
        self.retention_hours = retention_hours
        self.logger = get_logger(__name__)
        
        # 确保存储目录存在
        ensure_directory(str(self.storage_dir))
    
    def save_image(self, image_data: bytes, filename: str) -> Path:
        """
        保存图片到本地存储
        
        Args:
            image_data: 图片数据
            filename: 文件名
        
        Returns:
            保存的文件路径
        """
        file_path = self.storage_dir / filename
        file_path.write_bytes(image_data)
        return file_path
    
    def get_stored_files(self) -> List[Path]:
        """获取所有存储的图片文件"""
        if not self.storage_dir.exists():
            return []
        
        return [f for f in self.storage_dir.iterdir() if f.is_file()]
    
    def get_file_count(self) -> int:
        """获取存储的文件数量"""
        return get_file_count(str(self.storage_dir))
    
    def cleanup_old_files(self) -> int:
        """清理旧文件"""
        return cleanup_old_files(
            str(self.storage_dir),
            self.max_files,
            self.retention_hours
        )
    
    def remove_file(self, file_path: Path) -> bool:
        """删除指定文件"""
        try:
            file_path.unlink()
            return True
        except OSError as e:
            self.logger.error(f"删除文件失败 {file_path}: {e}")
            return False


class ScreenshotClient:
    """截图客户端"""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.local_storage = LocalImageStorage(
            str(config.local_storage_dir),
            config.max_local_files,
            config.local_file_retention_hours
        )
        self.is_running = False
        self._stop_event = threading.Event()
    
    def capture_screenshot(self) -> Optional[bytes]:
        """
        截取屏幕截图
        
        Returns:
            截图数据，如果失败则返回None
        """
        try:
            # 截取主显示器
            screenshot = ImageGrab.grab()
            
            # 转换为指定格式
            img_buffer = io.BytesIO()
            if self.config.image_format.upper() == "JPEG":
                screenshot.save(img_buffer, format="JPEG", quality=self.config.jpeg_quality)
            else:
                screenshot.save(img_buffer, format=self.config.image_format)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return None
    
    def generate_filename(self) -> str:
        """生成文件名"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        hostname = get_hostname()
        extension = "jpg" if self.config.image_format.upper() == "JPEG" else "png"
        return f"{timestamp}_{hostname}.{extension}"
    
    def upload_image(self, image_data: bytes, filename: str) -> bool:
        """
        上传图片到服务器
        
        Args:
            image_data: 图片数据
            filename: 文件名
        
        Returns:
            上传是否成功
        """
        try:
            # 准备上传数据
            files = {'file': (filename, io.BytesIO(image_data), 'image/jpeg')}
            data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': get_hostname()
            }
            
            # 发送请求
            response = requests.post(
                self.config.server_url,
                files=files,
                data=data,
                timeout=self.config.connection_timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'ok':
                self.logger.info(f"图片上传成功: {filename}")
                return True
            else:
                self.logger.error(f"服务器返回错误: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"上传失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"上传过程中发生错误: {e}")
            return False
    
    def save_local_copy(self, image_data: bytes, filename: str) -> Optional[Path]:
        """
        保存本地副本
        
        Args:
            image_data: 图片数据
            filename: 文件名
        
        Returns:
            保存的文件路径，如果失败则返回None
        """
        try:
            output_dir = ensure_directory(str(self.config.local_output_dir))
            file_path = output_dir / filename
            file_path.write_bytes(image_data)
            self.logger.info(f"本地副本已保存: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"保存本地副本失败: {e}")
            return None
    
    def upload_stored_images(self) -> int:
        """
        上传本地存储的图片
        
        Returns:
            成功上传的图片数量
        """
        uploaded_count = 0
        stored_files = self.local_storage.get_stored_files()
        
        for file_path in stored_files:
            if not self._stop_event.is_set():
                try:
                    image_data = file_path.read_bytes()
                    filename = file_path.name
                    
                    if self.upload_image(image_data, filename):
                        self.local_storage.remove_file(file_path)
                        uploaded_count += 1
                    else:
                        # 如果上传失败，保留文件下次再试
                        break
                        
                except Exception as e:
                    self.logger.error(f"上传存储图片失败 {file_path}: {e}")
                    break
        
        if uploaded_count > 0:
            self.logger.info(f"成功上传 {uploaded_count} 个本地图片")
        
        return uploaded_count
    
    def check_server_connection(self) -> bool:
        """检查服务器连接"""
        return check_connection(self.config.server_url, self.config.connection_timeout)
    
    def capture_and_upload_once(self) -> bool:
        """
        执行一次截图和上传
        
        Returns:
            操作是否成功
        """
        # 截取屏幕
        image_data = self.capture_screenshot()
        if image_data is None:
            return False
        
        filename = self.generate_filename()
        
        # 尝试上传
        upload_success = False
        if self.check_server_connection():
            upload_success = self.upload_image(image_data, filename)
        
        # 如果上传失败，保存到本地存储
        if not upload_success:
            self.local_storage.save_image(image_data, filename)
            self.logger.info(f"服务器不可用，图片已保存到本地: {filename}")
        
        # 保存本地副本（如果配置要求）
        if self.config.save_local_copy:
            self.save_local_copy(image_data, filename)
        
        return True
    
    def run(self):
        """运行客户端主循环"""
        self.is_running = True
        self._stop_event.clear()
        
        self.logger.info("客户端启动")
        self.logger.info(f"服务器地址: {self.config.server_url}")
        self.logger.info(f"截图间隔: {self.config.interval_seconds} 秒")
        
        # 检查本地存储
        local_file_count = self.local_storage.get_file_count()
        if local_file_count > 0:
            self.logger.info(f"发现 {local_file_count} 个本地图片")
            if self.check_server_connection():
                self.upload_stored_images()
        
        # 立即执行一次截图
        self.logger.info("执行初始截图")
        self.capture_and_upload_once()
        
        # 主循环
        last_execution_time = time.time()
        cleanup_counter = 0
        
        while self.is_running and not self._stop_event.is_set():
            current_time = time.time()
            
            # 检查是否到了执行时间
            if current_time - last_execution_time >= self.config.interval_seconds:
                self.logger.info("执行截图任务")
                self.capture_and_upload_once()
                last_execution_time = current_time
                
                # 尝试上传本地存储的图片
                if self.local_storage.get_file_count() > 0:
                    if self.check_server_connection():
                        self.upload_stored_images()
            
            # 定期清理过期文件
            cleanup_counter += 1
            if cleanup_counter >= 600:  # 每10分钟清理一次
                cleanup_counter = 0
                cleaned_count = self.local_storage.cleanup_old_files()
                if cleaned_count > 0:
                    self.logger.info(f"清理了 {cleaned_count} 个过期文件")
            
            time.sleep(0.1)  # 短暂休眠
        
        self.logger.info("客户端已停止")
    
    def stop(self):
        """停止客户端"""
        self.is_running = False
        self._stop_event.set()
        self.logger.info("正在停止客户端...")


def run_client():
    """运行客户端的便捷函数"""
    from .config import load_client_config
    from ..utils.logger import setup_logging
    
    # 设置日志
    setup_logging(log_file="client.log")
    
    # 加载配置
    config = load_client_config()
    
    # 创建并运行客户端
    client = ScreenshotClient(config)
    
    try:
        client.run()
    except KeyboardInterrupt:
        client.stop()
    except Exception as e:
        client.logger.error(f"客户端运行错误: {e}")
        raise
