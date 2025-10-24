"""
GUI工具类

提供GUI界面通用的工具和辅助类。
"""

import threading
import logging
from datetime import datetime
from typing import Callable


class GUILogHandler(logging.Handler):
    """GUI日志处理器"""
    
    def __init__(self, log_callback: Callable[[str], None]):
        super().__init__()
        self.log_callback = log_callback
        # 设置格式
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    def emit(self, record):
        try:
            message = self.format(record)
            self.log_callback(message)
        except Exception as e:
            # 如果GUI日志处理器出错，至少打印到控制台
            print(f"GUI日志处理器错误: {e}")
            pass


class GUIThreadSafe:
    """GUI线程安全工具类"""
    
    @staticmethod
    def safe_update(widget, update_func: Callable, *args, **kwargs):
        """
        安全地更新GUI组件
        
        Args:
            widget: GUI组件
            update_func: 更新函数
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if threading.current_thread() is threading.main_thread():
            update_func(*args, **kwargs)
        else:
            widget.after(0, lambda: update_func(*args, **kwargs))


def format_timestamp() -> str:
    """格式化当前时间戳"""
    return datetime.now().strftime("%H:%M:%S")


def create_log_entry(message: str) -> str:
    """创建日志条目"""
    timestamp = format_timestamp()
    return f"[{timestamp}] {message}\n"
