"""
配置管理模块

处理客户端和服务端的配置加载、验证和管理。
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class ClientConfig:
    """客户端配置"""
    server_url: str
    interval_seconds: int = 60
    image_format: str = "JPEG"
    jpeg_quality: int = 85
    save_local_copy: bool = False
    local_output_dir: str = "local_screenshots"
    max_retries: int = 3
    retry_delay: int = 5
    connection_timeout: int = 10
    local_storage_dir: str = "local_screenshots"
    max_local_files: int = 1000
    local_file_retention_hours: int = 24


@dataclass
class ServerConfig:
    """服务端配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    storage_dir: str = "received_screenshots"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not self.config_file.exists():
                self.logger.warning(f"配置文件 {self.config_file} 不存在，将使用默认配置")
                return {}
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.info(f"成功加载配置文件: {self.config_file}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            raise
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            raise
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已保存到: {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            raise
    
    def load_client_config(self) -> ClientConfig:
        """加载客户端配置"""
        config_data = self.load_config()
        client_config = config_data.get('client', {})
        
        return ClientConfig(
            server_url=client_config.get('server_url', ''),
            interval_seconds=client_config.get('interval_seconds', 60),
            image_format=client_config.get('image_format', 'JPEG'),
            jpeg_quality=client_config.get('jpeg_quality', 85),
            save_local_copy=client_config.get('save_local_copy', False),
            local_output_dir=client_config.get('local_output_dir', 'local_screenshots'),
            max_retries=client_config.get('max_retries', 3),
            retry_delay=client_config.get('retry_delay', 5),
            connection_timeout=client_config.get('connection_timeout', 10),
            local_storage_dir=client_config.get('local_storage_dir', 'local_screenshots'),
            max_local_files=client_config.get('max_local_files', 1000),
            local_file_retention_hours=client_config.get('local_file_retention_hours', 24)
        )
    
    def load_server_config(self) -> ServerConfig:
        """加载服务端配置"""
        config_data = self.load_config()
        server_config = config_data.get('server', {})
        
        return ServerConfig(
            host=server_config.get('host', '0.0.0.0'),
            port=server_config.get('port', 8000),
            storage_dir=server_config.get('storage_dir', 'received_screenshots')
        )
    
    def save_client_config(self, config: ClientConfig) -> None:
        """保存客户端配置"""
        config_data = self.load_config()
        config_data['client'] = {
            'server_url': config.server_url,
            'interval_seconds': config.interval_seconds,
            'image_format': config.image_format,
            'jpeg_quality': config.jpeg_quality,
            'save_local_copy': config.save_local_copy,
            'local_output_dir': config.local_output_dir,
            'max_retries': config.max_retries,
            'retry_delay': config.retry_delay,
            'connection_timeout': config.connection_timeout,
            'local_storage_dir': config.local_storage_dir,
            'max_local_files': config.max_local_files,
            'local_file_retention_hours': config.local_file_retention_hours
        }
        self.save_config(config_data)
    
    def save_server_config(self, config: ServerConfig) -> None:
        """保存服务端配置"""
        config_data = self.load_config()
        config_data['server'] = {
            'host': config.host,
            'port': config.port,
            'storage_dir': config.storage_dir
        }
        self.save_config(config_data)


# 全局配置管理器实例
config_manager = ConfigManager()


def load_client_config() -> ClientConfig:
    """加载客户端配置的便捷函数"""
    return config_manager.load_client_config()


def load_server_config() -> ServerConfig:
    """加载服务端配置的便捷函数"""
    return config_manager.load_server_config()
