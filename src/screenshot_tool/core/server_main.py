#!/usr/bin/env python3
"""
服务端启动脚本

独立运行服务端的脚本。
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, src_dir)

def main():
    """主函数"""
    try:
        print("正在启动服务端...", flush=True)
        
        print("开始导入server模块...", flush=True)
        from screenshot_tool.core.server import run_server
        print("服务端模块导入成功，开始运行...", flush=True)
        
        print("开始调用run_server函数...", flush=True)
        
        run_server()
    except KeyboardInterrupt:
        print("\n服务端已停止", flush=True)
    except Exception as e:
        print(f"服务端启动失败: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
