#!/usr/bin/env python3
"""
测试GUI功能
"""

import sys
import tkinter as tk
from tkinter import messagebox

def test_client_gui():
    """测试客户端GUI"""
    try:
        from client_gui import ClientGUI
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        app = ClientGUI(root)
        print("✅ 客户端GUI导入成功")
        
        # 测试配置加载
        app.load_config()
        print("✅ 客户端配置加载成功")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"❌ 客户端GUI测试失败: {e}")
        return False

def test_server_gui():
    """测试服务端GUI"""
    try:
        from server_gui import ServerGUI
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        app = ServerGUI(root)
        print("✅ 服务端GUI导入成功")
        
        # 测试配置加载
        app.load_config()
        print("✅ 服务端配置加载成功")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"❌ 服务端GUI测试失败: {e}")
        return False

def test_core_modules():
    """测试核心模块"""
    try:
        from client import load_client_config, LocalImageStorage
        from server import load_server_config
        print("✅ 核心模块导入成功")
        
        # 测试配置加载
        client_config = load_client_config()
        server_config = load_server_config()
        print("✅ 配置加载成功")
        
        return True
    except Exception as e:
        print(f"❌ 核心模块测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("GUI功能测试")
    print("="*40)
    
    tests = [
        ("核心模块", test_core_modules),
        ("客户端GUI", test_client_gui),
        ("服务端GUI", test_server_gui),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n测试 {name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {name} 测试失败")
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过!")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
