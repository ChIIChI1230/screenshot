"""
核心功能模块

包含截图工具的核心业务逻辑：
- 客户端截图和上传功能
- 服务器接收和存储功能
- 配置管理
- 本地存储管理
"""

from .client import ScreenshotClient
from .server import ScreenshotServer
from .config import ConfigManager, ClientConfig, ServerConfig

__all__ = [
    "ScreenshotClient",
    "ScreenshotServer",
    "ConfigManager",
    "ClientConfig", 
    "ServerConfig"
]
