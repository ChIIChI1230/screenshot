"""
截图服务端核心模块

提供HTTP服务器功能，接收和存储客户端上传的截图。
"""

import os
import logging
import warnings
import threading
import datetime as dt
import sys
from pathlib import Path
from typing import Dict, Any

from flask import Flask, request, jsonify

from ..utils.logger import get_logger, setup_logging
from ..utils.file_utils import ensure_directory
from .config import ServerConfig


class ScreenshotServer:
    """截图服务端"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.app = Flask(__name__)
        self._setup_routes()
        
        # 确保存储目录存在
        ensure_directory(str(self.config.storage_dir))
        
        # 添加停止标志
        self._stop_event = threading.Event()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/health")
        def health():
            """健康检查端点"""
            return {"status": "ok", "message": "Server is running"}, 200
        
        @self.app.post("/upload")
        def upload():
            """上传接口"""
            return self._handle_upload()
    
    def _handle_upload(self) -> tuple[Dict[str, Any], int]:
        """
        处理上传请求
        
        Returns:
            响应数据和状态码
        """
        try:
            # 简化日志，只记录关键信息
            # print("收到上传请求", flush=True)
            # self.logger.info("收到上传请求")
            # self.logger.info(f"请求文件: {list(request.files.keys())}")
            # self.logger.info(f"请求表单: {list(request.form.keys())}")
            
            # 检查是否有文件
            if "file" not in request.files:
                self.logger.error("缺少文件字段")
                return {"error": "missing file"}, 400
            
            file = request.files["file"]
            if file.filename == "":
                return {"error": "empty filename"}, 400
            
            # 获取可选元数据
            timestamp = request.form.get("timestamp")
            source = request.form.get("source", "client")
            
            # 创建日期目录
            now = dt.datetime.now(dt.timezone.utc)
            from pathlib import Path
            storage_path = Path(self.config.storage_dir)
            date_dir = storage_path / now.strftime("%Y-%m-%d")
            ensure_directory(str(date_dir))
            
            # 生成文件名
            timestamp_for_name = timestamp or now.strftime("%Y%m%dT%H%M%S%fZ")
            # 清理时间戳中的无效字符（Windows文件名不能包含 : 等字符）
            safe_timestamp = "".join(c for c in timestamp_for_name if c.isalnum() or c in ("-", "_", "T", "Z", "."))
            safe_source = "".join(c for c in source if c.isalnum() or c in ("-", "_")) or "client"
            ext = os.path.splitext(file.filename)[1] or ".jpg"
            filename = f"{safe_timestamp}_{safe_source}{ext}"
            
            # 保存文件
            target_path = date_dir / filename
            file.save(str(target_path))
            
            # 只输出简化的上传成功信息
            print(f"[UPLOAD] 收到截图: {filename} 来自 {source}", flush=True)
            
            return {"status": "ok", "path": str(target_path)}, 200
            
        except Exception as e:
            import traceback
            self.logger.error(f"处理上传请求失败: {e}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return {"error": "internal server error"}, 500
    
    def run(self):
        """运行服务器"""
        print("正在启动截图服务器...", flush=True)
        
        self.logger.info("正在启动截图服务器...")
        self.logger.info(f"服务器地址: {self.config.host}:{self.config.port}")
        self.logger.info(f"存储目录: {self.config.storage_dir}")
        
        try:
            # 使用waitress作为WSGI服务器，避免Flask开发服务器警告
            from waitress import serve
            
            print("使用Waitress WSGI服务器启动...", flush=True)
            self.logger.info("使用Waitress WSGI服务器启动...")
            
            print("服务端启动成功，正在监听连接...", flush=True)
            
            serve(
                self.app,
                host=self.config.host,
                port=self.config.port,
                threads=4
            )
        except ImportError:
            # 如果没有安装waitress，回退到Flask开发服务器
            self.logger.warning("未找到Waitress，使用Flask开发服务器（不推荐用于生产环境）")
            self.app.run(
                host=self.config.host,
                port=self.config.port,
                debug=False,
                threaded=True
            )
        except Exception as e:
            self.logger.error(f"服务器运行错误: {e}")
            raise
    
    def stop(self):
        """停止服务器"""
        self.logger.info("正在停止服务器...")
        self._stop_event.set()


def run_server():
    """运行服务端的便捷函数"""
    print("开始设置日志...", flush=True)
    
    from .config import load_server_config
    from ..utils.logger import setup_logging
    
    print("正在设置日志...", flush=True)
    
    # 抑制Flask开发服务器警告（可以通过环境变量控制）
    suppress_warnings = os.getenv('SUPPRESS_FLASK_WARNINGS', 'true').lower() == 'true'
    if suppress_warnings:
        warnings.filterwarnings("ignore", message=".*development server.*")
        warnings.filterwarnings("ignore", message=".*Werkzeug.*")
    
    # 设置日志（同时输出到文件和控制台）
    setup_logging(log_file="server.log")
    print("日志设置完成", flush=True)
    
    # 确保所有logger都输出到stdout
    import logging
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream.name == '<stdout>':
            handler.stream.reconfigure(line_buffering=True)
    
    # 加载配置
    print("正在加载配置...", flush=True)
    config = load_server_config()
    print("配置加载完成", flush=True)
    
    # 创建并运行服务器
    print("正在创建服务端实例...", flush=True)
    server = ScreenshotServer(config)
    print("服务端实例创建成功，准备启动...", flush=True)
    server.run()


# 为了兼容性，保留原有的函数名
def load_server_config() -> ServerConfig:
    """从配置文件加载服务器配置"""
    from .config import load_server_config as _load_config
    return _load_config()


def setup_logging():
    """设置日志配置"""
    from ..utils.logger import setup_logging as _setup_logging
    return _setup_logging(log_file="server.log")
