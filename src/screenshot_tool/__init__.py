"""
Screenshot Tool - 屏幕自动截图工具

一个支持客户端/服务器架构的屏幕截图工具，提供GUI界面和命令行界面。
"""

__version__ = "0.1.0"
__author__ = "Screenshot Tool Team"
__description__ = "屏幕自动截图工具（客户端/服务器）"

from .core.client import ScreenshotClient
from .core.server import ScreenshotServer
from .core.config import ConfigManager

__all__ = [
    "ScreenshotClient",
    "ScreenshotServer", 
    "ConfigManager",
    "__version__",
    "__author__",
    "__description__"
]
