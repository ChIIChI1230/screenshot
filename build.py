#!/usr/bin/env python3
"""
打包脚本 - 将客户端和服务端打包成exe文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理错误"""
    print(f"\n{'='*50}")
    print(f"正在执行: {description}")
    print(f"命令: {cmd}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ 成功!")
        if result.stdout:
            print("输出:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败: {e}")
        if e.stdout:
            print("标准输出:", e.stdout)
        if e.stderr:
            print("错误输出:", e.stderr)
        return False


def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")
    
    required_packages = [
        'pyinstaller',
        'pillow',
        'requests',
        'flask',
        'schedule',
        'waitress'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n缺少依赖: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    return True


def build_client():
    """打包客户端"""
    print("\n" + "="*60)
    print("开始打包客户端...")
    print("="*60)
    
    # 清理旧的构建文件
    if Path("dist").exists():
        shutil.rmtree("dist")
    if Path("build").exists():
        shutil.rmtree("build")
    
    # 使用spec文件打包
    cmd = "pyinstaller build_client.spec"
    success = run_command(cmd, "打包客户端")
    
    if success:
        exe_path = Path("dist/截图客户端.exe")
        if exe_path.exists():
            print(f"✅ 客户端打包成功: {exe_path}")
            return True
        else:
            print("❌ 客户端exe文件未找到")
            return False
    else:
        print("❌ 客户端打包失败")
        return False


def build_server():
    """打包服务端"""
    print("\n" + "="*60)
    print("开始打包服务端...")
    print("="*60)
    
    # 清理旧的构建文件
    if Path("dist").exists():
        shutil.rmtree("dist")
    if Path("build").exists():
        shutil.rmtree("build")
    
    # 使用spec文件打包
    cmd = "pyinstaller build_server.spec"
    success = run_command(cmd, "打包服务端")
    
    if success:
        exe_path = Path("dist/截图服务端.exe")
        if exe_path.exists():
            print(f"✅ 服务端打包成功: {exe_path}")
            return True
        else:
            print("❌ 服务端exe文件未找到")
            return False
    else:
        print("❌ 服务端打包失败")
        return False


def create_release_package():
    """创建发布包"""
    print("\n" + "="*60)
    print("创建发布包...")
    print("="*60)
    
    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    
    release_dir.mkdir()
    
    # 复制exe文件
    files_to_copy = [
        ("dist/截图客户端.exe", "截图客户端.exe"),
        ("dist/截图服务端.exe", "截图服务端.exe"),
        ("config.json", "config.json"),
        ("README.md", "README.md"),
    ]
    
    for src, dst in files_to_copy:
        src_path = Path(src)
        if src_path.exists():
            shutil.copy2(src_path, release_dir / dst)
            print(f"✅ 复制 {src} -> {dst}")
        else:
            print(f"❌ 文件不存在: {src}")
    
    # 创建启动脚本
    start_client_bat = release_dir / "启动客户端.bat"
    start_client_bat.write_text("""@echo off
echo 启动截图客户端...
"截图客户端.exe"
pause
""", encoding='utf-8')
    
    start_server_bat = release_dir / "启动服务端.bat"
    start_server_bat.write_text("""@echo off
echo 启动截图服务端...
"截图服务端.exe"
pause
""", encoding='utf-8')
    
    print(f"✅ 发布包已创建: {release_dir.absolute()}")
    return True


def main():
    """主函数"""
    print("截图工具打包脚本")
    print("="*60)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺少的依赖")
        return False
    
    # 打包客户端
    if not build_client():
        print("\n❌ 客户端打包失败")
        return False
    
    # 打包服务端
    if not build_server():
        print("\n❌ 服务端打包失败")
        return False
    
    # 创建发布包
    if not create_release_package():
        print("\n❌ 创建发布包失败")
        return False
    
    print("\n" + "="*60)
    print("🎉 打包完成!")
    print("="*60)
    print("发布包位置: release/")
    print("包含文件:")
    print("  - 截图客户端.exe")
    print("  - 截图服务端.exe")
    print("  - 启动客户端.bat")
    print("  - 启动服务端.bat")
    print("  - config.json")
    print("  - README.md")
    print("\n使用方法:")
    print("1. 先运行服务端: 双击 启动服务端.bat")
    print("2. 再运行客户端: 双击 启动客户端.bat")
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
