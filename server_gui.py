#!/usr/bin/env python3
"""
截图服务端GUI界面
"""

import sys
import json
import threading
import time
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import os

# 导入服务端模块
from server import load_server_config, ServerConfig, run_server, setup_logging
import logging


class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("奥力给-服务端")
        self.root.geometry("700x500")
        
        # 服务端进程
        self.server_process = None
        self.is_running = False
        self.flask_server = None  # 初始化服务器引用
        
        # 创建界面
        self.create_widgets()
        self.load_config()
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="服务端配置", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 主机地址
        ttk.Label(config_frame, text="主机地址:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.host_var = tk.StringVar()
        host_entry = ttk.Entry(config_frame, textvariable=self.host_var, width=20)
        host_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 端口号
        ttk.Label(config_frame, text="端口号:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.port_var = tk.StringVar()
        port_entry = ttk.Entry(config_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 存储目录
        ttk.Label(config_frame, text="存储目录:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.storage_dir_var = tk.StringVar()
        storage_dir_frame = ttk.Frame(config_frame)
        storage_dir_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        storage_dir_entry = ttk.Entry(storage_dir_frame, textvariable=self.storage_dir_var, width=40)
        storage_dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(storage_dir_frame, text="浏览", command=self.browse_storage_dir).grid(row=0, column=1, padx=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="启动服务端", command=self.start_server)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止服务端", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(button_frame, text="保存配置", command=self.save_config).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).grid(row=0, column=3)
        
        # 服务状态
        status_frame = ttk.LabelFrame(main_frame, text="服务状态", padding="5")
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_text = tk.Text(status_frame, height=3, width=70, state=tk.DISABLED)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        config_frame.columnconfigure(1, weight=1)
        storage_dir_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def browse_storage_dir(self):
        """浏览存储目录"""
        directory = filedialog.askdirectory(title="选择存储目录")
        if directory:
            self.storage_dir_var.set(directory)
    
    def load_config(self):
        """加载配置"""
        try:
            config = load_server_config()
            self.host_var.set(config.host)
            self.port_var.set(str(config.port))
            self.storage_dir_var.set(str(config.storage_dir))
        except Exception as e:
            self.log_message(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            # 读取现有配置
            config_data = {}
            if Path("config.json").exists():
                with open("config.json", "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            
            # 更新服务端配置
            config_data["server"] = {
                "host": self.host_var.get(),
                "port": int(self.port_var.get()),
                "storage_dir": self.storage_dir_var.get()
            }
            
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.log_message("配置保存成功")
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            self.log_message(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def start_server(self):
        """启动服务端"""
        if self.is_running:
            return
        
        try:
            # 验证配置
            if not self.host_var.get():
                messagebox.showerror("错误", "请输入主机地址")
                return
            
            if not self.port_var.get().isdigit():
                messagebox.showerror("错误", "端口号必须是数字")
                return
            
            if not self.storage_dir_var.get():
                messagebox.showerror("错误", "请选择存储目录")
                return
            
            # 创建存储目录
            storage_dir = Path(self.storage_dir_var.get())
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存当前配置
            self.save_config()
            
            # 启动服务端进程
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set("服务端运行中...")
            
            # 更新服务状态
            self.update_status(f"服务地址: {self.host_var.get()}:{self.port_var.get()}")
            self.update_status(f"存储目录: {self.storage_dir_var.get()}")
            self.update_status("状态: 运行中")
            
            # 在新线程中启动服务端
            self.server_thread = threading.Thread(target=self.run_server_process, daemon=True)
            self.server_thread.start()
            
            self.log_message("服务端启动成功")
            
        except Exception as e:
            self.log_message(f"启动服务端失败: {e}")
            messagebox.showerror("错误", f"启动服务端失败: {e}")
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("启动失败")
    
    def run_server_process(self):
        """运行服务端进程"""
        try:
            # 设置日志处理器
            log_handler = GUILogHandler(self.log_message)
            logging.getLogger().addHandler(log_handler)
            
            # 导入必要的模块
            from server import load_server_config, setup_logging
            from flask import Flask
            import threading
            import time
            
            # 设置日志
            setup_logging()
            config = load_server_config()
            
            # 创建Flask应用
            app = Flask(__name__)
            
            # 添加路由
            @app.get("/health")
            def health():
                """健康检查端点"""
                return {"status": "ok", "message": "Server is running"}, 200
            
            @app.post("/upload")
            def upload():
                """上传接口"""
                from flask import request, jsonify
                import os
                import datetime as dt
                from pathlib import Path
                
                if "file" not in request.files:
                    return jsonify({"error": "missing file"}), 400

                file = request.files["file"]
                if file.filename == "":
                    return jsonify({"error": "empty filename"}), 400

                # Optional metadata
                ts = request.form.get("timestamp")
                source = request.form.get("source", "client")

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
            
            # 启动Flask服务器
            logging.info(f"正在启动截图服务器...")
            logging.info(f"服务器地址: {config.host}:{config.port}")
            logging.info(f"存储目录: {config.storage_dir}")
            
            # 使用threading启动服务器，这样可以控制停止
            def run_flask():
                try:
                    # 使用werkzeug的make_server来创建可控制的服务器
                    from werkzeug.serving import make_server
                    self.flask_server = make_server(config.host, config.port, app, threaded=True)
                    self.flask_server.serve_forever()
                except Exception as e:
                    logging.error(f"Flask服务器运行错误: {e}")
            
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            
            # 等待服务器启动
            time.sleep(1)
            
            # 等待停止信号
            while self.is_running and flask_thread.is_alive():
                time.sleep(0.1)
            
            # 停止服务器
            if flask_thread.is_alive():
                logging.info("正在停止服务器...")
                try:
                    if hasattr(self, 'flask_server') and self.flask_server:
                        self.flask_server.shutdown()
                        logging.info("服务器已优雅停止")
                except Exception as e:
                    logging.error(f"停止服务器时出错: {e}")
                
        except Exception as e:
            self.log_message(f"服务端运行错误: {e}")
        finally:
            self.is_running = False
            self.root.after(0, self.on_server_stopped)
    
    def on_server_stopped(self):
        """服务端停止回调"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("服务端已停止")
        self.log_message("服务端已停止")
        self.update_status("状态: 已停止")
    
    def stop_server(self):
        """停止服务端"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.log_message("正在停止服务端...")
        
        # 更新UI状态
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("正在停止...")
        
        # 注意：实际的停止逻辑在run_server_process中处理
    
    def update_status(self, message):
        """更新服务状态"""
        def update():
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, f"{message}\n")
            self.status_text.config(state=tk.DISABLED)
            self.status_text.see(tk.END)
        
        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.root.after(0, update)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
        
        # 确保在主线程中更新UI
        if threading.current_thread() is threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)


class GUILogHandler(logging.Handler):
    """GUI日志处理器"""
    
    def __init__(self, log_callback):
        super().__init__()
        self.log_callback = log_callback
    
    def emit(self, record):
        try:
            message = self.format(record)
            self.log_callback(message)
        except Exception:
            pass


def main():
    """主函数"""
    root = tk.Tk()
    app = ServerGUI(root)
    
    # 设置窗口关闭事件
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("退出", "服务端正在运行，确定要退出吗？"):
                app.stop_server()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
