"""
服务端GUI界面

提供图形化的服务端控制界面。
"""

import logging
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path

from ..core.server import ScreenshotServer
from ..core.config import ServerConfig
from ..utils.logger import get_logger
from .gui_utils import GUILogHandler, GUIThreadSafe, create_log_entry


class ServerGUI:
    """服务端GUI界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("奥力给-服务端")
        self.root.geometry("700x500")
        
        self.logger = get_logger(__name__)
        self.server = None
        self.server_thread = None
        self.is_running = False
        
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
            from ..core.config import load_server_config
            config = load_server_config()
            self.host_var.set(config.host)
            self.port_var.set(str(config.port))
            self.storage_dir_var.set(str(config.storage_dir))
        except Exception as e:
            self.log_message(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            from ..core.config import config_manager
            config = ServerConfig(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                storage_dir=self.storage_dir_var.get()
            )
            
            config_manager.save_server_config(config)
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
            
            # 在新进程中启动服务端
            import sys
            import os
            
            # 获取项目根目录（从GUI文件位置计算）
            gui_dir = os.path.dirname(__file__)  # src/screenshot_tool/gui
            core_dir = os.path.join(gui_dir, '..', 'core')  # src/screenshot_tool/core
            server_script = os.path.join(core_dir, 'server_main.py')
            
            # 设置子进程的环境变量，确保能找到模块
            # 从GUI目录到src目录：gui -> .. -> .. -> src
            src_dir = os.path.abspath(os.path.join(gui_dir, '..', '..'))
            # 项目根目录：从src目录到根目录
            project_root = os.path.abspath(os.path.join(src_dir, '..'))
            env = os.environ.copy()
            env['PYTHONPATH'] = src_dir
            
            # 添加调试信息
            self.log_message(f"启动服务端脚本: {server_script}")
            self.log_message(f"工作目录: {project_root}")
            self.log_message(f"PYTHONPATH: {env['PYTHONPATH']}")
            
            self.server_process = subprocess.Popen(
                [sys.executable, '-u', server_script],  # -u: 无缓冲模式
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # 无缓冲
                env=env,
                cwd=project_root
            )
            
            # 启动日志监控线程
            self.log_thread = threading.Thread(target=self.monitor_server_logs, daemon=True)
            self.log_thread.start()
            
            self.log_message("服务端启动成功")
            
        except Exception as e:
            self.log_message(f"启动服务端失败: {e}")
            messagebox.showerror("错误", f"启动服务端失败: {e}")
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("启动失败")
    
    def monitor_server_logs(self):
        """监控服务端日志"""
        import time
        import threading
        import queue
        
        try:
            self.log_message("开始监控服务端日志...")
            
            # 创建队列来收集输出
            output_queue = queue.Queue()
            
            def read_output(pipe, queue, prefix=""):
                """读取管道输出的线程函数"""
                try:
                    for line in iter(pipe.readline, ''):
                        if line:
                            queue.put(f"{prefix}{line.strip()}")
                except Exception as e:
                    queue.put(f"[ERROR] 读取输出失败: {e}")
            
            # 启动读取线程
            stdout_thread = threading.Thread(
                target=read_output, 
                args=(self.server_process.stdout, output_queue, ""),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=read_output, 
                args=(self.server_process.stderr, output_queue, "[ERROR] "),
                daemon=True
            )
            
            stdout_thread.start()
            stderr_thread.start()
            
            # 主循环：处理队列中的输出
            while self.is_running and self.server_process.poll() is None:
                try:
                    # 非阻塞获取队列中的消息
                    message = output_queue.get(timeout=0.1)
                    self.log_message(message)
                except queue.Empty:
                    # 没有新消息，继续循环
                    pass
                except Exception as e:
                    self.log_message(f"处理输出时出错: {e}")
                
                # 检查进程是否已结束
                if self.server_process.poll() is not None:
                    self.log_message(f"服务端进程已结束，退出码: {self.server_process.poll()}")
                    break
                        
        except Exception as e:
            self.log_message(f"日志监控错误: {e}")
            import traceback
            self.log_message(f"错误详情: {traceback.format_exc()}")
        finally:
            self.is_running = False
            GUIThreadSafe.safe_update(self.root, self.on_server_stopped)
    
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
        
        # 终止服务端进程
        if hasattr(self, 'server_process') and self.server_process:
            try:
                self.server_process.terminate()
                # 等待进程结束
                self.server_process.wait(timeout=5)
                self.log_message("服务端已停止")
            except subprocess.TimeoutExpired:
                # 如果进程没有在5秒内结束，强制杀死
                self.server_process.kill()
                self.log_message("服务端已强制停止")
            except Exception as e:
                self.log_message(f"停止服务端时出错: {e}")
        
        # 更新UI状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("服务端已停止")
    
    def update_status(self, message: str):
        """更新服务状态"""
        def update():
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, f"{message}\n")
            self.status_text.config(state=tk.DISABLED)
            self.status_text.see(tk.END)
        
        GUIThreadSafe.safe_update(self.status_text, update)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def log_message(self, message: str):
        """添加日志消息"""
        log_entry = create_log_entry(message)
        
        def update_log():
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
        
        GUIThreadSafe.safe_update(self.log_text, update_log)


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
