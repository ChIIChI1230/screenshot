#!/usr/bin/env python3
"""
截图客户端GUI界面
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

# 导入客户端模块
from client import load_client_config, ClientConfig, setup_logging
import logging


class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("奥利给-客户端")
        self.root.geometry("800x600")
        
        # 客户端进程
        self.client_process = None
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
        config_frame = ttk.LabelFrame(main_frame, text="客户端配置", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 服务器地址
        ttk.Label(config_frame, text="服务器地址:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.server_url_var = tk.StringVar()
        server_entry = ttk.Entry(config_frame, textvariable=self.server_url_var, width=40)
        server_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        
        # 截图间隔
        ttk.Label(config_frame, text="截图间隔(秒):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.interval_var = tk.StringVar()
        interval_entry = ttk.Entry(config_frame, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 图片质量
        ttk.Label(config_frame, text="图片质量(1-100):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.quality_var = tk.StringVar()
        quality_entry = ttk.Entry(config_frame, textvariable=self.quality_var, width=10)
        quality_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 保存本地副本
        self.save_local_var = tk.BooleanVar()
        save_local_check = ttk.Checkbutton(config_frame, text="保存本地副本", variable=self.save_local_var)
        save_local_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # 本地输出目录
        ttk.Label(config_frame, text="本地输出目录:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.local_dir_var = tk.StringVar()
        local_dir_frame = ttk.Frame(config_frame)
        local_dir_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        local_dir_entry = ttk.Entry(local_dir_frame, textvariable=self.local_dir_var, width=30)
        local_dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(local_dir_frame, text="浏览", command=self.browse_local_dir).grid(row=0, column=1, padx=(5, 0))
        
        # 本地存储目录
        ttk.Label(config_frame, text="本地存储目录:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.storage_dir_var = tk.StringVar()
        storage_dir_frame = ttk.Frame(config_frame)
        storage_dir_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        storage_dir_entry = ttk.Entry(storage_dir_frame, textvariable=self.storage_dir_var, width=30)
        storage_dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(storage_dir_frame, text="浏览", command=self.browse_storage_dir).grid(row=0, column=1, padx=(5, 0))
        
        # 最大本地文件数
        ttk.Label(config_frame, text="最大本地文件数:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.max_files_var = tk.StringVar()
        max_files_entry = ttk.Entry(config_frame, textvariable=self.max_files_var, width=10)
        max_files_entry.grid(row=6, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 文件保留时间
        ttk.Label(config_frame, text="文件保留时间(小时):").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.retention_var = tk.StringVar()
        retention_entry = ttk.Entry(config_frame, textvariable=self.retention_var, width=10)
        retention_entry.grid(row=7, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="启动客户端", command=self.start_client)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止客户端", command=self.stop_client, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(button_frame, text="保存配置", command=self.save_config).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).grid(row=0, column=3)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        config_frame.columnconfigure(1, weight=1)
        local_dir_frame.columnconfigure(0, weight=1)
        storage_dir_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def browse_local_dir(self):
        """浏览本地输出目录"""
        directory = filedialog.askdirectory(title="选择本地输出目录")
        if directory:
            self.local_dir_var.set(directory)
    
    def browse_storage_dir(self):
        """浏览本地存储目录"""
        directory = filedialog.askdirectory(title="选择本地存储目录")
        if directory:
            self.storage_dir_var.set(directory)
    
    def load_config(self):
        """加载配置"""
        try:
            config = load_client_config()
            self.server_url_var.set(config.server_url)
            self.interval_var.set(str(config.interval_seconds))
            self.quality_var.set(str(config.jpeg_quality))
            self.save_local_var.set(config.save_local_copy)
            self.local_dir_var.set(str(config.local_output_dir))
            self.storage_dir_var.set(str(config.local_storage_dir))
            self.max_files_var.set(str(config.max_local_files))
            self.retention_var.set(str(config.local_file_retention_hours))
        except Exception as e:
            self.log_message(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            config_data = {
                "client": {
                    "server_url": self.server_url_var.get(),
                    "interval_seconds": int(self.interval_var.get()),
                    "image_format": "JPEG",
                    "jpeg_quality": int(self.quality_var.get()),
                    "save_local_copy": self.save_local_var.get(),
                    "local_output_dir": self.local_dir_var.get(),
                    "max_retries": 3,
                    "retry_delay": 5,
                    "connection_timeout": 10,
                    "local_storage_dir": self.storage_dir_var.get(),
                    "max_local_files": int(self.max_files_var.get()),
                    "local_file_retention_hours": int(self.retention_var.get()),
                }
            }
            
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.log_message("配置保存成功")
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            self.log_message(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def start_client(self):
        """启动客户端"""
        if self.is_running:
            return
        
        try:
            # 验证配置
            if not self.server_url_var.get():
                messagebox.showerror("错误", "请输入服务器地址")
                return
            
            if not self.interval_var.get().isdigit() or int(self.interval_var.get()) <= 0:
                messagebox.showerror("错误", "截图间隔必须是正整数")
                return
            
            # 保存当前配置
            self.save_config()
            
            # 启动客户端进程
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set("客户端运行中...")
            
            # 在新线程中启动客户端
            self.client_thread = threading.Thread(target=self.run_client_process, daemon=True)
            self.client_thread.start()
            
            self.log_message("客户端启动成功")
            
        except Exception as e:
            self.log_message(f"启动客户端失败: {e}")
            messagebox.showerror("错误", f"启动客户端失败: {e}")
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("启动失败")
    
    def run_client_process(self):
        """运行客户端进程"""
        try:
            # 清理现有的日志处理器
            for handler in logging.getLogger().handlers[:]:
                logging.getLogger().removeHandler(handler)
            
            # 设置日志处理器
            log_handler = GUILogHandler(self.log_message)
            logging.getLogger().addHandler(log_handler)
            
            # 设置日志级别
            logging.getLogger().setLevel(logging.INFO)
            
            # 运行客户端主循环
            from client import LocalImageStorage, job_once, check_server_connection, upload_local_images
            
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
            
            # 记录启动时间，用于精确计算下次执行时间
            start_time = time.time()
            
            # 立即执行一次
            logging.info("正在执行初始截图...")
            job_once(config, local_storage)
            logging.info("初始截图任务完成")
            
            # 不再使用schedule库，改用精确的时间控制
            
            logging.info(f"客户端已启动，每 {config.interval_seconds} 秒截图一次")
            logging.info("按 Ctrl+C 优雅停止")
            
            # 主循环 - 使用精确的时间控制
            last_execution_time = start_time
            cleanup_counter = 0
            
            while self.is_running:
                current_time = time.time()
                
                # 检查是否到了执行时间
                if current_time - last_execution_time >= config.interval_seconds:
                    logging.info(f"定时任务触发，距离上次执行: {current_time - last_execution_time:.1f}秒")
                    job_once(config, local_storage)
                    last_execution_time = current_time
                    
                    # 截图任务完成后，立即检查是否有本地图片需要上传
                    if local_storage and local_storage.get_file_count() > 0:
                        if check_server_connection(config):
                            logging.info("检测到服务器可用，正在上传本地图片...")
                            upload_local_images(local_storage, config)
                
                # 定期清理过期文件（每5分钟检查一次）
                cleanup_counter += 1
                if cleanup_counter >= 600:  # 600 * 0.1 = 60秒
                    cleanup_counter = 0
                    if local_storage:
                        local_storage.cleanup_old_files()
                
                time.sleep(0.1)  # 更频繁的检查，提高精确度
                
        except Exception as e:
            self.log_message(f"客户端运行错误: {e}")
        finally:
            self.is_running = False
            self.root.after(0, self.on_client_stopped)
    
    def on_client_stopped(self):
        """客户端停止回调"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("客户端已停止")
        self.log_message("客户端已停止")
    
    def stop_client(self):
        """停止客户端"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.log_message("正在停止客户端...")
        
        # 清理定时任务
        try:
            # 不再使用schedule库，定时任务通过is_running标志控制
            self.log_message("定时任务已清理")
        except Exception as e:
            self.log_message(f"清理定时任务时出错: {e}")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
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


def main():
    """主函数"""
    root = tk.Tk()
    app = ClientGUI(root)
    
    # 设置窗口关闭事件
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("退出", "客户端正在运行，确定要退出吗？"):
                app.stop_client()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
