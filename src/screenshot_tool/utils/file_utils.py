"""
文件处理工具

提供文件操作相关的工具函数。
"""

import os
import time
from pathlib import Path
from typing import List, Optional


def ensure_directory(directory: str) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
    
    Returns:
        Path对象
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_old_files(
    directory: str,
    max_files: int = 1000,
    retention_hours: int = 24,
    file_pattern: str = "*"
) -> int:
    """
    清理旧文件
    
    Args:
        directory: 目录路径
        max_files: 最大文件数
        retention_hours: 文件保留时间（小时）
        file_pattern: 文件匹配模式
    
    Returns:
        清理的文件数量
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        return 0
    
    files = list(directory_path.glob(file_pattern))
    if not files:
        return 0
    
    # 按修改时间排序
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    current_time = time.time()
    retention_seconds = retention_hours * 3600
    cleaned_count = 0
    
    # 清理超时文件
    for file_path in files:
        file_age = current_time - file_path.stat().st_mtime
        if file_age > retention_seconds:
            try:
                file_path.unlink()
                cleaned_count += 1
            except OSError:
                pass  # 忽略删除失败的文件
    
    # 如果文件数仍然超过限制，删除最旧的文件
    remaining_files = [f for f in files if f.exists()]
    if len(remaining_files) > max_files:
        files_to_delete = remaining_files[max_files:]
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                cleaned_count += 1
            except OSError:
                pass  # 忽略删除失败的文件
    
    return cleaned_count


def get_file_count(directory: str, file_pattern: str = "*") -> int:
    """
    获取目录中的文件数量
    
    Args:
        directory: 目录路径
        file_pattern: 文件匹配模式
    
    Returns:
        文件数量
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        return 0
    
    return len(list(directory_path.glob(file_pattern)))


def get_directory_size(directory: str) -> int:
    """
    获取目录大小（字节）
    
    Args:
        directory: 目录路径
    
    Returns:
        目录大小（字节）
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        return 0
    
    total_size = 0
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            try:
                total_size += file_path.stat().st_size
            except OSError:
                pass  # 忽略无法访问的文件
    
    return total_size
