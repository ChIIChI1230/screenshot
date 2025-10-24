"""
网络工具

提供网络连接检查和HTTP请求相关的工具函数。
"""

import requests
import socket
from typing import Optional, Dict, Any
from urllib.parse import urlparse


def check_connection(url: str, timeout: int = 10) -> bool:
    """
    检查网络连接是否可用
    
    Args:
        url: 要检查的URL
        timeout: 超时时间（秒）
    
    Returns:
        连接是否可用
    """
    try:
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        # 检查TCP连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        return result == 0
        
    except Exception:
        return False


def check_http_connection(url: str, timeout: int = 10) -> bool:
    """
    检查HTTP连接是否可用
    
    Args:
        url: 要检查的URL
        timeout: 超时时间（秒）
    
    Returns:
        HTTP连接是否可用
    """
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 500
    except Exception:
        return False


def upload_file(
    url: str,
    file_path: str,
    additional_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    上传文件到指定URL
    
    Args:
        url: 上传URL
        file_path: 文件路径
        additional_data: 额外的表单数据
        timeout: 超时时间（秒）
    
    Returns:
        上传结果字典
    """
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            data = additional_data or {}
            
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=timeout
            )
            
            response.raise_for_status()
            return response.json()
            
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'success': False}
    except Exception as e:
        return {'error': str(e), 'success': False}


def get_local_ip() -> Optional[str]:
    """
    获取本地IP地址
    
    Returns:
        本地IP地址，如果获取失败则返回None
    """
    try:
        # 连接到一个远程地址来获取本地IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        return None


def get_hostname() -> str:
    """
    获取主机名
    
    Returns:
        主机名
    """
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"
